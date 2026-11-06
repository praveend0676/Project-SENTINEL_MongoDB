import time
from openai import OpenAI
from src.config import EURI_API_KEY, EURI_BASE_URL, EMBEDDING_MODEL, VECTOR_DIMENSIONS

def make_embedding_client():
    if not EURI_API_KEY:
        raise RuntimeError("Set EURI_API_KEY in your local .env file.")
    return OpenAI(api_key=EURI_API_KEY, base_url=EURI_BASE_URL)

def embed_text(client, text):
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
        dimensions=VECTOR_DIMENSIONS
    )
    vector = response.data[0].embedding
    if len(vector) != VECTOR_DIMENSIONS:
        raise ValueError(f"Expected {VECTOR_DIMENSIONS} dimensions, received {len(vector)}")
    return vector

def embed_many(client, texts):
    vectors = []
    for i, text in enumerate(texts, start=1):
        for attempt in range(5):
            try:
                vectors.append(embed_text(client, text))
                break
            except Exception:
                if attempt == 4:
                    raise
                time.sleep(2 ** attempt)
        if i % 25 == 0:
            print(f"Embedded {i}/{len(texts)} chunks")
    return vectors
