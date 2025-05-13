from cryptography.fernet import Fernet
from dotenv import load_dotenv

import os

load_dotenv()
# Generate once and store securely (e.g., in .env or vault)
FERNET_KEY = os.getenv('FERNET_KEY')
fernet = Fernet(FERNET_KEY)


def encrypt_token(token: str) -> str:
    return fernet.encrypt(token.encode()).decode()

def decrypt_token(token: str) -> str:
    return fernet.decrypt(token.encode()).decode()
