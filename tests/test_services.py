import pytest

from exceptions import InvalidQuestionError, InvalidVoteValueError, UnauthorizedVoterError, VoterAlreadyVotedError


def test_authorized_voter_can_cast_vote(voting_service, repos):
    vote = voting_service.cast_vote("voter_001", "q1", True)
    _voter_repo, _question_repo, vote_repo, _result_repo, audit_repo = repos

    assert vote["voter_id"] == "voter_001"
    assert vote["question_id"] == "q1"
    assert len(vote_repo.load_all()) == 1
    assert audit_repo.load_all()[-1]["status"] == "accepted"


def test_unknown_voter_is_rejected(voting_service, repos):
    with pytest.raises(UnauthorizedVoterError):
        voting_service.cast_vote("unknown", "q1", True)

    _voter_repo, _question_repo, vote_repo, _result_repo, audit_repo = repos
    assert vote_repo.load_all() == []
    assert audit_repo.load_all()[-1]["reason"] == "unauthorized_voter"


def test_voter_cannot_vote_twice_on_same_question(voting_service, repos):
    voting_service.cast_vote("voter_001", "q1", True)

    with pytest.raises(VoterAlreadyVotedError):
        voting_service.cast_vote("voter_001", "q1", False)

    _voter_repo, _question_repo, vote_repo, _result_repo, audit_repo = repos
    assert len(vote_repo.load_all()) == 1
    assert audit_repo.load_all()[-1]["reason"] == "voter_already_voted_on_question"


def test_voter_can_vote_on_different_questions_before_final_mark(voting_service, repos):
    voting_service.cast_vote("voter_001", "q1", True)
    voting_service.cast_vote("voter_001", "q2", False)

    _voter_repo, _question_repo, vote_repo, _result_repo, _audit_repo = repos
    assert len(vote_repo.load_all()) == 2


def test_marked_voter_cannot_vote_again(voting_service):
    voting_service.mark_voter_voted("voter_001")

    with pytest.raises(VoterAlreadyVotedError):
        voting_service.cast_vote("voter_001", "q1", True)


def test_invalid_question_is_rejected(voting_service):
    with pytest.raises(InvalidQuestionError):
        voting_service.cast_vote("voter_001", "missing_question", True)


def test_invalid_vote_value_is_rejected(voting_service):
    with pytest.raises(InvalidVoteValueError):
        voting_service.cast_vote("voter_001", "q1", "tak")


def test_tally_single_question_counts_yes_and_no(voting_service, tally_service):
    voting_service.cast_vote("voter_001", "q1", True)
    voting_service.cast_vote("voter_002", "q1", False)

    result = tally_service.tally_question("q1")

    assert result["yes"] == 1
    assert result["no"] == 1
    assert result["total_valid_votes"] == 2


def test_tally_all_questions_saves_results(voting_service, tally_service, repos):
    voting_service.cast_vote("voter_001", "q1", True)
    voting_service.cast_vote("voter_001", "q2", False)
    voting_service.cast_vote("voter_002", "q2", True)

    results = {result["question_id"]: result for result in tally_service.tally_all_questions()}

    _voter_repo, _question_repo, _vote_repo, result_repo, audit_repo = repos
    assert results["q1"]["yes"] == 1
    assert results["q1"]["no"] == 0
    assert results["q2"]["yes"] == 1
    assert results["q2"]["no"] == 1
    assert len(result_repo.load_all()) == 2
    assert audit_repo.load_all()[-1]["event"] == "tally_completed"
