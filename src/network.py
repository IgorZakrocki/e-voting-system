from __future__ import annotations

import curses
import json
import socket
import socketserver
import threading
import time
from pathlib import Path
from typing import Any

from cli import (
    AppContext,
    candidates_screen,
    infer_mode,
    question_id,
    question_text,
    referendum_screen,
    result_screen,
    setup_curses,
    submit_election,
    submit_referendum,
    voter_input_form,
    verify_voter,
)

DISCOVERY_MAGIC = "SECURE_E_VOTING_DISCOVERY_V1"
BUFFER_SIZE = 65535


def _send_json_line(sock: socket.socket, payload: dict[str, Any]) -> None:
    sock.sendall(json.dumps(payload, ensure_ascii=False).encode("utf-8") + b"\n")


def _read_json_line(stream) -> dict[str, Any]:
    line = stream.readline()
    if not line:
        raise ConnectionError("Połączenie zamknięte przez drugą stronę.")
    return json.loads(line.decode("utf-8"))


class VotingTCPHandler(socketserver.StreamRequestHandler):
    context: AppContext
    questions: list[dict[str, Any]]
    mode: str

    def handle(self) -> None:
        try:
            hello = _read_json_line(self.rfile)
            if hello.get("type") != "verify":
                _send_json_line(self.request, {"type": "error", "message": "Najpierw wymagana jest weryfikacja."})
                return

            verified, voter_id, message = verify_voter(
                self.server.context,  # type: ignore[attr-defined]
                str(hello.get("full_name", "")),
                str(hello.get("pesel_last4", "")),
                str(hello.get("id_number", "")),
            )
            if not verified:
                _send_json_line(self.request, {"type": "verify_result", "verified": False, "message": message})
                return

            questions_payload = [
                {"question_id": question_id(question, i), "text": question_text(question)}
                for i, question in enumerate(self.server.questions)  # type: ignore[attr-defined]
            ]
            _send_json_line(
                self.request,
                {
                    "type": "verify_result",
                    "verified": True,
                    "message": message,
                    "mode": self.server.mode,  # type: ignore[attr-defined]
                    "questions": questions_payload,
                },
            )

            vote_msg = _read_json_line(self.rfile)
            if vote_msg.get("type") != "vote":
                _send_json_line(self.request, {"type": "error", "message": "Oczekiwano pakietu vote."})
                return

            answers = vote_msg.get("answers")
            if self.server.mode == "referendum":  # type: ignore[attr-defined]
                matrix = _referendum_answers_to_matrix(answers, len(self.server.questions))  # type: ignore[attr-defined]
                accepted, errors = submit_referendum(self.server.context, voter_id, self.server.questions, matrix)  # type: ignore[attr-defined]
                payload: Any = matrix
            else:
                selected = _election_answers_to_vector(answers, len(self.server.questions))  # type: ignore[attr-defined]
                accepted, errors = submit_election(self.server.context, voter_id, self.server.questions, selected)  # type: ignore[attr-defined]
                payload = selected

            _send_json_line(
                self.request,
                {"type": "vote_result", "accepted": accepted, "errors": errors, "payload": payload},
            )
        except Exception as exc:  # noqa: BLE001 - odpowiedź protokołu dla klienta
            try:
                _send_json_line(self.request, {"type": "error", "message": str(exc)})
            except Exception:
                pass


def _referendum_answers_to_matrix(answers: Any, expected: int) -> list[list[int]]:
    # Preferowany format klienta curses: 3 x n; wiersze: TAK, NIE, BRAK ZAZNACZENIA.
    if (
        isinstance(answers, list)
        and len(answers) == 3
        and all(isinstance(row, list) and len(row) == expected for row in answers)
    ):
        matrix = [[1 if bool(value) else 0 for value in row] for row in answers]
        for col in range(expected):
            if sum(matrix[row][col] for row in range(3)) != 1:
                raise ValueError("Każde pytanie referendalne musi mieć dokładnie jeden stan: TAK, NIE albo BRAK.")
        return matrix

    # Zgodność wsteczna: lista n odpowiedzi tekstowych/boolowskich.
    if not isinstance(answers, list) or len(answers) != expected:
        raise ValueError("Nieprawidłowa liczba odpowiedzi referendalnych.")
    matrix: list[list[int]] = [[0 for _ in range(expected)], [0 for _ in range(expected)], [0 for _ in range(expected)]]
    for i, value in enumerate(answers):
        normalized = str(value).strip().casefold()
        if normalized in {"tak", "t", "yes", "y", "1", "true"}:
            matrix[0][i] = 1
        elif normalized in {"nie", "n", "no", "0", "false"}:
            matrix[1][i] = 1
        else:
            matrix[2][i] = 1
    return matrix


def _election_answers_to_vector(answers: Any, expected: int) -> list[int]:
    if not isinstance(answers, list) or len(answers) != expected:
        raise ValueError("Nieprawidłowa liczba odpowiedzi wyborczych.")
    return [1 if bool(value) else 0 for value in answers]


