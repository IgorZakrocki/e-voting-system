from cli import (
    infer_mode,
    mask_id_number,
    normalize_digits,
    normalize_text,
    question_id,
    question_text,
    submit_election,
    submit_referendum,
    verify_voter,
)


def test_normalize_digits_removes_non_digits():
    assert normalize_digits("PESEL: 123-45") == "12345"


def test_normalize_text_ignores_case_spaces_and_polish_characters():
    assert normalize_text("  Łukasz   Żółć ") == "lukasz zołc".replace("ł", "l")


def test_mask_id_number_hides_document_number():
    assert mask_id_number("ABC123") == "******"


def test_question_helpers_use_fallback_fields():
    question = {"candidate_id": 7, "candidate_name": "Anna Nowak"}

    assert question_id(question, 0) == "7"
    assert question_text(question) == "Anna Nowak"


def test_infer_mode_detects_referendum_from_question_text():
    questions = [{"question_id": "q1", "text": "Czy jesteś za zmianą regulaminu?"}]

    assert infer_mode(questions) == "referendum"


def test_infer_mode_detects_election_from_candidate_field():
    questions = [{"candidate_id": "c1", "candidate_name": "Jan Kowalski"}]

    assert infer_mode(questions) == "election"


def test_verify_voter_accepts_correct_data(app_context):
    verified, voter_id, message = verify_voter(app_context, "jan kowalski", "2345", "abc123456")

    assert verified is True
    assert voter_id == "voter_001"
    assert message == "Wyborca zweryfikowany"


def test_verify_voter_rejects_wrong_document(app_context):
    verified, voter_id, message = verify_voter(app_context, "Jan Kowalski", "2345", "bad")

    assert verified is False
    assert voter_id == ""
    assert message == "Nie udało się zweryfikować wyborcy"


def test_submit_referendum_saves_only_marked_answers(app_context):
    questions = app_context.question_repo.load_all()
    matrix = [
        [1, 0],
        [0, 0],
        [0, 1],
    ]

    accepted, errors = submit_referendum(app_context, "voter_001", questions, matrix)

    assert accepted == 1
    assert errors == []
    assert len(app_context.vote_repo.load_all()) == 1
    assert app_context.voter_repo.load_all()[0]["voted"] is True


def test_submit_election_requires_exactly_one_candidate(app_context):
    questions = app_context.question_repo.load_all()

    accepted, errors = submit_election(app_context, "voter_001", questions, [1, 1])

    assert accepted == 0
    assert errors == ["W wyborach należy zaznaczyć dokładnie jednego kandydata."]
