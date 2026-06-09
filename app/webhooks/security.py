import hashlib
import hmac
from fastapi import HTTPException, Request
from app.config import settings


async def verify_webhook_signature(request: Request) -> bytes:
    """
    Reads the raw request body and verifies the GitHub HMAC-SHA256 signature.
    Returns the raw body bytes so the caller can parse them.
    Raises HTTP 401 if the signature is missing or invalid.
    """
    signature_header = request.headers.get("X-Hub-Signature-256")
    if not signature_header:
        raise HTTPException(status_code=401, detail="Missing signature header")

    body = await request.body()

    expected_sig = "sha256=" + hmac.new(
        settings.github_webhook_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, signature_header):
        raise HTTPException(status_code=401, detail="Invalid signature")

    return body