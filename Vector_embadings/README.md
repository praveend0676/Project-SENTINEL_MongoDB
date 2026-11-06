# Vector Database Search Lab — SENTINEL

This project demonstrates what vector search computes, validates NumPy results against Qdrant, and benchmarks exact search at 1,000 and 10,000 vectors.

## What this assignment demonstrates

1. Hand calculation of Euclidean distance and cosine similarity for the classroom 2D example.
2. Brute-force top-k search in NumPy for Euclidean and cosine metrics.
3. Exact Qdrant search and ID/ranking comparison against NumPy.
4. Why cosine similarity and dot product produce the same ranking after L2-normalizing **both** query and stored vectors.
5. Timing comparison for 1,000 and 10,000 vectors, plus an explanation of HNSW.

## Dataset choice

The script creates a reproducible synthetic dataset of 10,000 float32 vectors with a fixed random seed. It uses 3,072 dimensions to mirror the dimensionality of the SENTINEL Gemini Embedding 2 (`gemini-embedding-2-preview`) setup. The first 1,000 vectors are used for the 1,000-vector benchmark.

If Task 4 already produced Gemini vectors, you can replace the synthetic-data function with a loader for that saved NumPy `.npy` file. The search and Qdrant validation code does not depend on how the vectors were generated.

## Project structure

```text
vector_database_objective/
├── README.md
├── requirements.txt
└── src/
    └── vector_search_lab.py
```

## Setup

Python 3.10+ recommended.

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Run

```bash
python src/vector_search_lab.py
```

The program:
- prints every 2D distance and cosine score;
- prints the metric-specific rankings;
- runs NumPy and exact Qdrant top-k searches;
- checks that NumPy and Qdrant return the same ordered IDs;
- checks cosine-vs-dot-product ranking after normalization;
- prints benchmark timings for 1,000 and 10,000 vectors.

Qdrant runs in local in-memory mode, so no Qdrant server or Docker container is required.

## The calculations

For query \(q\) and stored vector \(x\):

**Euclidean distance** (smaller is closer):

\[
d(q,x)=\sqrt{\sum_i(q_i-x_i)^2}
\]

**Cosine similarity** (larger is more similar):

\[
\operatorname{cos}(q,x)=
\frac{q\cdot x}{\|q\|_2\|x\|_2}
\]

The 2D query is \(q=(2,4)\).

| Stored point | Euclidean distance | Cosine similarity |
|---|---:|---:|
| (2, 3) | 1.000000 | 0.992278 |
| (1, 2) | 2.236068 | 1.000000 |
| (0, 4) | 2.000000 | 0.894427 |

Euclidean ranking (ascending distance):
1. (2, 3)
2. (0, 4)
3. (1, 2)

Cosine ranking (descending similarity):
1. (1, 2)
2. (2, 3)
3. (0, 4)

This is the key lesson: different metrics define different notions of “nearest”. The point (1,2) is exactly in the same direction as (2,4), so its cosine similarity is 1, even though it is not the closest point by Euclidean distance.

## Why normalized cosine and dot product have the same ranking

L2 normalization converts each non-zero vector to unit length:

\[
\hat{x}=\frac{x}{\|x\|_2},\qquad
\hat{q}=\frac{q}{\|q\|_2}
\]

Then:

\[
\hat{q}\cdot\hat{x}
=\frac{q\cdot x}{\|q\|_2\|x\|_2}
=\operatorname{cos}(q,x)
\]

The values are equal, not merely similarly ordered. This equivalence requires normalizing **both** sides. Normalizing only the stored vectors or only the query does not generally establish the equality.

## What HNSW changes

Qdrant supports HNSW (Hierarchical Navigable Small World), a graph-based approximate nearest-neighbor index.

- **Brute force / exact search:** compares the query against every vector. It is conceptually simple and returns the exact top-k, but query work grows roughly linearly with the number of vectors and vector dimensions.
- **HNSW:** builds a multi-layer proximity graph during indexing. Search navigates the graph and visits a much smaller candidate set instead of exhaustively scoring every vector.
- **Trade-off:** HNSW usually reduces query latency at scale, but it uses additional memory and index-build time, and approximate search can miss a true nearest neighbor.
- **Recall/latency controls:** graph construction settings such as `m` and `ef_construct`, and query-time `ef`, influence index quality, memory, and search effort.
- **This benchmark:** uses Qdrant `exact=True` to validate the mathematics and compare exact query paths. It does **not** measure the speed advantage of approximate HNSW. The benchmark timings are machine-, library-, and load-dependent; report the values printed by your own run rather than expecting fixed numbers.

For a production evaluation, compare exact search with HNSW on the same dataset and report latency alongside recall@k against the exact results.

## Important interpretation of the benchmark

The Qdrant measurements are local in-memory exact-query timings. They exclude vector generation and collection creation/upsert time, but include the client query call. NumPy timings include scoring and top-k selection. Small datasets can make Python/client overhead dominate, so Qdrant need not be faster at 1,000 or even 10,000 vectors. The point of the benchmark is to measure and explain, not to assume Qdrant must win every test.
