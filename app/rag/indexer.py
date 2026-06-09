import os
import hashlib
import tempfile
import httpx
from app.rag.chunker import chunk_repository
from app.rag.embeddings import embed_texts
from app.db.vector_store import get_or_create_collection, upsert_chunks


def _chunk_id(filepath: str, start_line: int, name: str) -> str:
    """Generate a stable unique ID for a chunk."""
    raw = f"{filepath}:{start_line}:{name}"
    return hashlib.md5(raw.encode()).hexdigest()


async def index_repository(
    repo_full_name: str,
    token: str,
) -> int:
    """
    Clone a repo, chunk it, embed it, and store in Chroma.
    Returns the number of chunks indexed.
    """
    org, repo = repo_full_name.split("/")
    collection = get_or_create_collection(org, repo)

    # Download repo as a zip (simpler than full git clone)
    zip_url = f"https://api.github.com/repos/{repo_full_name}/zipball"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "repo.zip")

        async with httpx.AsyncClient(follow_redirects=True, timeout=60) as client:
            response = await client.get(zip_url, headers=headers)
            response.raise_for_status()
            with open(zip_path, "wb") as f:
                f.write(response.content)

        # Unzip
        import zipfile
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmpdir)

        # Find the extracted folder (GitHub adds a prefix)
        extracted = [
            d for d in os.listdir(tmpdir)
            if os.path.isdir(os.path.join(tmpdir, d)) and d != "__MACOSX"
        ][0]
        repo_path = os.path.join(tmpdir, extracted)

        # Chunk all Python files
        chunks = chunk_repository(repo_path)
        if not chunks:
            print(f"[indexer] No Python files found in {repo_full_name}")
            return 0

        print(f"[indexer] Found {len(chunks)} chunks in {repo_full_name}")

        # Embed in batches
        texts = [c.content for c in chunks]
        vectors = await embed_texts(texts)

        # Store in Chroma
        chunk_dicts = []
        for chunk, vector in zip(chunks, vectors):
            chunk_dicts.append({
                "id": _chunk_id(chunk.filepath, chunk.start_line, chunk.name),
                "embedding": vector,
                "content": chunk.content,
                "metadata": {
                    "filepath": chunk.filepath,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "chunk_type": chunk.chunk_type,
                    "name": chunk.name,
                    "repo": repo_full_name,
                },
            })

        upsert_chunks(collection, chunk_dicts)
        print(f"[indexer] Indexed {len(chunk_dicts)} chunks for {repo_full_name}")
        return len(chunk_dicts)