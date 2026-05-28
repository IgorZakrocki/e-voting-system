import io
import socket

import pytest

from network import _election_answers_to_vector, _read_json_line, _referendum_answers_to_matrix, _send_json_line


def test_referendum_matrix_is_accepted_when_each_question_has_one_answer():
    answers = [[1, 0], [0, 1], [0, 0]]

    assert _referendum_answers_to_matrix(answers, expected=2) == answers


def test_referendum_text_answers_are_converted_to_matrix():
    matrix = _referendum_answers_to_matrix(["tak", "nie", "brak"], expected=3)

    assert matrix == [[1, 0, 0], [0, 1, 0], [0, 0, 1]]


def test_referendum_rejects_question_with_two_answers():
    with pytest.raises(ValueError):
        _referendum_answers_to_matrix([[1], [1], [0]], expected=1)


def test_election_answers_are_converted_to_zero_one_vector():
    assert _election_answers_to_vector([True, False, 1], expected=3) == [1, 0, 1]


def test_election_rejects_wrong_number_of_answers():
    with pytest.raises(ValueError):
        _election_answers_to_vector([True], expected=2)


def test_json_line_helpers_send_and_read_payload():
    left, right = socket.socketpair()
    try:
        _send_json_line(left, {"type": "ping", "value": "zażółć"})
        stream = right.makefile("rb")

        assert _read_json_line(stream) == {"type": "ping", "value": "zażółć"}
    finally:
        left.close()
        right.close()


def test_json_line_reader_rejects_closed_connection():
    with pytest.raises(ConnectionError):
        _read_json_line(io.BytesIO(b""))
