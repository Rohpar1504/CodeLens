import openai
from app.config import settings


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a list of texts using OpenAI.
    Batches automatically to stay within API limits.
    Returns a list of vectors in the same order as input.
    """
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    all_vectors = []
    batch_size = 512

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=batch,
        )
        vectors = [item.embedding for item in response.data]
        all_vectors.extend(vectors)

    return all_vectors