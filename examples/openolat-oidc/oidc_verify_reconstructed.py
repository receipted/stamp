"""OpenID Connect Token Verification — Python reconstruction of CVE-2026-31946 (OpenOLAT).

The vulnerability: the JWT parser silently discards the signature segment,
and the access token validation only checks claim-level fields (issuer,
audience, state, nonce) without any cryptographic signature verification.

It checked the token fields but never verified the signature.

This is a WITNESS failure: the system performs claim-level checks without
cryptographic witness. The token looks validated but the signature — the
only proof that the identity provider actually issued it — was never checked.

Reconstructed as Python for static analysis. The original is Java
in OpenOLAT versions 10.5.4 through 20.2.4.

Public references:
- CVE-2026-31946: https://nvd.nist.gov/vuln/detail/CVE-2026-31946
- Fix: OpenOLAT v20.2.5
"""

import json
import base64
import time
from typing import Any


class JSONWebToken:
    """JWT parser that silently discards the signature.

    VULNERABILITY: The parse method strips the signature segment
    instead of preserving it for verification.
    """

    def __init__(self, header: dict, payload: dict):
        self.header = header
        self.payload = payload
        # NOTE: signature is NOT stored — silently discarded

    @classmethod
    def parse(cls, token_string: str) -> "JSONWebToken":
        """Parse a compact JWT string.

        VULNERABILITY (CVE-2026-31946):
        This method splits the token into header.payload.signature
        but only decodes header and payload. The signature is silently
        dropped. No error, no warning, no flag.
        """
        parts = token_string.split(".")
        # Parts: [header, payload, signature]
        # We only use parts[0] and parts[1] — signature is DISCARDED

        header_b64 = parts[0]
        payload_b64 = parts[1]
        # parts[2] (signature) is never used

        header = json.loads(_b64decode(header_b64))
        payload = json.loads(_b64decode(payload_b64))

        return cls(header=header, payload=payload)

    def get_claim(self, name: str) -> Any:
        return self.payload.get(name)

    def get_issuer(self) -> str | None:
        return self.payload.get("iss")

    def get_audience(self) -> str | None:
        return self.payload.get("aud")

    def get_expiration(self) -> int | None:
        return self.payload.get("exp")


def _b64decode(s: str) -> bytes:
    """URL-safe base64 decode with padding. Pure."""
    padding = 4 - len(s) % 4
    s += "=" * padding
    return base64.urlsafe_b64decode(s)


class OpenIdConnectApi:
    """OpenID Connect API for validating access tokens.

    VULNERABILITY: validates claim fields but never verifies
    the cryptographic signature against the IdP's JWKS endpoint.
    """

    def __init__(self, issuer: str, client_id: str, jwks_uri: str):
        self.issuer = issuer
        self.client_id = client_id
        self.jwks_uri = jwks_uri

    def get_access_token(self, token_string: str, expected_state: str,
                         expected_nonce: str) -> dict | None:
        """Validate and return the access token claims.

        VULNERABILITY (CVE-2026-31946):
        This method:
        1. Parses the JWT (which silently discards the signature)
        2. Checks issuer, audience, state, nonce, expiration
        3. Returns the claims as valid

        It NEVER:
        - Fetches the JWKS from the identity provider
        - Verifies the cryptographic signature
        - Checks that the token was actually issued by the claimed issuer

        The token is "validated" at the claim level but completely
        unverified at the cryptographic level. Anyone can forge a token
        with the right issuer/audience/state/nonce and it will pass.
        """
        token = JSONWebToken.parse(token_string)

        # Check issuer
        if token.get_issuer() != self.issuer:
            return None

        # Check audience
        if token.get_audience() != self.client_id:
            return None

        # Check state
        state = token.get_claim("state")
        if state != expected_state:
            return None

        # Check nonce
        nonce = token.get_claim("nonce")
        if nonce != expected_nonce:
            return None

        # Check expiration
        exp = token.get_expiration()
        if exp and exp < time.time():
            return None

        # ALL CHECKS PASS — but signature was never verified!
        # An attacker who knows the issuer, client_id, state, and nonce
        # can forge a token that passes all these checks.

        return token.payload


def validate_oidc_login(token_string: str, config: dict) -> dict | None:
    """Validate an OpenID Connect login token.

    Pure validation function. Returns user claims if valid.

    Args:
        token_string: The JWT from the identity provider.
        config: OIDC configuration with issuer, client_id, jwks_uri.

    Returns:
        User claims dict if valid, None otherwise.
    """
    api = OpenIdConnectApi(
        issuer=config["issuer"],
        client_id=config["client_id"],
        jwks_uri=config["jwks_uri"],
    )

    claims = api.get_access_token(
        token_string,
        expected_state=config.get("state", ""),
        expected_nonce=config.get("nonce", ""),
    )

    if not claims:
        return None

    return {
        "sub": claims.get("sub"),
        "email": claims.get("email"),
        "name": claims.get("name"),
        "roles": claims.get("roles", []),
    }
