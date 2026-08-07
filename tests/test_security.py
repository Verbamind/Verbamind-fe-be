"""TDD tests for security module — AES-256 encryption, DPAPI key protection, license activation.

RED phase: all imports will fail since modules don't exist yet.
"""

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as td:
        yield td


class TestEncryptor:
    """AES-256 encryption/decryption tests."""

    def test_encrypt_decrypt_bytes_roundtrip(self):
        from verbamind.security.encryptor import decrypt_bytes, encrypt_bytes, generate_aes_key

        key = generate_aes_key()
        plaintext = b"Hello, this is sensitive patient audio data!"

        encrypted = encrypt_bytes(plaintext, key)
        assert encrypted != plaintext
        assert len(encrypted) > len(plaintext)

        decrypted = decrypt_bytes(encrypted, key)
        assert decrypted == plaintext

    def test_encrypt_decrypt_file_roundtrip(self, temp_dir):
        from verbamind.security.encryptor import decrypt_file, encrypt_file, generate_aes_key

        key = generate_aes_key()
        original = b"Patient session recording data " * 1000
        input_path = Path(temp_dir) / "test_input.bin"
        encrypted_path = Path(temp_dir) / "test_output.vera"
        decrypted_path = Path(temp_dir) / "test_decrypted.bin"

        input_path.write_bytes(original)

        encrypt_file(str(input_path), str(encrypted_path), key)
        assert encrypted_path.exists()
        assert encrypted_path.read_bytes() != original

        decrypt_file(str(encrypted_path), str(decrypted_path), key)
        assert decrypted_path.read_bytes() == original

    def test_decrypt_with_wrong_key_fails(self, temp_dir):
        from verbamind.security.encryptor import decrypt_file, encrypt_file, generate_aes_key

        key1 = generate_aes_key()
        key2 = generate_aes_key()

        original = b"test data"
        input_path = Path(temp_dir) / "input.bin"
        encrypted_path = Path(temp_dir) / "encrypted.vera"
        decrypted_path = Path(temp_dir) / "decrypted.bin"

        input_path.write_bytes(original)
        encrypt_file(str(input_path), str(encrypted_path), key1)

        with pytest.raises(Exception):
            decrypt_file(str(encrypted_path), str(decrypted_path), key2)

    def test_tampered_ciphertext_detected(self, temp_dir):
        from verbamind.security.encryptor import decrypt_bytes, encrypt_bytes, generate_aes_key

        key = generate_aes_key()
        plaintext = b"original data to be tampered with"

        encrypted = encrypt_bytes(plaintext, key)
        tampered = bytearray(encrypted)
        tampered[20] ^= 0xFF

        with pytest.raises(Exception):
            decrypt_bytes(bytes(tampered), key)

    def test_generate_aes_key_produces_256_bit(self):
        from verbamind.security.encryptor import generate_aes_key

        key = generate_aes_key()
        assert len(key) == 32

    def test_generate_aes_key_is_unique(self):
        from verbamind.security.encryptor import generate_aes_key

        keys = {generate_aes_key() for _ in range(20)}
        assert len(keys) == 20

    def test_encrypt_same_data_different_iv(self):
        from verbamind.security.encryptor import encrypt_bytes, generate_aes_key

        key = generate_aes_key()
        plaintext = b"same data"

        c1 = encrypt_bytes(plaintext, key)
        c2 = encrypt_bytes(plaintext, key)
        assert c1 != c2

    def test_empty_data(self):
        from verbamind.security.encryptor import decrypt_bytes, encrypt_bytes, generate_aes_key

        key = generate_aes_key()
        encrypted = encrypt_bytes(b"", key)
        decrypted = decrypt_bytes(encrypted, key)
        assert decrypted == b""

    def test_large_data(self):
        from verbamind.security.encryptor import decrypt_bytes, encrypt_bytes, generate_aes_key

        key = generate_aes_key()
        plaintext = os.urandom(1024 * 1024)
        encrypted = encrypt_bytes(plaintext, key)
        decrypted = decrypt_bytes(encrypted, key)
        assert decrypted == plaintext


class TestKeyManager:
    """DPAPI key management tests."""

    @pytest.fixture(autouse=True)
    def _isolate_key_dir(self, temp_dir):
        from verbamind.security import key_manager

        original = key_manager._key_dir
        key_manager._set_key_dir(Path(temp_dir))
        yield
        key_manager._set_key_dir(original)

    def test_generate_aes_key_unique(self):
        from verbamind.security.key_manager import generate_aes_key

        k1 = generate_aes_key()
        k2 = generate_aes_key()
        assert k1 != k2
        assert len(k1) == 32

    def test_initialize_and_load_key(self):
        from verbamind.security.key_manager import initialize_key, is_key_initialized, load_key

        assert not is_key_initialized()
        assert not initialize_key()
        assert is_key_initialized()
        key = load_key()
        assert len(key) == 32

    def test_status_before_initialization(self):
        from verbamind.security.key_manager import is_key_initialized

        assert not is_key_initialized()

    def test_multiple_initialize_idempotent(self):
        from verbamind.security.key_manager import initialize_key, is_key_initialized, load_key

        initialize_key()
        key1 = load_key()
        was_initialized = initialize_key()
        key2 = load_key()

        assert was_initialized is True
        assert key1 == key2
        assert is_key_initialized()


class TestActivation:
    """License activation tests."""

    def test_hwid_is_stable(self):
        from verbamind.security.activation import get_hardware_id

        hwid1 = get_hardware_id()
        hwid2 = get_hardware_id()
        assert hwid1 == hwid2
        assert len(hwid1) > 0

    def test_hwid_is_string(self):
        from verbamind.security.activation import get_hardware_id

        hwid = get_hardware_id()
        assert isinstance(hwid, str)

    def test_validate_license_key_valid(self):
        from verbamind.security.activation import generate_license_key, get_hardware_id, validate_license_key

        hwid = get_hardware_id()
        key = generate_license_key(hwid, "secret-master-key")
        assert validate_license_key(key, hwid, "secret-master-key")

    def test_validate_license_key_invalid_wrong_hwid(self):
        from verbamind.security.activation import generate_license_key, get_hardware_id, validate_license_key

        hwid = get_hardware_id()
        key = generate_license_key(hwid, "secret-master-key")
        assert not validate_license_key(key, "different-hwid", "secret-master-key")

    def test_validate_license_key_invalid_garbage(self):
        from verbamind.security.activation import get_hardware_id, validate_license_key

        assert not validate_license_key("INVALID-KEY-12345", get_hardware_id(), "secret")

    def test_activation_state(self, temp_dir):
        from verbamind.security.activation import (
            activate,
            deactivate,
            is_activated,
        )

        assert not is_activated()
        activate("test-license-key")
        assert is_activated()
        deactivate()
        assert not is_activated()
