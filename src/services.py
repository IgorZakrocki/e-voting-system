from datetime import UTC, datetime
from uuid import uuid4

from exceptions import (
    InvalidQuestionError,
    InvalidVoteValueError,
    UnauthorizedVoterError,
    VoterAlreadyVotedError,
)


class AuditService:
    def __init__(self, audit_repo):
        self.audit_repo = audit_repo

    def log(self, event: str, voter_id: str | None = None, status: str = "info", reason: str | None = None) -> None:
        logs = self.audit_repo.load_all()
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event": event,
            "status": status,
        }
        if voter_id is not None:
            entry["voter_id"] = voter_id
        if reason is not None:
            entry["reason"] = reason
        logs.append(entry)
        self.audit_repo.save_all(logs)


class VotingService:
    """Business logic for accepting or rejecting encrypted votes."""

    def __init__(self, voter_repo, question_repo, vote_repo, audit_repo, crypto_service):
        self.voter_repo = voter_repo
        self.question_repo = question_repo
        self.vote_repo = vote_repo
        self.audit_service = AuditService(audit_repo)
        self.crypto_service = crypto_service

    def cast_vote(self, voter_id: str, question_id: str, answer: bool) -> dict:
        voters = self.voter_repo.load_all()
        questions = self.question_repo.load_all()

        voter = next((v for v in voters if str(v.get("voter_id")) == str(voter_id)), None)
        question = next((q for q in questions if q["question_id"] == question_id), None)

        if voter is None:
            self.audit_service.log("vote_rejected", voter_id, "rejected", "unauthorized_voter")
            raise UnauthorizedVoterError("Voter is not authorized.")

        if bool(voter.get("voted", False)):
            self.audit_service.log("vote_rejected", voter_id, "rejected", "voter_already_voted")
            raise VoterAlreadyVotedError("Voter has already taken part in this voting.")

        if question is None:
            self.audit_service.log("vote_rejected", voter_id, "rejected", "invalid_question")
            raise InvalidQuestionError("Question does not exist.")

        if not isinstance(answer, bool):
            self.audit_service.log("vote_rejected", voter_id, "rejected", "invalid_vote_value")
            raise InvalidVoteValueError("Answer must be a boolean value.")

        encrypted_vote = self.crypto_service.encrypt_vote(1 if answer else 0)
        serialized_vote = self.crypto_service.serialize_encrypted_number(encrypted_vote)

        vote = {
            "vote_id": str(uuid4()),
            "voter_id": voter_id,
            "question_id": question_id,
            **serialized_vote,
        }

        votes = self.vote_repo.load_all()
        votes.append(vote)
        self.vote_repo.save_all(votes)

        self.audit_service.log("vote_cast", voter_id, "accepted")
        return vote

    def mark_voter_voted(self, voter_id: str) -> None:
        voters = self.voter_repo.load_all()
        voter = next((v for v in voters if str(v.get("voter_id")) == str(voter_id)), None)
        if voter is None:
            self.audit_service.log("voter_state_update_rejected", voter_id, "rejected", "unauthorized_voter")
            raise UnauthorizedVoterError("Voter is not authorized.")
        voter["voted"] = True
        voter.pop("voted_questions", None)
        self.voter_repo.save_all(voters)
        self.audit_service.log("voter_marked_as_voted", voter_id, "accepted")


class TallyService:
    """Counts encrypted votes and decrypts only aggregated results."""

    def __init__(self, question_repo, vote_repo, result_repo, audit_repo, crypto_service):
        self.question_repo = question_repo
        self.vote_repo = vote_repo
        self.result_repo = result_repo
        self.audit_service = AuditService(audit_repo)
        self.crypto_service = crypto_service

    def tally_question(self, question_id: str) -> dict:
        questions = self.question_repo.load_all()
        question = next((q for q in questions if q["question_id"] == question_id), None)
        if question is None:
            raise InvalidQuestionError("Question does not exist.")

        votes = [vote for vote in self.vote_repo.load_all() if vote["question_id"] == question_id]
        encrypted_votes = [self.crypto_service.deserialize_encrypted_number(vote) for vote in votes]
        encrypted_sum = self.crypto_service.add_encrypted_votes(encrypted_votes)

        yes_count = self.crypto_service.decrypt_result(encrypted_sum)
        total_valid_votes = len(votes)
        no_count = total_valid_votes - yes_count

        return {
            "question_id": question_id,
            "question_text": question["text"],
            "yes": yes_count,
            "no": no_count,
            "total_valid_votes": total_valid_votes,
        }

    def tally_all_questions(self) -> list[dict]:
        questions = self.question_repo.load_all()
        results = [self.tally_question(question["question_id"]) for question in questions]
        self.result_repo.save_all(results)
        self.audit_service.log("tally_completed", status="completed")
        return results
