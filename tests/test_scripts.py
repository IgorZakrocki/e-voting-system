import json

import pytest

from scripts import clean_system, prepare_system


def test_clean_system_removes_runtime_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for relative_path in [
        "data/votes.json",
        "data/results.json",
        "data/audit_log.json",
        "keys/private_key.json",
        "keys/public_key.json",
    ]:
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")

    clean_system.clear_runtime_data()

    assert not (tmp_path / "data/votes.json").exists()
    assert not (tmp_path / "data/results.json").exists()
    assert not (tmp_path / "data/audit_log.json").exists()
    assert not (tmp_path / "keys/private_key.json").exists()
    assert not (tmp_path / "keys/public_key.json").exists()


def test_clean_system_resets_voters_status(tmp_path):
    voters_path = tmp_path / "voters.json"
    voters_path.write_text(
        json.dumps([
            {"voter_id": "1", "voted": True},
            {"voter_id": "2", "voted": True},
        ]),
        encoding="utf-8",
    )

    clean_system.reset_voters_status(voters_path)

    voters = json.loads(voters_path.read_text(encoding="utf-8"))
    assert [voter["voted"] for voter in voters] == [False, False]


def test_clean_system_rejects_wrong_voters_file_format(tmp_path):
    voters_path = tmp_path / "voters.json"
    voters_path.write_text(json.dumps({"voter_id": "1"}), encoding="utf-8")

    with pytest.raises(ValueError):
        clean_system.reset_voters_status(voters_path)


def test_prepare_system_regenerates_key_files(tmp_path, monkeypatch):
    class FakePublicKey:
        n = 17

    class FakePrivateKey:
        p = 3
        q = 5

    class FakePaillierService:
        def generate_keypair(self):
            return FakePublicKey(), FakePrivateKey()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(prepare_system, "PaillierService", FakePaillierService)

    prepare_system.regenerate_keys()

    public_key = json.loads((tmp_path / "keys/public_key.json").read_text(encoding="utf-8"))
    private_key = json.loads((tmp_path / "keys/private_key.json").read_text(encoding="utf-8"))
    assert public_key == {"n": "17"}
    assert private_key == {"p": "3", "q": "5"}
