from app.rag.embeddings import embed_texts
from app.db.vector_store import get_or_create_collection, query_similar


async def retrieve_context(
    repo_full_name: str,
    diff_text: str,
    k: int = 5,
) -> list[dict]:
    """
    Given a diff snippet, find the k most similar chunks
    from the repo's indexed codebase.
    """
    org, repo = repo_full_name.split("/")
    collection = get_or_create_collection(org, repo)

    # Embed the diff text as the query
    vectors = await embed_texts([diff_text])
    query_vector = vectors[0]

    # Find similar chunks
    results = query_similar(collection, query_vector, k=k)
    return results


async def retrieve_style_examples(
    repo_full_name: str,
    diff_text: str,
    k: int = 3,
) -> list[dict]:
    """
    Same as retrieve_context but returns fewer, higher-quality
    results specifically for style matching.
    """
    return await retrieve_context(repo_full_name, diff_text, k=k)