import httpx


async def post_review_comments(
    repo_full_name: str,
    pull_number: int,
    head_sha: str,
    comments: list[dict],
    token: str,
) -> None:
    """
    Post inline review comments on a pull request via the GitHub API.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    if not comments:
        # Post a simple passing review if no issues found
        await _post_review(
            repo_full_name, pull_number, head_sha,
            body="✅ **CodeLens** reviewed this PR and found no issues.",
            event="COMMENT",
            comments=[],
            headers=headers,
        )
        return

    # Format comments for GitHub API
    github_comments = []
    for c in comments:
        github_comments.append({
            "path": c["path"],
            "line": c["line"],
            "side": "RIGHT",  # RIGHT = new version of the file
            "body": c["body"],
        })

    # Post all comments as a single review
    summary_lines = [f"- {c['body']}" for c in comments]
    summary = f"**CodeLens** found {len(comments)} issue(s):\n\n" + "\n".join(summary_lines)

    await _post_review(
        repo_full_name, pull_number, head_sha,
        body=summary,
        event="COMMENT",
        comments=github_comments,
        headers=headers,
    )


async def _post_review(
    repo_full_name: str,
    pull_number: int,
    head_sha: str,
    body: str,
    event: str,
    comments: list[dict],
    headers: dict,
) -> None:
    url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pull_number}/reviews"

    payload = {
        "commit_id": head_sha,
        "body": body,
        "event": event,
        "comments": comments,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)

        if response.status_code not in (200, 201):
            print(f"[poster] GitHub API error: {response.status_code} {response.text}")
        else:
            print(f"[poster] Posted review with {len(comments)} inline comments")