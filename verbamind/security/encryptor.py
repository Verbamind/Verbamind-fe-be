"""AES-256-GCM encryption/decryption for audio files and in-memory data."""


from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


def generate_aes_key() -> bytes:
    return get_random_bytes(32)


def encrypt_bytes(data: bytes, key: bytes) -> bytes:
    nonce = get_random_bytes(12)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    return nonce + tag + ciphertext


def decrypt_bytes(data: bytes, key: bytes) -> bytes:
    nonce = data[:12]
    tag = data[12:28]
    ciphertext = data[28:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)


def encrypt_file(input_path: str, output_path: str, key: bytes) -> None:
    with open(input_path, "rb") as f:
        plaintext = f.read()
    encrypted = encrypt_bytes(plaintext, key)
    with open(output_path, "wb") as f:
        f.write(encrypted)


def decrypt_file(input_path: str, output_path: str, key: bytes) -> None:
    with open(input_path, "rb") as f:
        encrypted = f.read()
    plaintext = decrypt_bytes(encrypted, key)
    with open(output_path, "wb") as f:
        f.write(plaintext)
