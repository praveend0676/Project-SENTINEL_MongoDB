"""
Project SENTINEL — Vector Database Search Lab

Uses the REAL Gemini Embedding 2 vectors already stored in the Qdrant Cloud
collection `sentinel_knowledge`. It does not silently generate substitute data.

Configuration is read from .env:
  QDRANT_URL, QDRANT_API_KEY, EURI_API_KEY
Optional:
  QDRANT_COLLECTION=sentinel_knowledge
  EMBEDDING_MODEL=gemini-embedding-2-preview
  EMBEDDING_BASE_URL=https://api.euron.one/api/v1/euri
  VECTOR_NAME=                 # leave blank for unnamed/default Qdrant vectors
  QUERY_TEXT=What steps should be followed for failed authentication?
"""
from __future__ import annotations

import os
import statistics
import time
from typing import Any

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient, models


load_dotenv()

COLLECTION = os.getenv("QDRANT_COLLECTION", "sentinel_knowledge")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-2-preview")
EMBEDDING_BASE_URL = os.getenv(
    "EMBEDDING_BASE_URL", "https://api.euron.one/api/v1/euri"
)
VECTOR_NAME = os.getenv("VECTOR_NAME", "").strip() or None
QUERY_TEXT = os.getenv(
    "QUERY_TEXT", "What steps should be followed for failed authentication?"
)
TOP_K = 5
BENCHMARK_SIZES = (1_000, 10_000)


def hand_calculation_demo() -> None:
    print("\n" + "=" * 76)
    print("1) HAND-CALCULATED 2D EXAMPLE")
    print("=" * 76)

    points = np.array([[2.0, 3.0], [1.0, 2.0], [0.0, 4.0]])
    labels = ["(2, 3)", "(1, 2)", "(0, 4)"]
    query = np.array([2.0, 4.0])

    distances = np.linalg.norm(points - query, axis=1)
    cosine = (points @ query) / (
        np.linalg.norm(points, axis=1) * np.linalg.norm(query)
    )

    print(f"Query: {tuple(query.astype(int))}\n")
    print(f"{'Point':<12}{'Euclidean distance':>22}{'Cosine similarity':>22}")
    for label, distance, similarity in zip(labels, distances, cosine):
        print(f"{label:<12}{distance:>22.6f}{similarity:>22.6f}")

    print("\nEuclidean ranking (ascending distance):")
    for rank, idx in enumerate(np.argsort(distances), 1):
        print(f"  {rank}. {labels[idx]}  distance={distances[idx]:.6f}")

    print("\nCosine ranking (descending similarity):")
    for rank, idx in enumerate(np.argsort(-cosine), 1):
        print(f"  {rank}. {labels[idx]}  similarity={cosine[idx]:.6f}")


def make_embedding_client() -> OpenAI:
    api_key = os.getenv("EURI_API_KEY")
    if not api_key:
        raise RuntimeError("EURI_API_KEY is missing. Add it to your local .env file.")
    return OpenAI(api_key=api_key, base_url=EMBEDDING_BASE_URL)


def embed_query(text: str) -> np.ndarray:
    client = make_embedding_client()
    result = client.embeddings.create(model=EMBEDDING_MODEL, input=[text])
    return np.asarray(result.data[0].embedding, dtype=np.float32)


def make_qdrant_cloud_client() -> QdrantClient:
    url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")
    if not url or not api_key:
        raise RuntimeError(
            "QDRANT_URL and QDRANT_API_KEY are missing. Add them to your local .env file."
        )
    return QdrantClient(url=url, api_key=api_key, timeout=60)


def extract_vector(record: Any) -> list[float]:
    raw = record.vector
    if isinstance(raw, dict):
        if VECTOR_NAME:
            raw = raw.get(VECTOR_NAME)
        elif len(raw) == 1:
            raw = next(iter(raw.values()))
        else:
            raise RuntimeError(
                "Collection has multiple named vectors. Set VECTOR_NAME in .env."
            )
    if raw is None:
        raise RuntimeError(
            "A Qdrant point has no returned vector. Check collection vector settings."
        )
    return raw


def load_task4_vectors(
    client: QdrantClient,
) -> tuple[np.ndarray, list[int | str], list[dict[str, Any]]]:
    """Read the stored Task 4 Gemini vectors from sentinel_knowledge."""
    info = client.get_collection(COLLECTION)
    print(f"\nConnected to Qdrant collection: {COLLECTION}")
    print("Collection status:", info.status)
    print("Configured distance:", info.config.params.vectors)

    all_vectors: list[list[float]] = []
    point_ids: list[int | str] = []
    payloads: list[dict[str, Any]] = []
    offset = None

    while True:
        records, next_offset = client.scroll(
            collection_name=COLLECTION,
            limit=256,
            offset=offset,
            with_payload=True,
            with_vectors=True,
        )
        for record in records:
            all_vectors.append(extract_vector(record))
            point_ids.append(record.id)
            payloads.append(record.payload or {})
        if next_offset is None:
            break
        offset = next_offset

    if not all_vectors:
        raise RuntimeError(f"No vectors were found in Qdrant collection '{COLLECTION}'.")

    vectors = np.asarray(all_vectors, dtype=np.float32)
    if vectors.ndim != 2:
        raise RuntimeError(f"Expected a 2D embedding matrix; got shape {vectors.shape}.")
    if not np.isfinite(vectors).all():
        raise RuntimeError("The stored vector set contains NaN or infinite values.")

    print(f"Loaded {len(vectors):,} Task 4 vectors; dimension={vectors.shape[1]:,}")
    print("First payload fields:", sorted(payloads[0].keys())[:12])
    return vectors, point_ids, payloads


