import chromadb
from chromadb.config import Settings


def get_chroma_client() -> chromadb.Client:
    """Get a persistent Chroma client stored locally."""
    return chromadb.PersistentClient(
        path="./chroma_data",
        settings=Settings(anonymized_telemetry=False),
    )


def get_or_create_collection(org: str, repo: str):
    """
    Each repo gets its own Chroma collection.
    Collection names must be alphanumeric + hyphens only.
    """
    client = get_chroma_client()
    collection_name = f"{org}-{repo}".lower().replace("_", "-")[:63]
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"org": org, "repo": repo},
    )


def upsert_chunks(collection, chunks: list[dict]) -> None:
    """
    Upsert a list of chunk dicts into the collection.
    Each dict must have: id, embedding, content, metadata.
    """
    collection.upsert(
        ids=[c["id"] for c in chunks],
        embeddings=[c["embedding"] for c in chunks],
        documents=[c["content"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks],
    )


def query_similar(collection, query_vector: list[float], k: int = 5) -> list[dict]:
    """
    Find the k most similar chunks to a query vector.
    Returns list of dicts with content and metadata.
    """
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=k,
    )
    chunks = []
    for i, doc in enumerate(results["documents"][0]):
        chunks.append({
            "content": doc,
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })
    return chunks