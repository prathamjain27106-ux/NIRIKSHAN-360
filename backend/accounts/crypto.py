"""
NIRIKSHAN 360 — AES-GCM Identity Encryption
==============================================
Authenticated encryption for complainant identity.
Key is supplied via IDENTITY_ENCRYPTION_KEY environment variable.
Never stores plaintext identity.
"""

import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings


def _get_key() -> bytes:
    """Retrieve the AES-256 key from environment.
    Key should be 32 bytes, base64-encoded in the env var."""
    import sys
    raw = settings.IDENTITY_ENCRYPTION_KEY
    if not raw:
        # In development/test without a key, use a deterministic dev key
        # This is NOT secure — production MUST set IDENTITY_ENCRYPTION_KEY
        is_dev_or_test = settings.DEBUG or "test" in sys.argv
        if is_dev_or_test:
            return b"NIRIKSHAN360_DEV_KEY_32B_NOTPROD"  # exactly 32 bytes
        raise ValueError(
            "IDENTITY_ENCRYPTION_KEY is not set. "
            "Set it to a base64-encoded 32-byte key in production."
        )

    try:
        key = base64.b64decode(raw)
    except Exception:
        # Treat as raw UTF-8 and pad/truncate to 32 bytes
        key = raw.encode("utf-8")[:32].ljust(32, b"\x00")
    if len(key) != 32:
        raise ValueError(
            f"IDENTITY_ENCRYPTION_KEY must decode to exactly 32 bytes, got {len(key)}."
        )
    return key


def encrypt_identity(plaintext: str) -> tuple[bytes, bytes]:
    """Encrypt plaintext identity with AES-GCM.
    Returns (ciphertext, nonce) as bytes."""
    if not plaintext:
        return b"", b""
    key = _get_key()
    nonce = os.urandom(12)  # 96-bit nonce for AES-GCM
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return ciphertext, nonce


def decrypt_identity(ciphertext: bytes, nonce: bytes) -> str:
    """Decrypt AES-GCM encrypted identity.
    Should ONLY be called after dual-approval workflow completes."""
    if not ciphertext or not nonce:
        return "[no identity stored]"
    key = _get_key()
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")


def generate_encryption_key() -> str:
    """Generate a new random AES-256 key, base64-encoded.
    Utility for setup — run: python -c 'from accounts.crypto import generate_encryption_key; print(generate_encryption_key())'
    """
    return base64.b64encode(os.urandom(32)).decode("ascii")