def top_k_indices(scores: np.ndarray, k: int, largest: bool) -> np.ndarray:
    k = min(k, scores.size)
    if largest:
        candidates = np.argpartition(-scores, k - 1)[:k]
        return candidates[np.argsort(-scores[candidates])]
    candidates = np.argpartition(scores, k - 1)[:k]
    return candidates[np.argsort(scores[candidates])]


def numpy_search(
    vectors: np.ndarray, query: np.ndarray, k: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    distances = np.linalg.norm(vectors - query, axis=1)
    cosine_scores = (vectors @ query) / (
        np.linalg.norm(vectors, axis=1) * np.linalg.norm(query) + 1e-12
    )
    euclidean_ids = top_k_indices(distances, k, largest=False)
    cosine_ids = top_k_indices(cosine_scores, k, largest=True)
    return (
        euclidean_ids,
        distances[euclidean_ids],
        cosine_ids,
        cosine_scores[cosine_ids],
    )


def qdrant_local_exact(
    vectors: np.ndarray, query: np.ndarray, k: int, distance: models.Distance
) -> tuple[list[int], list[float]]:
    """Exact Qdrant search over the same Task 4 vectors, in local memory."""
    client = QdrantClient(":memory:")
    name = "task4_exact_validation"
    client.create_collection(
        collection_name=name,
        vectors_config=models.VectorParams(
            size=vectors.shape[1], distance=distance
        ),
    )

    batch_size = 256
    for start in range(0, len(vectors), batch_size):
        batch = vectors[start : start + batch_size]
        client.upsert(
            collection_name=name,
            points=[
                models.PointStruct(id=start + j, vector=row.tolist())
                for j, row in enumerate(batch)
            ],
            wait=True,
        )

    result = client.query_points(
        collection_name=name,
        query=query.tolist(),
        limit=min(k, len(vectors)),
        search_params=models.SearchParams(exact=True),
        with_payload=False,
    )
    ids = [int(point.id) for point in result.points]
    scores = [float(point.score) for point in result.points]
    client.close()
    return ids, scores


def validate_task4_vectors(
    vectors: np.ndarray,
    original_ids: list[int | str],
    query: np.ndarray,
) -> None:
    print("\n" + "=" * 76)
    print("2–3) NUMPY BRUTE FORCE VS QDRANT — TASK 4 GEMINI VECTORS")
    print("=" * 76)

    if query.shape[0] != vectors.shape[1]:
        raise RuntimeError(
            f"Query dimension {query.shape[0]} does not match stored vector "
            f"dimension {vectors.shape[1]}. Confirm the embedding model and collection."
        )

    k = min(TOP_K, len(vectors))
    eu_ids, eu_distances, cos_ids, cos_scores = numpy_search(vectors, query, k)

    q_eu_ids, q_eu_scores = qdrant_local_exact(
        vectors, query, k, models.Distance.EUCLID
    )
    q_cos_ids, q_cos_scores = qdrant_local_exact(
        vectors, query, k, models.Distance.COSINE
    )

    eu_match = eu_ids.tolist() == q_eu_ids
    cos_match = cos_ids.tolist() == q_cos_ids

    print("\nEuclidean ranking:")
    for rank, (idx, score) in enumerate(zip(eu_ids, eu_distances), 1):
        print(f"  {rank}. Qdrant point ID={original_ids[int(idx)]} distance={score:.6f}")
    print("Qdrant local exact IDs:", [original_ids[i] for i in q_eu_ids])
    print("Ordered ranking matches:", eu_match)

    print("\nCosine ranking:")
    for rank, (idx, score) in enumerate(zip(cos_ids, cos_scores), 1):
        print(f"  {rank}. Qdrant point ID={original_ids[int(idx)]} similarity={score:.6f}")
    print("Qdrant local exact IDs:", [original_ids[i] for i in q_cos_ids])
    print("Ordered ranking matches:", cos_match)

    print("\nQdrant Euclidean distances:", np.round(q_eu_scores, 6).tolist())
    print("Qdrant cosine similarities:", np.round(q_cos_scores, 6).tolist())

    if not eu_match or not cos_match:
        raise AssertionError(
            "NumPy and Qdrant rankings differ. Check metric conventions, "
            "vector precision, and whether the same query/vector set was used."
        )
    print("\nPASS: NumPy and Qdrant exact rankings match on the Task 4 vectors.")


def normalized_dot_product_demo(vectors: np.ndarray, query: np.ndarray) -> None:
    print("\n" + "=" * 76)
    print("4) WHY NORMALIZED COSINE AND DOT PRODUCT HAVE THE SAME RANKING")
    print("=" * 76)

    normalized_vectors = vectors / np.maximum(
        np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12
    )
    normalized_query = query / max(float(np.linalg.norm(query)), 1e-12)

    normalized_dot_scores = normalized_vectors @ normalized_query
    cosine_scores = (vectors @ query) / (
        np.linalg.norm(vectors, axis=1) * np.linalg.norm(query) + 1e-12
    )

    cosine_ids = top_k_indices(cosine_scores, TOP_K, largest=True)
    dot_ids = top_k_indices(normalized_dot_scores, TOP_K, largest=True)

    print("Cosine top-k row indexes:       ", cosine_ids.tolist())
    print("Normalized dot-product indexes:", dot_ids.tolist())
    print("Same ordered ranking:", np.array_equal(cosine_ids, dot_ids))
    print(
        "Maximum score difference:",
        float(np.max(np.abs(cosine_scores - normalized_dot_scores))),
    )


def build_local_collection(
    vectors: np.ndarray, distance: models.Distance
) -> tuple[QdrantClient, str]:
    client = QdrantClient(":memory:")
    name = "benchmark"
    client.create_collection(
        collection_name=name,
        vectors_config=models.VectorParams(size=vectors.shape[1], distance=distance),
    )
    for start in range(0, len(vectors), 256):
        batch = vectors[start : start + 256]
        client.upsert(
            collection_name=name,
            points=[
                models.PointStruct(id=start + j, vector=row.tolist())
                for j, row in enumerate(batch)
            ],
            wait=True,
        )
    return client, name


def qdrant_query_ms(
    client: QdrantClient, collection: str, query: np.ndarray, k: int
) -> float:
    # Warm-up then median of five exact queries; collection build is excluded.
    kwargs = dict(
        collection_name=collection,
        query=query.tolist(),
        limit=k,
        search_params=models.SearchParams(exact=True),
        with_payload=False,
    )
    client.query_points(**kwargs)
    timings = []
    for _ in range(5):
        start = time.perf_counter()
        client.query_points(**kwargs)
        timings.append((time.perf_counter() - start) * 1000)
    return statistics.median(timings)


def numpy_query_ms(vectors: np.ndarray, query: np.ndarray, k: int) -> float:
    timings = []
    for _ in range(5):
        start = time.perf_counter()
        numpy_search(vectors, query, k)
        timings.append((time.perf_counter() - start) * 1000)
    return statistics.median(timings)


def benchmark(vectors: np.ndarray, query: np.ndarray) -> None:
    print("\n" + "=" * 76)
    print("5) NUMPY VS QDRANT EXACT-SEARCH BENCHMARK — TASK 4 VECTORS")
    print("=" * 76)
    print("Timings are median of 5 queries; Qdrant collection creation/upsert excluded.")
    print(f"{'Count':>9} {'Metric':<12} {'NumPy ms':>12} {'Qdrant ms':>12} {'Status':>12}")

    for count in BENCHMARK_SIZES:
        if len(vectors) < count:
            print(
                f"{count:>9,} {'—':<12} {'—':>12} {'—':>12} {'SKIPPED':>12}"
            )
            print(
                f"  Need {count:,} stored Task 4 vectors; collection currently has "
                f"{len(vectors):,}. No synthetic vectors are substituted."
            )
            continue

        subset = vectors[:count]
        for metric_name, metric in (
            ("Euclidean", models.Distance.EUCLID),
            ("Cosine", models.Distance.COSINE),
        ):
            numpy_ms = numpy_query_ms(subset, query, TOP_K)
            q_client, q_collection = build_local_collection(subset, metric)
            qdrant_ms = qdrant_query_ms(q_client, q_collection, query, TOP_K)
            q_client.close()
            print(
                f"{count:>9,} {metric_name:<12} {numpy_ms:>12.3f} "
                f"{qdrant_ms:>12.3f} {'measured':>12}"
            )

    print(
        "\nInterpretation: this compares exact local query paths on the same stored "
        "Gemini vectors. At small sizes, Python/Qdrant call overhead may dominate."
    )


def main() -> None:
    hand_calculation_demo()

    cloud = make_qdrant_cloud_client()
    try:
        vectors, original_ids, payloads = load_task4_vectors(cloud)
    finally:
        cloud.close()

    query = embed_query(QUERY_TEXT)
    print("\nQuery text:", QUERY_TEXT)
    print("Query embedding model:", EMBEDDING_MODEL)
    print("Query vector dimension:", len(query))

    validate_task4_vectors(vectors, original_ids, query)
    normalized_dot_product_demo(vectors, query)
    benchmark(vectors, query)


if __name__ == "__main__":
    main()
