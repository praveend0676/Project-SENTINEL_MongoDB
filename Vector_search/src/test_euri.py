from src.config import EURI_BASE_URL, EMBEDDING_MODEL, VECTOR_DIMENSIONS
from src.embeddings import make_embedding_client, embed_text

def main():
    print("EURI base URL:", EURI_BASE_URL)
    print("Embedding model:", EMBEDDING_MODEL)
    client = make_embedding_client()
    vector = embed_text(client, "SENTINEL semantic search connection test.")
    print("EURI embedding connection successful.")
    print("Vector dimensions:", len(vector))

if __name__ == "__main__":
    main()
