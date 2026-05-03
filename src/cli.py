from __future__ import annotations

import argparse
import curses
import unicodedata
from pathlib import Path
from typing import Any, Literal

from crypto import KeyManager, PaillierService
from repositories import JsonRepository
from services import TallyService, VotingService


ElectionMode = Literal["referendum", "election"]


class AppContext:
    def __init__(self, base_dir: str | Path = ".", questions_path: str | Path | None = None):
        self.base_dir = Path(base_dir)
        self.voter_repo = JsonRepository(self.base_dir / "data/voters.json")
        self.question_repo = JsonRepository(Path(questions_path) if questions_path else self.base_dir / "data/questions.json")
        self.vote_repo = JsonRepository(self.base_dir / "data/votes.json")
        self.result_repo = JsonRepository(self.base_dir / "data/results.json")
        self.audit_repo = JsonRepository(self.base_dir / "data/audit_log.json")

        self._normalize_storage_records()

        key_manager = KeyManager(self.base_dir / "keys/public_key.json", self.base_dir / "keys/private_key.json")
        public_key = key_manager.load_public_key()
        private_key = key_manager.load_private_key()
        self.crypto_service = PaillierService(public_key, private_key)

        self.voting_service = VotingService(
            self.voter_repo,
            self.question_repo,
            self.vote_repo,
            self.audit_repo,
            self.crypto_service,
        )
        self.tally_service = TallyService(
            self.question_repo,
            self.vote_repo,
            self.result_repo,
            self.audit_repo,
            self.crypto_service,
        )

    def _normalize_storage_records(self) -> None:
        voters = self.voter_repo.load_all()
        voters_changed = False
        for index, voter in enumerate(voters):
            if "voter_id" not in voter:
                voter["voter_id"] = str(get_any(voter, ("id", "uuid", "pesel", "document_number", "id_number", "id_card_number")) or index + 1)
                voters_changed = True
            if "voted" not in voter:
                voter["voted"] = False
                voters_changed = True
            if "voted_questions" in voter:
                voter.pop("voted_questions", None)
                voters_changed = True
        if voters_changed:
            self.voter_repo.save_all(voters)

        questions = self.question_repo.load_all()
        questions_changed = False
        for index, question in enumerate(questions):
            if "question_id" not in question:
                question["question_id"] = str(get_any(question, ("id", "candidate_id")) or index + 1)
                questions_changed = True
            if "text" not in question:
                question["text"] = str(get_any(question, ("question", "name", "candidate", "candidate_name")) or "")
                questions_changed = True
        if questions_changed:
            self.question_repo.save_all(questions)


class Colors:
    TITLE = 1
    INPUT = 2
    OK = 3
    ERROR = 4
    HINT = 5
    ACTIVE = 6
    CHECKED = 7


def setup_curses(stdscr: curses.window) -> None:
    curses.curs_set(0)
    stdscr.keypad(True)
    curses.noecho()
    curses.cbreak()
    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(Colors.TITLE, curses.COLOR_CYAN, -1)
        curses.init_pair(Colors.INPUT, curses.COLOR_BLUE, -1)
        curses.init_pair(Colors.OK, curses.COLOR_GREEN, -1)
        curses.init_pair(Colors.ERROR, curses.COLOR_RED, -1)
        curses.init_pair(Colors.HINT, curses.COLOR_YELLOW, -1)
        curses.init_pair(Colors.ACTIVE, curses.COLOR_BLACK, curses.COLOR_CYAN)
        curses.init_pair(Colors.CHECKED, curses.COLOR_GREEN, -1)


def attr(color: int, *flags: int) -> int:
    value = curses.color_pair(color) if curses.has_colors() else curses.A_NORMAL
    for flag in flags:
        value |= flag
    return value


def safe_addstr(stdscr: curses.window, y: int, x: int, text: str, style: int = curses.A_NORMAL) -> None:
    height, width = stdscr.getmaxyx()
    if y < 0 or y >= height or x >= width:
        return
    text = text[: max(0, width - x - 1)]
    try:
        stdscr.addstr(y, x, text, style)
    except curses.error:
        pass

def mask_id_number(value: str) -> str:
    return "*" * len(value.strip()) if value.strip() else ""


