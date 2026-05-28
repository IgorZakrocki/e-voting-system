from crypto import KeyManager, PaillierService
from pathlib import Path
import json

VOTERS_PATH = Path("data/voters.json")

def clear_runtime_data() -> None:
    files_to_remove = [
        "data/votes.json",
        "data/results.json",
        "data/audit_log.json",
        "keys/private_key.json",
        "keys/public_key.json",
    ]

    for file_path in files_to_remove:
        Path(file_path).unlink(missing_ok=True)

def reset_voters_status(path: Path = VOTERS_PATH) -> None:
    """Ustawia voted=False dla każdego wyborcy w data/voters.json."""
    if not path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku wyborców: {path}")

    with path.open("r", encoding="utf-8") as file:
        voters = json.load(file)

    if not isinstance(voters, list):
        raise ValueError(f"Nieprawidłowy format pliku {path}: oczekiwano listy wyborców")

    for voter in voters:
        if not isinstance(voter, dict):
            raise ValueError(f"Nieprawidłowy rekord wyborcy w pliku {path}: {voter!r}")
        voter["voted"] = False

    with path.open("w", encoding="utf-8") as file:
        json.dump(voters, file, ensure_ascii=False, indent=2)
        file.write("\n")

def regenerate_keys() -> None:
    crypto_service = PaillierService()
    public_key, private_key = crypto_service.generate_keypair() #n_length=128
    KeyManager().save_keys(public_key, private_key)
    

def main() -> None:
    clear_runtime_data()
    reset_voters_status()
    regenerate_keys()


if __name__ == "__main__":
    main()