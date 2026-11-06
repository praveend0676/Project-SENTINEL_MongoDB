
import os
import csv

from qdrant_client import QdrantClient, models
from qdrant_client.models import PayloadSchemaType

from src.config import *
from src.documents import load_docs, make_chunks
from src.embeddings import make_embedding_client, embed_many


def ensure_collection_and_indexes(qdrant):
    """Create collection if missing and ensure payload indexes exist."""

    collections = qdrant.get_collections()
    print("Qdrant connection successful:", collections)

    collection_names = [
        item.name for item in collections.collections
    ]

    if COLLECTION not in collection_names:
        print(f"Creating collection: {COLLECTION}")

        qdrant.create_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=VECTOR_DIMENSIONS,
                distance=models.Distance.COSINE
            )
        )
    else:
        print(f"Using existing collection: {COLLECTION}")

    # Create keyword index for payload filtering.
    qdrant.create_payload_index(
        collection_name=COLLECTION,
        field_name="document_type",
        field_schema=PayloadSchemaType.KEYWORD,
        wait=True
    )

    print("Payload index ready: document_type")


def main():

    if not all([EURI_API_KEY, QDRANT_URL, QDRANT_API_KEY]):
        raise SystemExit(
            "Please configure EURI_API_KEY, QDRANT_URL "
            "and QDRANT_API_KEY in your .env file."
        )

    # Step 1: Load documents
    docs = load_docs()

    print("Total unique documents:", len(docs))

    if len(docs) < MIN_DOCS:
        raise SystemExit(
            f"Minimum {MIN_DOCS} documents required. "
            f"Found only {len(docs)}."
        )

    # Step 2: Create chunks
    chunks = make_chunks(docs)

    if not chunks:
        raise SystemExit("No chunks generated.")

    print("Total chunks generated:", len(chunks))

    os.makedirs(OUT, exist_ok=True)

    # Step 3: Save document inventory
    with open(
        os.path.join(OUT, "document_inventory.csv"),
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "source_document",
                "document_type"
            ]
        )

        writer.writeheader()

        for doc in docs:
            writer.writerow({
                "source_document": doc["source_document"],
                "document_type": doc["document_type"]
            })

    # Step 4: Save chunk inventory
    with open(
        os.path.join(OUT, "chunk_inventory.csv"),
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "source_document",
                "document_type",
                "chunk_number",
                "text"
            ]
        )

        writer.writeheader()
        writer.writerows(chunks)

    # Step 5: Connect to Qdrant
    qdrant = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        timeout=60
    )

    # Step 6: Ensure collection and index
    ensure_collection_and_indexes(qdrant)

    # Step 7: Generate EURI embeddings
    print("Generating embeddings through EURI...")

    embedding_client = make_embedding_client()

    vectors = embed_many(
        embedding_client,
        [chunk["text"] for chunk in chunks]
    )

    if len(vectors) != len(chunks):
        raise SystemExit(
            "Embedding count does not match chunk count."
        )

    # Step 8: Prepare Qdrant points
    points = []

    for index, (chunk, vector) in enumerate(
        zip(chunks, vectors)
    ):

        points.append(
            models.PointStruct(
                id=index + 1,
                vector=vector,
                payload={
                    "source_document": chunk["source_document"],
                    "document_type": chunk["document_type"],
                    "chunk_number": chunk["chunk_number"],
                    "text": chunk["text"]
                }
            )
        )

    # Step 9: Upload in batches
    batch_size = 64

    for start in range(0, len(points), batch_size):

        batch = points[start:start + batch_size]

        qdrant.upsert(
            collection_name=COLLECTION,
            points=batch,
            wait=True
        )

        print(
            f"Uploaded {start + 1} to "
            f"{start + len(batch)} of {len(points)}"
        )

    print("\n================================")
    print("SENTINEL INGESTION COMPLETED")
    print("================================")
    print("Documents:", len(docs))
    print("Chunks:", len(chunks))
    print("Qdrant collection:", COLLECTION)
    print("Payload index: document_type")
    print("================================")


if __name__ == "__main__":
    main()
