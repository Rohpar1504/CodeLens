import json
import openai
from app.config import settings
from app.webhooks.diff_parser import DiffHunk
from app.review.prompts import build_review_prompt, SYSTEM_PROMPT


async def review_hunk(
    hunk: DiffHunk,
    context_chunks: list[dict],
) -> dict:
    """
    Send a diff hunk to GPT-4o for review.
    Returns a dict with 'comments' and 'summary'.
    """
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    prompt = build_review_prompt(hunk, context_chunks)

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        max_tokens=1000,
        temperature=0.2,  # low temperature = more consistent, focused output
    )

    raw = response.choices[0].message.content

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        # If parsing fails return empty review rather than crashing
        print(f"[llm] Failed to parse response: {raw}")
        return {"comments": [], "summary": "Could not parse review."}

    return result


async def review_pull_request(
    hunks: list[DiffHunk],
    context_by_hunk: list[list[dict]],
) -> list[dict]:
    """
    Review all hunks in a PR.
    Returns a flat list of comment dicts ready to post to GitHub.
    """
    all_comments = []

    for hunk, context in zip(hunks, context_by_hunk):
        if not hunk.added_lines:
            continue  # skip pure deletions

        print(f"[llm] Reviewing {hunk.filename} @ line {hunk.start_line}")
        result = await review_hunk(hunk, context)

        summary = result.get("summary", "")
        print(f"[llm] Summary: {summary}")

        for comment in result.get("comments", []):
            all_comments.append({
                "path": hunk.filename,
                "line": comment.get("line", hunk.start_line),
                "severity": comment.get("severity", "suggestion"),
                "body": f"**[{comment.get('severity', 'suggestion').upper()}]** {comment.get('comment', '')}",
            })

    return all_comments