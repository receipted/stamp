"""SHA-256 content hashing for blob deduplication."""

import hashlib


def hash_content(content: str | bytes) -> str:
    """Compute SHA-256 hash of content.

    Args:
        content: String or bytes to hash.

    Returns:
        Hash string in "sha256:<hex>" format.
    """
    if isinstance(content, str):
        content = content.encode("utf-8")
    digest = hashlib.sha256(content).hexdigest()
    return f"sha256:{digest}"


def hash_to_path_parts(content_hash: str) -> tuple[str, str]:
    """Split a content hash into directory prefix and filename.

    Args:
        content_hash: Hash in "sha256:<hex>" format.

    Returns:
        Tuple of (first_2_hex_chars, full_hex) for filesystem layout.
    """
    hex_digest = content_hash.removeprefix("sha256:")
    return hex_digest[:2], hex_digest