def _broadcast_discovery(host: str, port: int, discovery_port: int, stop_event: threading.Event) -> None:
    payload = json.dumps({"magic": DISCOVERY_MAGIC, "host": host, "port": port}, ensure_ascii=False).encode("utf-8")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while not stop_event.is_set():
            sock.sendto(payload, ("255.255.255.255", discovery_port))
            stop_event.wait(1.0)


def run_server(questions_path: str | Path, host: str = "0.0.0.0", port: int = 8765, discovery_port: int = 8766) -> None:
    context = AppContext(questions_path=questions_path)
    questions = context.question_repo.load_all()
    if not questions:
        raise SystemExit(f"Brak pytań w pliku: {questions_path}")
    mode = infer_mode(questions)

    class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True

    server = ThreadedTCPServer((host, port), VotingTCPHandler)
    server.context = context  # type: ignore[attr-defined]
    server.questions = questions  # type: ignore[attr-defined]
    server.mode = mode  # type: ignore[attr-defined]

    stop_event = threading.Event()
    advertised_host = _local_ip_guess() if host in {"0.0.0.0", ""} else host
    discovery_thread = threading.Thread(
        target=_broadcast_discovery,
        args=(advertised_host, port, discovery_port, stop_event),
        daemon=True,
    )
    discovery_thread.start()

    print(f"Serwer działa na {host}:{port}")
    print(f"Tryb wykryty automatycznie: {mode}")
    print(f"Rozgłaszanie UDP broadcast na porcie {discovery_port}; klient nie musi znać IP serwera.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nZamykanie serwera...")
    finally:
        stop_event.set()
        server.shutdown()
        server.server_close()


def discover_server(discovery_port: int = 8766, timeout: float = 5.0) -> tuple[str, int]:
    deadline = time.time() + timeout
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", discovery_port))
        sock.settimeout(0.5)
        while time.time() < deadline:
            try:
                data, address = sock.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                continue
            try:
                payload = json.loads(data.decode("utf-8"))
            except json.JSONDecodeError:
                continue
            if payload.get("magic") == DISCOVERY_MAGIC:
                return str(payload.get("host") or address[0]), int(payload.get("port"))
    raise TimeoutError("Nie znaleziono serwera w sieci lokalnej.")


def run_client(port: int = 8765, discovery_port: int = 8766, timeout: float = 5.0) -> None:
    curses.wrapper(lambda stdscr: run_client_curses(stdscr, port, discovery_port, timeout))


def run_client_curses(stdscr: curses.window, port: int = 8765, discovery_port: int = 8766, timeout: float = 5.0) -> None:
    setup_curses(stdscr)
    stdscr.clear()
    stdscr.addstr(0, 0, "Secure E-Voting", curses.A_BOLD)
    stdscr.addstr(2, 0, "Szukam serwera w sieci lokalnej...")
    stdscr.refresh()
    try:
        host, discovered_port = discover_server(discovery_port=discovery_port, timeout=timeout)
        port = discovered_port or port
    except Exception as exc:
        result_screen(stdscr, "Nie znaleziono serwera", str(exc), 0, [str(exc)])
        return

    full_name, pesel_last4, id_number = voter_input_form(stdscr, f"Dane wyborcy — serwer {host}:{port}")
    if len("".join(ch for ch in pesel_last4 if ch.isdigit())) != 4:
        result_screen(stdscr, "Weryfikacja odrzucona", "PESEL musi zawierać dokładnie 4 cyfry.", 0, ["PESEL musi zawierać dokładnie 4 cyfry."])
        return

    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            stream = sock.makefile("rb")
            _send_json_line(
                sock,
                {
                    "type": "verify",
                    "full_name": full_name,
                    "pesel_last4": pesel_last4,
                    "id_number": id_number,
                },
            )
            response = _read_json_line(stream)
            if not response.get("verified"):
                message = str(response.get("message", "Weryfikacja odrzucona."))
                result_screen(stdscr, "Weryfikacja odrzucona", message, 0, [message])
                return

            mode = response["mode"]
            questions = response["questions"]
            if mode == "referendum":
                matrix = referendum_screen(stdscr, questions)
                if matrix is None:
                    result_screen(stdscr, "Referendum anulowane", None, 0, [])
                    return
                payload: Any = matrix
            else:
                selected = candidates_screen(stdscr, questions, "WYBORY")
                if selected is None:
                    result_screen(stdscr, "Wybory anulowane", None, 0, [])
                    return
                payload = selected

            _send_json_line(sock, {"type": "vote", "answers": payload})
            result = _read_json_line(stream)
            if result.get("type") == "error":
                message = str(result.get("message", "Błąd serwera."))
                result_screen(stdscr, "Błąd", message, 0, [message])
                return
            title = "Referendum zapisane" if mode == "referendum" else "Wybory zapisane"
            result_screen(stdscr, title, result.get("payload", payload), int(result.get("accepted", 0)), list(result.get("errors", [])))
    except Exception as exc:
        result_screen(stdscr, "Błąd połączenia", str(exc), 0, [str(exc)])


def _local_ip_guess() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
        except OSError:
            return socket.gethostbyname(socket.gethostname())
