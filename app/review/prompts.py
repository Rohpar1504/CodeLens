from app.webhooks.diff_parser import DiffHunk


def build_review_prompt(
    hunk: DiffHunk,
    context_chunks: list[dict],
) -> str:
    """
    Build the user prompt for a single diff hunk review.
    Includes the diff and retrieved codebase context.
    """
    context_text = ""
    if context_chunks:
        context_text = "\n\n### Relevant code from this codebase:\n"
        for i, chunk in enumerate(context_chunks, 1):
            meta = chunk["metadata"]
            context_text += f"""
--- Context {i}: {meta['filepath']} (lines {meta['start_line']}-{meta['end_line']}) ---
{chunk['content']}
"""

    added = "\n".join(hunk.added_lines)
    removed = "\n".join(hunk.removed_lines)

    return f"""You are reviewing a pull request. Analyze the following code change and provide feedback.

### File: {hunk.filename} (starting at line {hunk.start_line})

### Lines removed:
{removed if removed else "(none)"}

### Lines added:
{added if added else "(none)"}
{context_text}

Respond with a JSON object in exactly this format:
{{
  "comments": [
    {{
      "line": <line number as integer>,
      "severity": "<suggestion | warning | error>",
      "comment": "<your feedback>"
    }}
  ],
  "summary": "<one sentence overall assessment>"
}}

Rules:
- Only comment on real issues — bugs, security problems, performance, clarity
- If the code looks fine, return an empty comments array
- Line numbers must be within the changed lines ({hunk.start_line} to {hunk.start_line + len(hunk.added_lines)})
- Keep comments concise and actionable
- Return valid JSON only, no extra text
"""


SYSTEM_PROMPT = """You are CodeLens, an expert code reviewer integrated into GitHub.
You give precise, constructive feedback on pull requests.
You focus on bugs, security issues, performance problems, and unclear code.
You match the tone of the team — professional but direct.
You always return valid JSON as instructed."""