def read_text(
    stdscr: curses.window,
    y: int,
    x: int,
    prompt: str,
    hidden: bool = False,
    max_length: int | None = None,
    digits_only: bool = False,
) -> str:
    curses.curs_set(1)
    curses.echo(False)
    value: list[str] = []
    while True:
        safe_addstr(stdscr, y, x, prompt, curses.A_BOLD)
        visible = "*" * len(value) if hidden else "".join(value)
        safe_addstr(stdscr, y, x + len(prompt), " " * 80)
        safe_addstr(stdscr, y, x + len(prompt), visible, attr(Colors.INPUT, curses.A_BOLD))
        stdscr.move(y, min(x + len(prompt) + len(visible), curses.COLS - 2))
        stdscr.refresh()
        key = stdscr.get_wch()
        if key in ("\n", "\r") or key == curses.KEY_ENTER:
            break
        if key == "\x1b":
            return ""
        if key in (curses.KEY_BACKSPACE, 127, 8, "\b", "\x7f"):
            if value:
                value.pop()
            continue
        if isinstance(key, str) and key.isprintable():
            char = key
            if digits_only and not char.isdigit():
                continue
            if max_length is not None and len(value) >= max_length:
                continue
            value.append(char)
    curses.curs_set(0)
    return "".join(value).strip()


def normalize_digits(value: Any) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def strip_polish_diacritics(value: str) -> str:
    """Return lowercase text without diacritics, e.g. Wójcik == Wojcik."""
    decomposed = unicodedata.normalize("NFKD", value)
    without_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return without_marks.replace("ł", "l").replace("Ł", "L")


def normalize_text(value: Any) -> str:
    text = str(value or "").casefold()
    text = strip_polish_diacritics(text)
    return " ".join(text.split())


