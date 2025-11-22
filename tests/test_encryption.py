"""Tests for encryption module."""
import pytest
from shell_motorsport.encryption import MessageEncryptor
from shell_motorsport.config import AES_KEY


def test_encryptor_init():
    """Test encryptor initialization."""
    encryptor = MessageEncryptor(AES_KEY)
    assert encryptor.key == AES_KEY


def test_encryptor_init_invalid_key():
    """Test encryptor initialization with invalid key."""
    with pytest.raises(ValueError, match="16 bytes"):
        MessageEncryptor(b"short_key")


def test_encrypt():
    """Test message encryption."""
    encryptor = MessageEncryptor(AES_KEY)
    message = b"1234567890123456"  # 16 bytes
    encrypted = encryptor.encrypt(message)
    assert len(encrypted) == 16
    assert encrypted != message  # Should be different


def test_encrypt_invalid_length():
    """Test encryption with invalid message length."""
    encryptor = MessageEncryptor(AES_KEY)
    with pytest.raises(ValueError, match="16 bytes"):
        encryptor.encrypt(b"short")


def test_decrypt():
    """Test message decryption."""
    encryptor = MessageEncryptor(AES_KEY)
    original = b"1234567890123456"
    encrypted = encryptor.encrypt(original)
    decrypted = encryptor.decrypt(encrypted)
    assert decrypted == original


def test_decrypt_invalid_length():
    """Test decryption with invalid message length."""
    encryptor = MessageEncryptor(AES_KEY)
    with pytest.raises(ValueError, match="16 bytes"):
        encryptor.decrypt(b"short")


def test_encrypt_decrypt_roundtrip():
    """Test encrypt-decrypt roundtrip."""
    encryptor = MessageEncryptor(AES_KEY)
    messages = [
        b"1234567890123456",
        b"abcdefghijklmnop",
        b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f",
    ]

    for message in messages:
        encrypted = encryptor.encrypt(message)
        decrypted = encryptor.decrypt(encrypted)
        assert decrypted == message

