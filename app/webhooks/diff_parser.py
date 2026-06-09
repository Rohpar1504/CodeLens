import re
from dataclasses import dataclass


@dataclass
class DiffHunk:
    filename: str
    start_line: int
    added_lines: list[str]
    removed_lines: list[str]
    context: str  # the full raw hunk text


def parse_pull_request_files(pr_files: list[dict]) -> list[DiffHunk]:
    """
    Takes the list of file objects from GitHub's
    GET /repos/{owner}/{repo}/pulls/{pull_number}/files
    and returns a flat list of DiffHunk objects.
    """
    hunks = []
    for file in pr_files:
        filename = file.get("filename", "")
        patch = file.get("patch", "")
        if not patch:
            continue  # binary files, deletions, etc.

        hunks.extend(_parse_patch(filename, patch))

    return hunks


def _parse_patch(filename: str, patch: str) -> list[DiffHunk]:
    """Split a patch string on @@ hunk headers."""
    hunk_pattern = re.compile(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
    parts = hunk_pattern.split(patch)
    # parts alternates: [pre-match, start_line, hunk_body, start_line, hunk_body, ...]

    hunks = []
    # parts[0] is text before first @@, skip it
    for i in range(1, len(parts) - 1, 2):
        start_line = int(parts[i])
        body = parts[i + 1]

        added = [l[1:] for l in body.splitlines() if l.startswith("+")]
        removed = [l[1:] for l in body.splitlines() if l.startswith("-")]

        hunks.append(DiffHunk(
            filename=filename,
            start_line=start_line,
            added_lines=added,
            removed_lines=removed,
            context=body,
        ))

    return hunks