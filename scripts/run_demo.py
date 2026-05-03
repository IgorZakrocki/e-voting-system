from crypto import KeyManager, PaillierService
from exceptions import UnauthorizedVoterError, VoterAlreadyVotedError
from repositories import JsonRepository
from services import TallyService, VotingService


def build_services():
    key_manager = KeyManager()
    public_key = key_manager.load_public_key()
    private_key = key_manager.load_private_key()
    crypto_service = PaillierService(public_key, private_key)

    voter_repo = JsonRepository("data/voters.json")
    question_repo = JsonRepository("data/questions_referendum.json") #data/chairperson_questions.json lub data/referendum_questions.json
    vote_repo = JsonRepository("data/votes.json")
    result_repo = JsonRepository("data/results.json")
    audit_repo = JsonRepository("data/audit_log.json")

    voting_service = VotingService(voter_repo, question_repo, vote_repo, audit_repo, crypto_service)
    tally_service = TallyService(question_repo, vote_repo, result_repo, audit_repo, crypto_service)
    return voting_service, tally_service


def main() -> None:
    print("Run `uv run python scripts/seed_data.py` first if keys or data are missing.")
    voting_service, tally_service = build_services()

    planned_votes = [
        ("001", "q01", True),
        ("002", "q01", False),
        ("003", "q01", True),
        ("001", "q02", False),
        ("002", "q02", True),
    ]

    for voter_id, question_id, answer in planned_votes:
        voting_service.cast_vote(voter_id, question_id, answer)
        print(f"Accepted encrypted vote: {voter_id} -> {question_id} = {answer}")

    try:
        voting_service.cast_vote("unknown_voter", "q01", True)
    except UnauthorizedVoterError:
        print("Rejected unauthorized voter as expected.")

    try:
        voting_service.cast_vote("001", "q01", False)
    except VoterAlreadyVotedError:
        print("Rejected duplicate vote as expected.")

    results = tally_service.tally_all_questions()
    print("\nFinal results:")
    for result in results:
        print(result)


if __name__ == "__main__":
    main()
