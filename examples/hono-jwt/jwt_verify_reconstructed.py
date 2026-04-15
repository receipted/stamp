"""JWT Verification Middleware — Python reconstruction of CVE-2026-22817 (Hono).

The vulnerability: when the JWK does not explicitly specify an algorithm,
the verifier falls back to the JWT header's 'alg' value. This means an
attacker-controlled token can influence how its own signature is verified.

This is a trust boundary failure: untrusted input (the JWT header)
steers the verification logic that is supposed to validate that input.

Reconstructed as Python for static analysis. The original is TypeScript
in honojs/hono v4.11.3, src/middleware/jwt/jwt.ts and src/utils/jwt/jws.ts.

Public references:
- CVE-2026-22817: https://nvd.nist.gov/vuln/detail/CVE-2026-22817
- Fix: hono v4.11.4 requires explicit alg option
"""

import json
import base64
import hmac
import hashlib
from typing import Any


def decode_jwt_header(token: str) -> dict[str, Any]:
    """Decode the JWT header (first segment). Pure."""
    header_b64 = token.split(".")[0]
    # Add padding
    padding = 4 - len(header_b64) % 4
    header_b64 += "=" * padding
    header_bytes = base64.urlsafe_b64decode(header_b64)
    return json.loads(header_bytes)


def decode_jwt_payload(token: str) -> dict[str, Any]:
    """Decode the JWT payload (second segment). Pure."""
    payload_b64 = token.split(".")[1]
    padding = 4 - len(payload_b64) % 4
    payload_b64 += "=" * padding
    payload_bytes = base64.urlsafe_b64decode(payload_b64)
    return json.loads(payload_bytes)


def find_matching_jwk(header: dict, jwks: list[dict]) -> dict | None:
    """Find the JWK matching the JWT header's 'kid' field. Pure."""
    kid = header.get("kid")
    for jwk in jwks:
        if jwk.get("kid") == kid:
            return jwk
    return jwks[0] if jwks else None


def resolve_algorithm(header: dict, jwk: dict, alg_option: str | None = None) -> str:
    """Resolve which algorithm to use for verification.

    VULNERABILITY (CVE-2026-22817):
    When neither the JWK nor alg_option specifies an algorithm,
    this function falls back to the JWT header's 'alg' value.
    The token is telling the verifier how to verify itself.

    Pure function — but the trust boundary is wrong.
    """
    # Priority 1: explicit option from server config
    if alg_option:
        return alg_option

    # Priority 2: JWK's declared algorithm
    if jwk.get("alg"):
        return jwk["alg"]

    # Priority 3: JWT header's algorithm — THIS IS THE BUG
    # The attacker controls this value. It should never be trusted.
    return header.get("alg", "HS256")


def verify_signature(token: str, key: bytes, algorithm: str) -> bool:
    """Verify JWT signature using the resolved algorithm. Pure."""
    parts = token.split(".")
    if len(parts) != 3:
        return False

    message = f"{parts[0]}.{parts[1]}".encode()
    signature_b64 = parts[2]
    padding = 4 - len(signature_b64) % 4
    signature_b64 += "=" * padding
    signature = base64.urlsafe_b64decode(signature_b64)

    if algorithm == "none":
        # Algorithm "none" means no signature required — always passes
        return True

    if algorithm.startswith("HS"):
        expected = hmac.new(key, message, hashlib.sha256).digest()
        return hmac.compare_digest(expected, signature)

    return False


def verify_jwt(token: str, jwks: list[dict], secret: bytes,
               alg: str | None = None) -> dict[str, Any] | None:
    """Verify a JWT token and return its payload.

    This is the main entry point for JWT verification.
    It finds the matching key, resolves the algorithm, and verifies.

    Args:
        token: The JWT string.
        jwks: List of JWK objects (from JWKS endpoint).
        secret: The HMAC secret key.
        alg: Explicit algorithm override (server-side).

    Returns:
        The decoded payload if verification succeeds, None otherwise.
    """
    header = decode_jwt_header(token)
    jwk = find_matching_jwk(header, jwks)

    if not jwk:
        return None

    # VULNERABILITY: algorithm resolved from untrusted header
    algorithm = resolve_algorithm(header, jwk, alg)

    if not verify_signature(token, secret, algorithm):
        return None

    return decode_jwt_payload(token)
