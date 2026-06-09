import ast
import os
from dataclasses import dataclass


@dataclass
class CodeChunk:
    content: str
    filepath: str
    start_line: int
    end_line: int
    chunk_type: str  # "function", "class", "module"
    name: str


def chunk_repository(repo_path: str) -> list[CodeChunk]:
    """
    Walk all Python files in a repo and split them into
    function/class level chunks.
    """
    chunks = []
    for root, dirs, files in os.walk(repo_path):
        # Skip hidden folders and common non-code dirs
        dirs[:] = [
            d for d in dirs
            if not d.startswith(".")
            and d not in ("node_modules", "__pycache__", ".venv", "venv")
        ]
        for filename in files:
            if filename.endswith(".py"):
                filepath = os.path.join(root, filename)
                relative_path = os.path.relpath(filepath, repo_path)
                chunks.extend(_chunk_python_file(filepath, relative_path))

    return chunks


def _chunk_python_file(filepath: str, relative_path: str) -> list[CodeChunk]:
    """Parse a Python file with AST and extract functions/classes."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
    except Exception:
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    lines = source.splitlines()
    chunks = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = node.lineno - 1
            end = node.end_lineno
            content = "\n".join(lines[start:end])

            chunk_type = "class" if isinstance(node, ast.ClassDef) else "function"
            chunks.append(CodeChunk(
                content=content,
                filepath=relative_path,
                start_line=node.lineno,
                end_line=node.end_lineno,
                chunk_type=chunk_type,
                name=node.name,
            ))

    # If no functions/classes found, treat whole file as one chunk
    if not chunks and source.strip():
        chunks.append(CodeChunk(
            content=source,
            filepath=relative_path,
            start_line=1,
            end_line=len(lines),
            chunk_type="module",
            name=relative_path,
        ))

    return chunks