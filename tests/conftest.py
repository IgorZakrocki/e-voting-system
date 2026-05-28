from types import SimpleNamespace

import pytest

from phe import paillier

from crypto import PaillierService
from repositories import JsonRepository
from services import TallyService, VotingService


@pytest.fixture
def crypto_service():
    # Generujemy mały klucz bezpośrednio przez bibliotekę phe.
    # Dzięki temu testy są szybkie i nie zależą od tego, czy PaillierService.generate_keypair()
    # przyjmuje parametr n_length.
    public_key, private_key = paillier.generate_paillier_keypair(n_length=128)
    return PaillierService(public_key, private_key)


@pytest.fixture
def repos(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    voter_repo = JsonRepository(data_dir / "voters.json")
    question_repo = JsonRepository(data_dir / "questions.json")
    vote_repo = JsonRepository(data_dir / "votes.json")
    result_repo = JsonRepository(data_dir / "results.json")
    audit_repo = JsonRepository(data_dir / "audit_log.json")

    voter_repo.save_all(
        [
            {
                "voter_id": "voter_001",
                "name": "Jan Kowalski",
                "pesel": "90010112345",
                "document_number": "ABC123456",
                "voted": False,
            },
            {
                "voter_id": "voter_002",
                "name": "Anna Nowak",
                "pesel": "88020298765",
                "document_number": "XYZ987654",
                "voted": False,
            },
        ]
    )
    question_repo.save_all(
        [
            {"question_id": "q1", "text": "Czy przyjmujesz regulamin?", "type": "referendum"},
            {"question_id": "q2", "text": "Czy wybierasz kandydata A?", "type": "referendum"},
        ]
    )
    vote_repo.clear()
    result_repo.clear()
    audit_repo.clear()

    return voter_repo, question_repo, vote_repo, result_repo, audit_repo


@pytest.fixture
def voting_service(repos, crypto_service):
    voter_repo, question_repo, vote_repo, _result_repo, audit_repo = repos
    return VotingService(voter_repo, question_repo, vote_repo, audit_repo, crypto_service)


@pytest.fixture
def tally_service(repos, crypto_service):
    _voter_repo, question_repo, vote_repo, result_repo, audit_repo = repos
    return TallyService(question_repo, vote_repo, result_repo, audit_repo, crypto_service)


@pytest.fixture
def app_context(repos, voting_service, tally_service):
    voter_repo, question_repo, vote_repo, result_repo, audit_repo = repos
    return SimpleNamespace(
        voter_repo=voter_repo,
        question_repo=question_repo,
        vote_repo=vote_repo,
        result_repo=result_repo,
        audit_repo=audit_repo,
        voting_service=voting_service,
        tally_service=tally_service,
    )
