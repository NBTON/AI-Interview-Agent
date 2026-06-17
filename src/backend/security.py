import base64
import hashlib
import hmac
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import HTTPException


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=True)


def _candidate_secret() -> bytes:
    secret = os.environ.get("CANDIDATE_TOKEN_SECRET") or os.environ.get("APP_SECRET_KEY")
    if not secret:
        raise HTTPException(status_code=503, detail="Candidate verification is not configured")
    return secret.encode("utf-8")


def create_candidate_token(email: str, ttl_seconds: int = 3600) -> str:
    payload = {
        "email": email.strip().lower(),
        "exp": int(time.time()) + ttl_seconds,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    encoded_payload = base64.urlsafe_b64encode(payload_bytes).rstrip(b"=")
    signature = hmac.new(_candidate_secret(), encoded_payload, hashlib.sha256).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).rstrip(b"=")
    return f"{encoded_payload.decode()}.{encoded_signature.decode()}"


def verify_candidate_token(token: str, email: str) -> None:
    if not token:
        raise HTTPException(status_code=401, detail="Candidate verification token is required")

    try:
        encoded_payload, encoded_signature = token.split(".", 1)
        expected = hmac.new(_candidate_secret(), encoded_payload.encode("utf-8"), hashlib.sha256).digest()
        actual = base64.urlsafe_b64decode(encoded_signature + "=" * (-len(encoded_signature) % 4))
        payload_bytes = base64.urlsafe_b64decode(encoded_payload + "=" * (-len(encoded_payload) % 4))
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid candidate verification token")

    if not hmac.compare_digest(actual, expected):
        raise HTTPException(status_code=401, detail="Invalid candidate verification token")
    if int(payload.get("exp", 0)) < int(time.time()):
        raise HTTPException(status_code=401, detail="Candidate verification token has expired")
    if not hmac.compare_digest(str(payload.get("email", "")).lower(), email.strip().lower()):
        raise HTTPException(status_code=403, detail="Candidate token does not match this email")
