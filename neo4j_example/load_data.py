import os
import pandas as pd
from dotenv import load_dotenv
from src.db import get_driver, DATABASE

load_dotenv()
CSV_PATH = os.getenv("CSV_PATH", "data/transactions.csv")
BATCH_SIZE = 500

def write_batch(tx, rows):
    query = """
    UNWIND $rows AS row
    MERGE (c:Customer {customer_id: row.customer_id})
    MERGE (d:Device {device_id: row.device_id})
    MERGE (m:Merchant {merchant_id: row.merchant_id})
    MERGE (c)-[u:USED_DEVICE]->(d)
    ON CREATE SET u.first_seen = datetime(row.transaction_time),
                  u.last_seen = datetime(row.transaction_time)
    ON MATCH SET u.first_seen =
        CASE WHEN datetime(row.transaction_time) < u.first_seen
             THEN datetime(row.transaction_time) ELSE u.first_seen END,
        u.last_seen =
        CASE WHEN datetime(row.transaction_time) > u.last_seen
             THEN datetime(row.transaction_time) ELSE u.last_seen END
    MERGE (c)-[p:PAID {transaction_id: row.transaction_id}]->(m)
    ON CREATE SET p.amount = row.transaction_amount,
                  p.time = datetime(row.transaction_time),
                  p.fraud_label = row.fraud_label,
                  p.device_id = row.device_id,
                  p.merchant_category = row.merchant_category,
                  p.currency = row.currency
    """
    tx.run(query, rows=rows).consume()

def main():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Place transactions.csv at {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    required = ["transaction_id", "customer_id", "merchant_id", "device_id",
                "transaction_time", "transaction_amount", "fraud_label", "merchant_category"]
    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing required columns: {sorted(missing)}")
    df["transaction_time"] = pd.to_datetime(df["transaction_time"], utc=True, errors="coerce")
    if df["transaction_time"].isna().any():
        raise ValueError("Invalid transaction_time value(s) in CSV.")
    df["transaction_time"] = df["transaction_time"].dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    df["transaction_amount"] = pd.to_numeric(df["transaction_amount"], errors="coerce")
    df["fraud_label"] = pd.to_numeric(df["fraud_label"], errors="coerce")
    rows = []
    for row in df.to_dict("records"):
        rows.append({
            "transaction_id": str(row["transaction_id"]),
            "customer_id": str(row["customer_id"]),
            "merchant_id": str(row["merchant_id"]),
            "device_id": str(row["device_id"]),
            "transaction_time": row["transaction_time"],
            "transaction_amount": float(row["transaction_amount"]),
            "fraud_label": int(row["fraud_label"]) if pd.notna(row["fraud_label"]) else None,
            "merchant_category": str(row["merchant_category"]),
            "currency": str(row.get("currency", "INR")) if pd.notna(row.get("currency", "INR")) else "INR"
        })
    driver = get_driver()
    try:
        with driver.session(database=DATABASE) as session:
            for i in range(0, len(rows), BATCH_SIZE):
                session.execute_write(write_batch, rows[i:i+BATCH_SIZE])
                print(f"Loaded {min(i+BATCH_SIZE, len(rows))} / {len(rows)} transactions")
            summary = session.run("""
                MATCH (c:Customer) WITH count(c) AS customers
                MATCH (d:Device) WITH customers, count(d) AS devices
                MATCH (m:Merchant) WITH customers, devices, count(m) AS merchants
                MATCH ()-[p:PAID]->() RETURN customers, devices, merchants, count(p) AS payments
            """).single()
            print("Graph load summary:", dict(summary))
    finally:
        driver.close()

if __name__ == "__main__":
    main()
