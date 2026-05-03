import json
from pathlib import Path

from phe import paillier
from phe.paillier import EncryptedNumber, PaillierPrivateKey, PaillierPublicKey

from exceptions import KeyNotFoundError


class PaillierService:
    """Facade for Paillier cryptographic operations used by the voting system."""

    def __init__(self, public_key: PaillierPublicKey | None = None, private_key: PaillierPrivateKey | None = None):
        self.public_key = public_key
        self.private_key = private_key

    def generate_keypair(self) -> tuple[PaillierPublicKey, PaillierPrivateKey]:
        self.public_key, self.private_key = paillier.generate_paillier_keypair()
        return self.public_key, self.private_key

    def encrypt_vote(self, value: int) -> EncryptedNumber:
        if self.public_key is None:
            raise KeyNotFoundError("Public key is required for encryption.")
        if value not in (0, 1):
            raise ValueError("Vote value must be 0 or 1.")
        return self.public_key.encrypt(value)

    def add_encrypted_votes(self, encrypted_votes: list[EncryptedNumber]) -> EncryptedNumber:
        if self.public_key is None:
            raise KeyNotFoundError("Public key is required for homomorphic addition.")
        if not encrypted_votes:
            return self.public_key.encrypt(0)

        encrypted_sum = encrypted_votes[0]
        for encrypted_vote in encrypted_votes[1:]:
            encrypted_sum += encrypted_vote
        return encrypted_sum

    def decrypt_result(self, encrypted_sum: EncryptedNumber) -> int:
        if self.private_key is None:
            raise KeyNotFoundError("Private key is required for decryption.")
        return int(self.private_key.decrypt(encrypted_sum))

    def serialize_encrypted_number(self, encrypted_number: EncryptedNumber) -> dict[str, int | str]:
        return {
            "encrypted_vote": str(encrypted_number.ciphertext()),
            "exponent": encrypted_number.exponent,
        }

    def deserialize_encrypted_number(self, data: dict[str, int | str]) -> EncryptedNumber:
        if self.public_key is None:
            raise KeyNotFoundError("Public key is required for encrypted vote deserialization.")
        return EncryptedNumber(
            self.public_key,
            int(data["encrypted_vote"]),
            int(data["exponent"]),
        )


class KeyManager:
    """Reads and writes Paillier keys as JSON files."""

    def __init__(self, public_key_path: str | Path = "keys/public_key.json", private_key_path: str | Path = "keys/private_key.json"):
        self.public_key_path = Path(public_key_path)
        self.private_key_path = Path(private_key_path)

    def save_keys(self, public_key: PaillierPublicKey, private_key: PaillierPrivateKey) -> None:
        self.public_key_path.parent.mkdir(parents=True, exist_ok=True)
        self.private_key_path.parent.mkdir(parents=True, exist_ok=True)

        self.public_key_path.write_text(
            json.dumps({"n": str(public_key.n)}, indent=2),
            encoding="utf-8",
        )
        self.private_key_path.write_text(
            json.dumps(
                {
                    "p": str(private_key.p),
                    "q": str(private_key.q),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def load_public_key(self) -> PaillierPublicKey:
        data = self._load_json(self.public_key_path)
        if "n" not in data:
            raise KeyNotFoundError("Public key file is missing field 'n'. Run scripts/generate_keys.py first.")
        return PaillierPublicKey(n=int(data["n"]))

    def load_private_key(self) -> PaillierPrivateKey:
        public_key = self.load_public_key()
        data = self._load_json(self.private_key_path)
        if "p" not in data or "q" not in data:
            raise KeyNotFoundError("Private key file is missing fields 'p' and 'q'. Run scripts/generate_keys.py first.")
        return PaillierPrivateKey(public_key, int(data["p"]), int(data["q"]))

    @staticmethod
    def _load_json(path: Path) -> dict[str, str]:
        if not path.exists() or path.stat().st_size == 0:
            raise KeyNotFoundError(f"Key file does not exist or is empty: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not data:
            raise KeyNotFoundError(f"Key file is empty or invalid: {path}")
        return data
