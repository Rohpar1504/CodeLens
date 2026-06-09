import time
import httpx
import jwt  # PyJWT
from app.config import settings

def generate_jwt() -> str:
    """Create a signed JWT for GitHub App authentication (valid 10 min)."""
    now = int(time.time())
    payload = {
        "iat": now - 60,   # issued slightly in the past to allow clock skew
        "exp": now + 540,  # 9 minutes from now (max is 10)
        "iss": settings.github_app_id,
    }
    with open(settings.github_private_key_path, "r") as f:
        private_key = f.read()

    return jwt.encode(payload, private_key, algorithm="RS256")


async def get_installation_token(installation_id: int) -> str:
    """Exchange a JWT for a short-lived installation access token (valid 1h)."""
    app_jwt = generate_jwt()
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {app_jwt}",
                "Accept": "application/vnd.github+json",
            },
        )
        response.raise_for_status()
        return response.json()["token"]