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
    Supports either 64-character hex string (32 bytes) or base64 encoded 32 bytes."""
    import sys
    raw = getattr(settings, "IDENTITY_ENCRYPTION_KEY", None)
    if not raw:
        # In development/test without a key, use a deterministic dev key
        # This is NOT secure — production MUST set IDENTITY_ENCRYPTION_KEY
        is_dev_or_test = settings.DEBUG or "test" in sys.argv
        if is_dev_or_test:
            return b"NIRIKSHAN360_DEV_KEY_32B_NOTPROD"  # exactly 32 bytes
        raise ValueError(
            "IDENTITY_ENCRYPTION_KEY is not set. "
            "Set it to a 32-byte hex key or base64-encoded key in production."
        )

    key = None
    # 1. Try 64-char hex format (standard from README & .env.example)
    if len(raw.strip()) == 64:
        try:
            key = bytes.fromhex(raw.strip())
        except ValueError:
            pass

    # 2. Try base64
    if key is None:
        try:
            b64_key = base64.b64decode(raw.strip())
            if len(b64_key) == 32:
                key = b64_key
        except Exception:
            pass

    # 3. Fallback to raw utf-8 padded/truncated to 32 bytes
    if key is None or len(key) != 32:
        key = raw.strip().encode("utf-8")[:32].ljust(32, b"\x00")

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
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce for AES-GCM
    data = plaintext.encode("utf-8")
    ciphertext = aesgcm.encrypt(nonce, data, None)
    return ciphertext, nonce


def decrypt_identity(ciphertext: bytes, nonce: bytes) -> str:
    """Decrypt ciphertext with AES-GCM.
    Returns plaintext identity string."""
    if not ciphertext or not nonce:
        return ""
    key = _get_key()
    aesgcm = AESGCM(key)
    try:
        decrypted = aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted.decode("utf-8")
    except Exception as e:
        raise ValueError(f"Identity decryption failed: {e}")
