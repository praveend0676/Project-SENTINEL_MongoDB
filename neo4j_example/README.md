# Project SENTINEL – Neo4j Graph Database with Python

## Graph model
- `(:Customer {customer_id})`
- `(:Device {device_id})`
- `(:Merchant {merchant_id})`
- `(Customer)-[:USED_DEVICE {first_seen, last_seen}]->(Device)`
- `(Customer)-[:PAID {transaction_id, amount, time, fraud_label, device_id, merchant_category, currency}]->(Merchant)`

Each payment is a separate relationship keyed by `transaction_id`. The loader uses `MERGE` for repeatable loads.

## 1. Start Neo4j
```powershell
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/Password12345 -v neo4j_data:/data neo4j:5
```
If the container already exists, use `docker start neo4j`.
Browser: http://localhost:7474/browser/ | Bolt: bolt://localhost:7687
Username: `neo4j`; password: the password set when the container was created.

## 2. Install dependencies
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```
Copy `.env.example` to `.env`, set your password, and never commit `.env`.

## 3. Dataset
Put `transactions.csv` in `data/transactions.csv`. Required columns:
`transaction_id, customer_id, merchant_id, device_id, transaction_time, transaction_amount, fraud_label, merchant_category`

The supplied learning CSV is synthetic. If your instructor requires actual Project Work 4/5 or class API data, replace it with authorized source data using these column names.

## 4. Run
```bash
python test_connection.py
python create_schema.py
python load_data.py
python run_queries.py
```

## 5. Required investigations
See `src/queries.py` for:
1. Devices shared by 3+ distinct customers in the last 7 days.
2. Customers within two relationship hops (Customer → Device → Customer) of a customer with a fraud-labelled payment.
3. Merchants most frequently paid through devices shared by 3+ customers in the last 7 days.

## 6. Capture graph screenshot
Run in Neo4j Browser:
```cypher
MATCH (c:Customer)-[u:USED_DEVICE]->(d:Device)<-[:USED_DEVICE]-(other:Customer)
MATCH (c)-[p:PAID]->(m:Merchant)
WHERE u.last_seen >= datetime() - duration('P7D')
  AND p.fraud_label = 1
  AND c.customer_id <> other.customer_id
RETURN c, u, d, other, p, m
LIMIT 100
```
Select Graph view and capture the cluster. If no records appear, inspect shared-device results; do not fabricate findings.

## Interpretation
A shared device is an investigation lead, not proof of fraud. Family, workplace and kiosk devices may be legitimate. Validate timing, merchant concentration and other evidence.

## Submission checklist
- [ ] Public GitHub repository with code and README.
- [ ] Screenshots: connection, load summary, query outputs, graph view.
- [ ] `.env` and credentials excluded.
- [ ] 5–10 minute video with face or voice, showing the problem, code and live run.
- [ ] Submit GitHub and YouTube links in the assignment fields.

## Troubleshooting
- Container already exists: `docker start neo4j`.
- Inspect: `docker ps`; logs: `docker logs neo4j`.
- Password errors: use the password set at container creation; editing `.env` does not change the existing Neo4j password.
- Empty 7-day results: inspect transaction timestamps and confirm the data load.
