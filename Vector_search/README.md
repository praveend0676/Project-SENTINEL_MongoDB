# Project SENTINEL — Semantic Search with Gemini Embedding 2 and Qdrant Cloud

## Governance warning — read first
The SENTINEL Client Requirement Document says data, prompts and model artifacts must stay inside PayVista AWS and third-party hosted AI APIs are out of scope. Gemini API and Qdrant Cloud are external services. For this learning exercise, use only public RBI/NPCI material or synthetic/de-identified documents, and obtain instructor/data-owner approval. Do NOT upload investigator notes, chargeback narratives, customer-linked data, confidential playbooks or any PayVista confidential material to external services without written authorization and approved privacy/security review. The included regex masking is only basic hygiene, not production-grade PII redaction.

## What it does
Reads local PDF/DOCX/TXT/MD documents, cleans and deduplicates them, chunks text, embeds each chunk using `gemini-embedding-2` at 3,072 dimensions, creates a cosine collection in Qdrant Cloud, runs `get_collections()` as a health check, upserts payloads and runs ten semantic searches (top five results each). Search 10 uses a payload filter for RBI/NPCI documents.

## Corpus and minimum
Put at least 200 genuine, unique, readable documents under:
- `corpus/rbi_npci/`
- `corpus/playbooks/`
- `corpus/investigator_notes/`
- `corpus/chargeback_narratives/`

Supported: PDF, DOCX, TXT, MD. The code stops if it finds fewer than 200 unique documents. It does not fabricate documents.

## Chunking choice
Chunk size: 3,000 characters (roughly 750 tokens using an approximate 4 characters/token conversion). Overlap: 400 characters (roughly 100 tokens). This keeps each passage focused on one rule/procedure while retaining enough adjacent context to avoid cutting off definitions or exceptions. Actual token counts vary; chunks remain comfortably below Gemini Embedding 2's 8,192-token input limit.

## Create services
1. Create a free Qdrant Cloud cluster. Copy its HTTPS cluster URL and API key.
2. Create a Gemini API key in Google AI Studio.
3. Keep both credentials private.

## Windows / VS Code setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```
Edit `.env` with GEMINI_API_KEY, QDRANT_URL and QDRANT_API_KEY.

## Run ingestion
Add approved documents to corpus folders, then:
```powershell
python -m src.ingest
```
This prints the unique document count, chunk count, Qdrant health check, collection creation and upsert count. Payload fields: source_document, document_type, chunk_number and text.

## Run semantic searches
```powershell
python -m src.search
```
Prints top 5 passages and cosine similarity scores for 10 natural-language queries. The tenth query is filtered to `document_type=rbi_npci_guideline`. Saves `outputs/search_results.csv`.

## Assignment evidence
Capture: Qdrant cluster, get_collections output, unique document count (>=200), chunk size/overlap explanation, model name and 3072 dimensions, collection vector size/distance, upsert count, ten searches with top-five scores, filtered search, and CSV output inventories.

A cosine score is similarity, not a probability or fraud score. Re-running this starter with a changed corpus may require deleting/recreating the collection because point IDs are sequential.


## Updated: EURI gateway with OpenAI Python SDK
The project now calls the EURI OpenAI-compatible embeddings endpoint using the OpenAI SDK:
- Base URL: `https://api.euron.one/api/v1/euri`
- Model: `gemini-embedding-2-preview`
- Dimensions: `3072`
- Python package: `openai`

Configure `EURI_API_KEY`, `EURI_BASE_URL`, `EURI_EMBEDDING_MODEL`, and `EMBEDDING_DIMENSIONS` in `.env`. The gateway's current documentation lists `gemini-embedding-2-preview` as a premium embedding model; check that your EURI account has access and sufficient wallet balance before embedding the full corpus.

Test the EURI connection before ingestion:
```powershell
python -m src.test_euri
```
Then run:
```powershell
python -m src.ingest
python -m src.search
```