def get_any(record: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in record:
            return record[key]
    return None


def voter_identifier(voter: dict[str, Any], fallback: str) -> str:
    return str(get_any(voter, ("voter_id", "id", "uuid", "pesel", "document_number", "id_number", "id_card_number")) or fallback)


def verify_voter(context: AppContext, full_name: str, pesel_last4: str, id_number: str) -> tuple[bool, str, str]:
    voters = context.voter_repo.load_all()
    wanted_name = normalize_text(full_name)
    wanted_pesel = normalize_digits(pesel_last4)[-4:]
    wanted_doc = normalize_text(id_number)
    for index, voter in enumerate(voters):
        name = get_any(voter, ("name", "full_name", "fullName", "imie_nazwisko"))
        first_name = get_any(voter, ("first_name", "firstName", "imie"))
        last_name = get_any(voter, ("last_name", "lastName", "nazwisko"))
        record_name = normalize_text(name) or normalize_text(f"{first_name or ''} {last_name or ''}")
        pesel = normalize_digits(get_any(voter, ("pesel", "PESEL")))[-4:]
        doc = normalize_text(get_any(voter, ("document_number", "id_number", "id_card", "id_card_number", "nr_dowodu", "document")))
        if (not record_name or record_name == wanted_name) and (not pesel or pesel == wanted_pesel) and (not doc or doc == wanted_doc):
            if bool(voter.get("voted", False)):
                return False, "", "Wyborca już wziął udział w głosowaniu"
            return True, voter_identifier(voter, str(index + 1)), "Wyborca zweryfikowany"
    return False, "", "Nie udało się zweryfikować wyborcy"


def voter_input_form(stdscr: curses.window, subtitle: str = "Weryfikacja wyborcy:") -> tuple[str, str, str]:
    stdscr.clear()
    #safe_addstr(stdscr, 0, 0, "Secure E-Voting System", attr(Colors.TITLE, curses.A_BOLD))
    safe_addstr(stdscr, 1, 0, subtitle, curses.A_BOLD)
    full_name = read_text(stdscr, 2, 0, "Imię i Nazwisko: ")
    safe_addstr(stdscr, 3, 0, "PESEL (dokładnie 4 ostatnie cyfry): ", curses.A_BOLD)
    safe_addstr(stdscr, 3, 39, "max 4 cyfry", attr(Colors.HINT))
    pesel_last4 = read_text(stdscr, 3, 0, "PESEL (dokładnie 4 ostatnie cyfry): ", max_length=4, digits_only=True)
    id_number = read_text(stdscr, 4, 0, "Nr dowodu osobistego: ", hidden=True)
    return full_name, pesel_last4, id_number


def voter_form(stdscr: curses.window, context: AppContext) -> tuple[bool, str]:
    full_name, pesel_last4, id_number = voter_input_form(stdscr)
    if len(normalize_digits(pesel_last4)) != 4:
        verified, voter_id, message = False, "", "PESEL musi zawierać dokładnie 4 cyfry."
    else:
        verified, voter_id, message = verify_voter(context, full_name, pesel_last4, id_number)
    safe_addstr(stdscr, 2, 0, "Imię i Nazwisko: ", curses.A_BOLD)
    safe_addstr(stdscr, 2, 17, full_name, attr(Colors.INPUT, curses.A_BOLD))
    safe_addstr(stdscr, 3, 0, "PESEL (dokładnie 4 ostatnie cyfry): ", curses.A_BOLD)
    safe_addstr(stdscr, 3, 39, pesel_last4, attr(Colors.INPUT, curses.A_BOLD))
    safe_addstr(stdscr, 4, 0, "Nr dowodu osobistego: ", curses.A_BOLD)
    safe_addstr(stdscr, 4, 23, mask_id_number(id_number), attr(Colors.INPUT, curses.A_BOLD))
    safe_addstr(stdscr, 6, 0, message, attr(Colors.OK if verified else Colors.ERROR, curses.A_BOLD))
    safe_addstr(stdscr, 8, 0, "Naciśnij dowolny klawisz aby przejść dalej ...", attr(Colors.HINT))
    stdscr.refresh()
    stdscr.getch()
    return verified, voter_id 


def load_questions(context: AppContext) -> list[dict[str, Any]]:
    questions = context.question_repo.load_all()
    return questions if isinstance(questions, list) else []


def question_id(question: dict[str, Any], index: int) -> str:
    return str(get_any(question, ("question_id", "id", "candidate_id")) or index + 1)


def question_text(question: dict[str, Any]) -> str:
    return str(get_any(question, ("text", "question", "name", "candidate", "candidate_name")) or "")


def infer_mode(questions: list[dict[str, Any]]) -> ElectionMode:
    explicit = {normalize_text(get_any(q, ("type", "mode", "kind"))) for q in questions}
    if {"referendum", "referendalne"} & explicit:
        return "referendum"
    if {"election", "wybory", "presidential", "chairman", "kandydat"} & explicit:
        return "election"
    if any(normalize_text(question_text(q)).startswith("czy ") for q in questions):
        return "referendum"
    if any(get_any(q, ("candidate", "candidate_name")) for q in questions):
        return "election"
    return "election"


def draw_voter_summary(stdscr: curses.window) -> int:
    safe_addstr(stdscr, 0, 0, "Wyborca zweryfikowany", attr(Colors.OK, curses.A_BOLD))
    return 2


def draw_referendum(stdscr: curses.window, questions: list[dict[str, Any]], answers: list[list[int]], row: int, col: int) -> None:
    stdscr.clear()
    start_y = draw_voter_summary(stdscr)
    safe_addstr(stdscr, start_y, 0,"PYTANIA REFERENDALNE:", curses.A_BOLD)
    safe_addstr(stdscr, start_y + 2, 0, "Strzałki: ruch | Enter/Spacja: zaznacz | S: submit | Q: cancel", attr(Colors.HINT))
    for i, question in enumerate(questions):
        y = start_y + 4 + i
        safe_addstr(stdscr, y, 0, f"{i + 1}. {question_text(question)[:68]:68}")
        for j, label in enumerate(("Tak", "Nie")):
            x = 74 + j * 13
            checked = answers[j][i] == 1
            box = "[X]" if checked else "[ ]"
            style = attr(Colors.ACTIVE, curses.A_BOLD) if i == row and j == col else curses.A_NORMAL
            if checked and not (i == row and j == col):
                style = attr(Colors.CHECKED, curses.A_BOLD)
            safe_addstr(stdscr, y, x, f"{label} {box}", style)
    stdscr.refresh()


def referendum_screen(stdscr: curses.window, questions: list[dict[str, Any]]) -> list[list[int]] | None:
    # Format zwracany: 3 x n, gdzie kolejne wiersze oznaczają: TAK, NIE, BRAK ZAZNACZENIA.
    answers = [[0 for _ in questions], [0 for _ in questions], [1 for _ in questions]]
    row = 0
    col = 0
    while True:
        draw_referendum(stdscr, questions, answers, row, col)
        key = stdscr.getch()
        if key == curses.KEY_UP:
            row = max(0, row - 1)
        elif key == curses.KEY_DOWN:
            row = min(len(questions) - 1, row + 1)
        elif key == curses.KEY_LEFT:
            col = max(0, col - 1)
        elif key == curses.KEY_RIGHT:
            col = min(1, col + 1)
        elif key in (10, 13, curses.KEY_ENTER, ord(" ")):
            target = col  # 0 = TAK, 1 = NIE
            if answers[target][row] == 1:
                answers[target][row] = 0
                answers[2][row] = 1
            else:
                answers[0][row] = 0
                answers[1][row] = 0
                answers[2][row] = 0
                answers[target][row] = 1
        elif key in (ord("s"), ord("S")):
            return answers
        elif key in (ord("q"), ord("Q"), 27):
            return None


def draw_candidates(stdscr: curses.window, candidates: list[dict[str, Any]], selected: list[int], cursor: int, title: str) -> None:
    stdscr.clear()
    start_y = draw_voter_summary(stdscr)
    safe_addstr(stdscr, start_y, 0,"WYBORY PRZEWODNICZĄCEGO:", curses.A_BOLD)
    safe_addstr(stdscr, start_y + 2, 0, "Strzałki: ruch | Enter/Spacja: zaznacz | S: submit | Q: cancel", attr(Colors.HINT))
    for i, candidate in enumerate(candidates):
        checked = selected[i] == 1
        style = attr(Colors.ACTIVE, curses.A_BOLD) if i == cursor else attr(Colors.CHECKED, curses.A_BOLD) if checked else curses.A_NORMAL
        safe_addstr(stdscr, start_y + 4 + i, 0, f"{i + 1}. {question_text(candidate):55} {'[X]' if checked else '[ ]'}", style)
    stdscr.refresh()


def candidates_screen(stdscr: curses.window, candidates: list[dict[str, Any]], title: str) -> list[int] | None:
    selected = [0] * len(candidates)
    cursor = 0
    while True:
        draw_candidates(stdscr, candidates, selected, cursor, title)
        key = stdscr.getch()
        if key == curses.KEY_UP:
            cursor = max(0, cursor - 1)
        elif key == curses.KEY_DOWN:
            cursor = min(len(candidates) - 1, cursor + 1)
        elif key in (10, 13, curses.KEY_ENTER, ord(" ")):
            if selected[cursor] == 1:
                selected[cursor] = 0
            else:
                selected = [0] * len(candidates)
                selected[cursor] = 1
        elif key in (ord("s"), ord("S")):
            return selected
        elif key in (ord("q"), ord("Q"), 27):
            return None


def submit_referendum(context: AppContext, voter_id: str, questions: list[dict[str, Any]], matrix: list[list[int]]) -> tuple[int, list[str]]:
    errors: list[str] = []
    accepted = 0
    if len(matrix) != 3 or any(len(row) != len(questions) for row in matrix):
        return 0, ["Nieprawidłowy format referendum: oczekiwano macierzy 3 x n."]
    for i in range(len(questions)):
        yes = matrix[0][i] == 1
        no = matrix[1][i] == 1
        blank = matrix[2][i] == 1
        if blank or yes == no:
            continue
        try:
            context.voting_service.cast_vote(voter_id, question_id(questions[i], i), yes)
            accepted += 1
        except Exception as exc:
            errors.append(f"{question_id(questions[i], i)}: {exc}")
    if not errors:
        context.voting_service.mark_voter_voted(voter_id)
    return accepted, errors


def submit_election(context: AppContext, voter_id: str, candidates: list[dict[str, Any]], selected: list[int]) -> tuple[int, list[str]]:
    errors: list[str] = []
    accepted = 0
    if sum(1 for value in selected if value == 1) != 1:
        return 0, ["W wyborach należy zaznaczyć dokładnie jednego kandydata."]
    for i, value in enumerate(selected):
        if value != 1:
            continue
        try:
            context.voting_service.cast_vote(voter_id, question_id(candidates[i], i), True)
            accepted += 1
        except Exception as exc:
            errors.append(f"{question_id(candidates[i], i)}: {exc}")
    if not errors:
        context.voting_service.mark_voter_voted(voter_id)
    return accepted, errors


def result_screen(stdscr: curses.window, title: str, payload: Any, accepted: int, errors: list[str]) -> None:
    stdscr.clear()
    safe_addstr(stdscr, 0, 0, "WYNIK OPERACJI", curses.A_BOLD)
    safe_addstr(stdscr, 2, 0, f"{title}", attr(Colors.OK if not errors else Colors.HINT, curses.A_BOLD))
    if errors:
        safe_addstr(stdscr, 4, 0, "Błędy:", attr(Colors.ERROR, curses.A_BOLD))
        for i, error in enumerate(errors[:8]):
            safe_addstr(stdscr, 5 + i, 0, f"- {error}", attr(Colors.ERROR))
    safe_addstr(stdscr, curses.LINES - 2, 0, "Naciśnij dowolny klawisz, aby zakończyć.", attr(Colors.HINT))
    stdscr.refresh()
    stdscr.getch()


def run_curses(stdscr: curses.window, questions_path: str | Path | None = None) -> None:
    setup_curses(stdscr)
    context = AppContext(questions_path=questions_path)

    verified, voter_id = voter_form(stdscr, context)
    if not verified:
        return

    questions = load_questions(context)
    if not questions:
        result_screen(stdscr, f"Brak pytań/kandydatów w {context.question_repo.file_path}", None, 0, [])
        return

    mode = infer_mode(questions)

    if mode == "referendum":
        matrix = referendum_screen(stdscr, questions)
        if matrix is None:
            result_screen(stdscr, "Referendum anulowane", None, 0, [])
            return

        accepted, errors = submit_referendum(context, voter_id, questions, matrix)

        if accepted > 0 and not errors:
            context.tally_service.tally_all_questions()

        result_screen(stdscr, "Referendum zapisane", matrix, accepted, errors)
        return

    selected = candidates_screen(stdscr, questions, "WYBORY")
    if selected is None:
        result_screen(stdscr, "Wybory anulowane", None, 0, [])
        return

    accepted, errors = submit_election(context, voter_id, questions, selected)

    if accepted > 0 and not errors:
        context.tally_service.tally_all_questions()

    result_screen(stdscr, "Wybory zapisane", selected, accepted, errors)


def run_menu(questions_path: str | Path | None = None) -> None:
    curses.wrapper(lambda stdscr: run_curses(stdscr, questions_path))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Secure E-Voting")
    subparsers = parser.add_subparsers(dest="command")

    local = subparsers.add_parser("local", help="Uruchom lokalne głosowanie TUI")
    local.add_argument("questions", nargs="?", help="Ścieżka do pliku JSON z pytaniami/kandydatami")

    server = subparsers.add_parser("server", help="Uruchom serwer głosowania")
    server.add_argument("questions", help="Ścieżka do pliku JSON z pytaniami/kandydatami")
    server.add_argument("--host", default="0.0.0.0")
    server.add_argument("--port", type=int, default=8765)
    server.add_argument("--discovery-port", type=int, default=8766)

    client = subparsers.add_parser("client", help="Uruchom klienta; adres serwera zostanie wykryty automatycznie")
    client.add_argument("--port", type=int, default=8765)
    client.add_argument("--discovery-port", type=int, default=8766)
    client.add_argument("--timeout", type=float, default=5.0)

    return parser


def main(argv: list[str] | None = None) -> None:
    import sys

    raw = sys.argv[1:] if argv is None else argv
    # Zgodność wsteczna: `python -m main data/questions.json`.
    if len(raw) == 1 and raw[0] not in {"local", "server", "client", "-h", "--help"} and Path(raw[0]).exists():
        run_menu(raw[0])
        return

    parser = build_parser()
    args = parser.parse_args(raw)

    if args.command == "server":
        from network import run_server
        run_server(args.questions, host=args.host, port=args.port, discovery_port=args.discovery_port)
        return
    if args.command == "client":
        from network import run_client
        run_client(port=args.port, discovery_port=args.discovery_port, timeout=args.timeout)
        return
    if args.command == "local":
        run_menu(args.questions)
        return

    run_menu()


if __name__ == "__main__":
    main()
