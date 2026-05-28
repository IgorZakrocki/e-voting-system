import pytest

from crypto import KeyManager, PaillierService
from exceptions import KeyNotFoundError


def test_encrypt_and_decrypt_yes_vote(crypto_service):
    encrypted_vote = crypto_service.encrypt_vote(1)

    result = crypto_service.decrypt_result(encrypted_vote)

    assert result == 1


def test_encrypt_and_decrypt_no_vote(crypto_service):
    encrypted_vote = crypto_service.encrypt_vote(0)

    result = crypto_service.decrypt_result(encrypted_vote)

    assert result == 0


def test_homomorphic_addition_counts_only_yes_votes(crypto_service):
    encrypted_votes = [
        crypto_service.encrypt_vote(1),
        crypto_service.encrypt_vote(0),
        crypto_service.encrypt_vote(1),
    ]

    encrypted_sum = crypto_service.add_encrypted_votes(encrypted_votes)

    assert crypto_service.decrypt_result(encrypted_sum) == 2


def test_empty_vote_sum_is_zero(crypto_service):
    encrypted_sum = crypto_service.add_encrypted_votes([])

    assert crypto_service.decrypt_result(encrypted_sum) == 0


def test_encrypted_number_can_be_serialized_and_restored(crypto_service):
    encrypted_vote = crypto_service.encrypt_vote(1)

    serialized = crypto_service.serialize_encrypted_number(encrypted_vote)
    restored = crypto_service.deserialize_encrypted_number(serialized)

    assert crypto_service.decrypt_result(restored) == 1


def test_invalid_vote_value_is_not_encrypted(crypto_service):
    with pytest.raises(ValueError):
        crypto_service.encrypt_vote(2)


def test_encryption_requires_public_key():
    service = PaillierService()

    with pytest.raises(KeyNotFoundError):
        service.encrypt_vote(1)


def test_key_manager_saves_and_loads_keys(tmp_path, crypto_service):
    public_path = tmp_path / "keys" / "public_key.json"
    private_path = tmp_path / "keys" / "private_key.json"
    manager = KeyManager(public_path, private_path)

    manager.save_keys(crypto_service.public_key, crypto_service.private_key)
    loaded_public = manager.load_public_key()
    loaded_private = manager.load_private_key()

    assert loaded_public.n == crypto_service.public_key.n
    assert loaded_private.p == crypto_service.private_key.p
    assert loaded_private.q == crypto_service.private_key.q
