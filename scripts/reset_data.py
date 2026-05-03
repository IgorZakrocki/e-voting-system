from crypto import KeyManager, PaillierService
from repositories import JsonRepository


def main() -> None:
    
    JsonRepository("data/votes.json").clear()
    JsonRepository("data/results.json").clear()
    JsonRepository("data/audit_log.json").clear()


    crypto_service = PaillierService()
    public_key, private_key = crypto_service.generate_keypair()
    KeyManager().save_keys(public_key, private_key)

if __name__ == "__main__":
    main()