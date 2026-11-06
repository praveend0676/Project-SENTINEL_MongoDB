
from qdrant_client import QdrantClient
from src.config import QDRANT_URL, QDRANT_API_KEY, COLLECTION


def main():

    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        timeout=60
    )

    # 1. Retrieve collection information
    info = client.get_collection(COLLECTION)

    print("\n================================")
    print("SENTINEL QDRANT COLLECTION")
    print("================================")

    print("Collection:", COLLECTION)
    print("Points count:", info.points_count)
    print("Status:", info.status)

    # Vector configuration
    vector_config = info.config.params.vectors

    print("\n===== VECTOR CONFIGURATION =====")

    if isinstance(vector_config, dict):
        for name, config in vector_config.items():
            print("Vector name:", name)
            print("Vector size:", config.size)
            print("Distance:", config.distance)
    else:
        print("Vector size:", vector_config.size)
        print("Distance:", vector_config.distance)

    # 2. Retrieve sample records
    print("\n===== SAMPLE DOCUMENT RECORDS =====")

    records, next_offset = client.scroll(
        collection_name=COLLECTION,
        limit=5,
        with_payload=True,
        with_vectors=False
    )

    for record in records:

        payload = record.payload or {}

        print("\nPoint ID:", record.id)
        print(
            "Source:",
            payload.get("source_document")
        )
        print(
            "Document type:",
            payload.get("document_type")
        )
        print(
            "Chunk number:",
            payload.get("chunk_number")
        )
        print(
            "Text:",
            (payload.get("text") or "")[:300]
        )

    # 3. Retrieve payload index information
    print("\n===== PAYLOAD INDEXES =====")

    if info.payload_schema:

        for field, schema in info.payload_schema.items():
            print(f"{field}: {schema}")

    else:
        print("No payload indexes found.")

    # 4. Count records by document type
    print("\n===== DOCUMENT TYPE DISTRIBUTION =====")

    from collections import Counter

    counts = Counter()
    offset = None

    while True:

        records, offset = client.scroll(
            collection_name=COLLECTION,
            limit=100,
            offset=offset,
            with_payload=["document_type"],
            with_vectors=False
        )

        for record in records:
            payload = record.payload or {}
            category = payload.get(
                "document_type",
                "unknown"
            )
            counts[category] += 1

        if offset is None:
            break

    for category, count in sorted(counts.items()):
        print(f"{category}: {count}")

    print("Total points:", sum(counts.values()))

    print("\n================================")
    print("QDRANT VERIFICATION COMPLETED")
    print("================================")


if __name__ == "__main__":
    main()
