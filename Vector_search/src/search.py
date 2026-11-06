
from qdrant_client import QdrantClient, models
from qdrant_client.models import PayloadSchemaType

from src.config import *
from src.embeddings import make_embedding_client, embed_text


QUERIES = [
    "What are the security controls for digital payments?",
    "How should UPI disputes be investigated?",
    "What controls help identify unusual card transactions?",
    "How should investigators review new devices?",
    "How can transaction velocity be monitored?",
    "What steps should be followed for failed authentication?",
    "How should geographic anomalies be investigated?",
    "How should duplicate payment disputes be handled?",
    "What evidence is needed for goods not received disputes?",
    "What RBI and NPCI payment security guidance is relevant?"
]


def ensure_payload_index(qdrant):

    qdrant.create_payload_index(
        collection_name=COLLECTION,
        field_name="document_type",
        field_schema=PayloadSchemaType.KEYWORD,
        wait=True
    )


def main():

    qdrant = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        timeout=60
    )

    print("Connected to Qdrant.")

    ensure_payload_index(qdrant)

    embedding_client = make_embedding_client()

    for index, query in enumerate(QUERIES, start=1):

        print("\n================================")
        print(f"QUERY {index}: {query}")
        print("================================")

        vector = embed_text(
            embedding_client,
            query
        )

        query_filter = None

        # Query 10: Payload-filtered search
        if index == 10:

            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_type",
                        match=models.MatchValue(
                            value="rbi_npci"
                        )
                    )
                ]
            )

            print("Filter: document_type = rbi_npci")

        hits = qdrant.query_points(
            collection_name=COLLECTION,
            query=vector,
            query_filter=query_filter,
            limit=5,
            with_payload=True
        ).points

        if not hits:
            print("No matching documents found.")
            continue

        for rank, hit in enumerate(hits, start=1):

            payload = hit.payload or {}

            print(f"\nRank: {rank}")
            print(f"Score: {hit.score:.4f}")
            print(
                "Source:",
                payload.get("source_document")
            )
            print(
                "Document Type:",
                payload.get("document_type")
            )
            print(
                "Chunk Number:",
                payload.get("chunk_number")
            )
            print(
                "Text:",
                (payload.get("text") or "")[:500]
            )


if __name__ == "__main__":
    main()
