# encrypt_env.py
from cryptography.fernet import Fernet

# 1) Generate and save a key (do this only once!)
key = Fernet.generate_key()
with open("secret.key", "wb") as f:
    f.write(key)

# 2) Read your plaintext .env and encrypt it
with open(".env", "rb") as f:
    data = f.read()

fernet = Fernet(key)
encrypted = fernet.encrypt(data)

with open(".env.enc", "wb") as f:
    f.write(encrypted)

print("Encrypted .env → .env.enc, key saved to secret.key")
