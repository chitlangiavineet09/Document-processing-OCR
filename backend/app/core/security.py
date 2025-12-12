from typing import Optional
import hashlib
import secrets


def generate_request_id() -> str:
    """Generate a unique request ID for logging and tracing"""
    return secrets.token_urlsafe(16)


def hash_file_content(content: bytes) -> str:
    """Generate SHA256 hash of file content for deduplication"""
    return hashlib.sha256(content).hexdigest()

