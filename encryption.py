"""AES encryption module for RC car messages."""
from Crypto.Cipher import AES
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class MessageEncryptor:
    """Handles AES encryption for RC car control messages."""

    def __init__(self, key: bytes):
        """
        Initialize the encryptor with an AES key.

        Args:
            key: AES encryption key (16 bytes for AES-128)
        """
        if len(key) != 16:
            raise ValueError("AES key must be 16 bytes long")
        self.key = key

    def encrypt(self, message: bytes) -> bytes:
        """
        Encrypt a message using AES-128 ECB mode.

        Args:
            message: Plaintext message to encrypt (must be 16 bytes)

        Returns:
            Encrypted message bytes

        Raises:
            ValueError: If message length is not 16 bytes
        """
        if len(message) != 16:
            raise ValueError(f"Message must be exactly 16 bytes, got {len(message)}")
        try:
            cipher = AES.new(self.key, AES.MODE_ECB)
            return cipher.encrypt(message)
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, encrypted_message: bytes) -> Optional[bytes]:
        """
        Decrypt a message using AES-128 ECB mode.

        Args:
            encrypted_message: Encrypted message to decrypt (must be 16 bytes)

        Returns:
            Decrypted message bytes, or None if decryption fails

        Raises:
            ValueError: If encrypted message length is not 16 bytes
        """
        if len(encrypted_message) != 16:
            raise ValueError(
                f"Encrypted message must be exactly 16 bytes, got {len(encrypted_message)}"
            )
        try:
            cipher = AES.new(self.key, AES.MODE_ECB)
            return cipher.decrypt(encrypted_message)
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None

