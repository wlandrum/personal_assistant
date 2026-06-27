import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()


def _key() -> bytes:
    return os.environ["CREDENTIALS_KEY"].encode()


def encrypt(plaintext: str) -> bytes:
    return Fernet(_key()).encrypt(plaintext.encode())


def decrypt(token: bytes) -> str:
    return Fernet(_key()).decrypt(token).decode()
