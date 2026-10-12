import os
from dataclasses import dataclass

import jwt
from fastapi import Header, HTTPException


@dataclass(frozen=True)
class Identity:
    subject: str
    claims: dict


def authenticate(
    authorization: str | None = Header(default=None),
    x_authenticated_user: str | None = Header(default=None),
) -> Identity | None:
    """Validate a JWT, or use a trusted identity proxy when explicitly enabled."""
    if os.getenv("REQUIRE_AUTH", "false").lower() != "true":
        return None

    if x_authenticated_user and os.getenv("TRUST_PROXY_IDENTITY", "false").lower() == "true":
        return Identity(subject=x_authenticated_user, claims={"sub": x_authenticated_user, "source": "proxy"})

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication is required")

    token = authorization.removeprefix("Bearer ").strip()
    issuer = os.getenv("AUTH_ISSUER")
    audience = os.getenv("AUTH_AUDIENCE")
    secret = os.getenv("AUTH_HS256_SECRET")
    jwks_url = os.getenv("AUTH_JWKS_URL")
    options = {"require": ["sub"]}

    try:
        if secret:
            claims = jwt.decode(token, secret, algorithms=["HS256"], issuer=issuer, audience=audience, options=options)
        elif jwks_url:
            key = jwt.PyJWKClient(jwks_url).get_signing_key_from_jwt(token).key
            claims = jwt.decode(token, key, algorithms=["RS256", "ES256"], issuer=issuer, audience=audience, options=options)
        else:
            raise HTTPException(status_code=500, detail="Authentication is enabled but no verifier is configured")
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid identity token") from exc

    return Identity(subject=str(claims["sub"]), claims=claims)
