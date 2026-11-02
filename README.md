# Project SENTINEL — MongoDB with Python (Building Blocks)

## Objective
Model a portion of Project SENTINEL transaction data as MongoDB documents in Atlas, access it with PyMongo, and demonstrate CRUD, indexes, explain plans, and aggregations.

> **Recording/prep runbook:** see `YOUTUBE_EXECUTION_GUIDE.md` for the full execution flow, expected outputs, YouTube chapter plan, and troubleshooting.

> **Source-data integrity:** This repository does not contain fabricated SENTINEL transactions. Use the actual output/data from Project Work 4 and 5. The schema mapper includes common field-name alternatives, but you must confirm actual column names against your source. The supplied `sql/create_table.sql` is only an optional example; do not run it over an existing schema without checking first.

## 1. Document model and embed/reference decision

### `customers`
```json
{
  "customer_id": "<source customer id>",
  "devices": ["<device id 1>", "<device id 2>"],
  "updated_at": "<UTC datetime>"
}
```
Customer device IDs are **embedded** as a small, deduplicated array because the assignment asks for customer documents with devices embedded or referenced and device history is commonly read with a customer. If a customer's device history can grow without bound, move devices to a separate collection instead.

### `transactions`
```json
{
  "transaction_id": "<source transaction id>",
  "customer_id": "<source customer id>",
  "merchant_id": "<source merchant id>",
  "merchant_category": "<category>",
  "device_id": "<device id or null>",
  "transaction_time": "<UTC datetime>",
  "transaction_amount": 123.45,
  "fraud_label": 0,
  "currency": "INR",
  "source": "sentinel_project_work_4_5"
}
```
Transactions reference customers through `customer_id` instead of embedding the full customer document in every transaction. This avoids duplicating customer attributes across many transaction records and allows a customer to be updated independently. Merchant/device details are represented by identifiers and category fields in this learning slice; a separate `merchants` or `devices` collection can be added if richer shared metadata is needed.

## 2. Create Atlas and configure access
1. Create a free MongoDB Atlas account and free cluster.
2. Create a database user with read/write privileges for the target database.
3. Add your current IP address to Atlas Network Access. Avoid `0.0.0.0/0` except for a short, controlled test; never expose production data that way.
4. Choose **Connect → Drivers → Python**, copy the URI, and put it in `.env` as `MONGODB_URI`.
5. Copy `.env.example` to `.env` only if `.env` does not already exist; otherwise edit the existing `.env`. The code reads `MONGODB_URI` (not `MONGO_URI`). Do not commit `.env` or credentials.

## 3. Install and configure
Windows PowerShell, from this folder:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```
Edit `.env` before connecting. If PowerShell blocks activation, use the interpreter at `.venv\Scripts\python.exe` directly or follow your organization's policy; don't weaken system policy just for this project.

## 4. Load at least 5,000 real source transactions
Choose **one** supported source:

### Option A — CSV export of Project Work 4/5 data
Export your actual transaction rows to `data/transactions.csv`. Required semantic fields are transaction ID, customer ID, timestamp, and amount. Common accepted names are listed in `src/schema.py`. Add/map any actual class field names there if different.
```powershell
python ingest.py all --source csv
```

### Option B — Supabase table from Project Work 4/5
Set `SUPABASE_URL`, `SUPABASE_KEY`, and the actual `SUPABASE_TABLE` in `.env`. The key must have read access; prefer a restricted read-only key where supported. Confirm actual field names and table name from your Project Work 4/5 work before running:
```powershell
python ingest.py all --source supabase
```
The loader pages through Supabase results and upserts by `transaction_id`. It prints processed/rejected rows and total MongoDB count. The target collection must contain at least 5,000 source records for the assignment. If fewer are loaded, inspect the mapping, source row count, and rejected-row count. Do not claim the 5,000-row criterion is met until the printed count verifies it.

### Source field mapping
`src/schema.py` maps common variants such as `transaction_amount`/`amount`, `transaction_time`/`created_at`, and `fraud_label`/`is_fraud`. **Check the real source schema first**; change this mapping for your actual Project Work 4/5 fields. Rows without transaction ID, customer ID, parseable time, or numeric amount are rejected and counted.

> **Configured Supabase source:** `public.transactions` currently contains **110,000** rows with `transaction_id`, `customer_id`, `merchant_id`, `device_id`, `transaction_amount`, `merchant_category`, `transaction_time`, and other enrichment columns. It does **not** contain a `fraud_label` column, so real source rows are ingested with `fraud_label: null`. The fraud-rate pipeline therefore only produces rates for the labelled demo rows; this is stated in the `operations.py` output.

## 5. CRUD, queries, indexes and aggregations
Run:
```powershell
python operations.py
```
It demonstrates:
- `insert_one` on a dedicated demo row (duplicate-key is handled on reruns)
- `insert_many` on two dedicated demo rows (duplicate-key errors are handled on reruns)
- `find` with filter and projection
- `update_many` only on `source: demo_only` rows
- `delete_one` only on the dedicated demo row
- fraud rate per `merchant_category` (only labels 0/1 contribute to the denominator)
- top 10 customers by sum of transaction amount in the last 24 hours
- an `explain()` plan before the new indexes are created

To create the requested indexes and capture the post-index explain plan:
```powershell
python create_indexes.py
```
This creates indexes on `customer_id` and descending `transaction_time`, then prints the winning query plan. For a valid before/after comparison, run `operations.py` before `create_indexes.py`, then `create_indexes.py`. If the collection is tiny or the query returns a large fraction of documents, the optimizer may still choose a collection scan; record the actual plan rather than promising an index scan.

## 6. Notebook option
In VS Code, select your `.venv` interpreter/kernel. In a notebook cell run:
```python
%pip install -r requirements.txt
```
Then use:
```python
from src.db import get_database
client, db = get_database()
print(db.command("ping"))
client.close()
```

## 7. Acceptance checklist
- [ ] Atlas cluster, database user, and IP access rule configured.
- [ ] Python connects using `MongoClient`/PyMongo.
- [ ] `customers` and `transactions` collections exist.
- [ ] At least 5,000 actual Project Work 4/5 transactions loaded (verify count).
- [ ] README explains embedded devices and referenced customers.
- [ ] Demonstrated insert_one, insert_many, filtered/projection find, update_many, delete_one.
- [ ] Indexes on `customer_id` and `transaction_time` created.
- [ ] Before/after `explain()` output captured and discussed.
- [ ] Both aggregation pipelines executed and results captured.
- [ ] Credentials excluded from source control and screenshots.

## 8. Limitations and notes
- This code cannot infer undocumented table names or field names. Confirm them from the existing Supabase/API assignment before ingestion.
- Fraud rate is `fraud_count / labelled_transaction_count` per category; unlabelled records are excluded.
- “Last 24 hours” uses UTC-aware Python datetimes. Ensure `transaction_time` is stored as a BSON datetime (not a string) for correct range filtering. Because the Supabase data is historical, `operations.py` also prints the same top-10 pipeline anchored to the latest 24 hours present in the dataset.
- Use a non-production/test database while demonstrating `update_many` and `delete_one`.
