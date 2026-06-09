import httpx
import base64
import yaml


DEFAULT_CONFIG = {
    "enabled": True,
    "exclude": [],
    "severity_threshold": "suggestion",
}


async def fetch_repo_config(
    repo_full_name: str,
    token: str,
) -> dict:
    """
    Try to fetch .codelens.yml from the repo root.
    Falls back to defaults if not found.
    """
    url = f"https://api.github.com/repos/{repo_full_name}/contents/.codelens.yml"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    if response.status_code == 404:
        return DEFAULT_CONFIG

    if response.status_code != 200:
        print(f"[config] Could not fetch .codelens.yml: {response.status_code}")
        return DEFAULT_CONFIG

    # GitHub returns file content as base64
    content = base64.b64decode(response.json()["content"]).decode("utf-8")

    try:
        config = yaml.safe_load(content)
        # Merge with defaults so missing keys are filled in
        return {**DEFAULT_CONFIG, **config}
    except yaml.YAMLError as e:
        print(f"[config] Invalid .codelens.yml: {e}")
        return DEFAULT_CONFIG