from crypto import KeyManager, PaillierService


def main() -> None:
    crypto_service = PaillierService()
    public_key, private_key = crypto_service.generate_keypair()
    KeyManager().save_keys(public_key, private_key)
    print("Paillier key pair generated in keys/.")


if __name__ == "__main__":
    main()
