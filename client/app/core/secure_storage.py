from cryptography.fernet import Fernet
import keyring
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class SecureStorage:
    def __init__(self):
        self.service_name = "Canopus"
        self._ensure_encryption_key()
        self.fernet = Fernet(self._get_encryption_key())

    def _ensure_encryption_key(self):
        try:
            key = keyring.get_password(self.service_name, "encryption_key")
            if not key:
                key = Fernet.generate_key()
                keyring.set_password(
                    self.service_name,
                    "encryption_key",
                    key.decode()
                )
        except Exception as e:
            logger.error(f"Failed to setup encryption key: {str(e)}")
            raise

    def _get_encryption_key(self) -> bytes:
        key = keyring.get_password(self.service_name, "encryption_key")
        return key.encode()

    def store(self, key: str, value: str):
        try:
            encrypted_data = self.fernet.encrypt(value.encode())
            keyring.set_password(
                self.service_name,
                key,
                encrypted_data.decode()
            )
        except Exception as e:
            logger.error(f"Failed to store secure data: {str(e)}")
            raise

    def retrieve(self, key: str) -> str:
        try:
            encrypted_data = keyring.get_password(self.service_name, key)
            if encrypted_data:
                return self.fernet.decrypt(
                    encrypted_data.encode()
                ).decode()
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve secure data: {str(e)}")
            return None
