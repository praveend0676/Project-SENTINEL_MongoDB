"""Ingest SENTINEL transactions into MongoDB Atlas.

Usage:
  python ingest.py all --source csv
  python ingest.py all --source supabase

The Supabase source table and column names must be confirmed against Project Work 4/5.
"""
import argparse
import csv
import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import ASCENDING, DESCENDING, UpdateOne
from src.db import get_database
from src.schema import normalize_transaction

load_dotenv()
BASE = Path(__file__).resolve().parent


def read_csv_rows(path):
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}. Export your real Project Work 4/5 transactions to this path.")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        yield from csv.DictReader(f)


def read_supabase_rows():
    from supabase import create_client
    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
    table = os.getenv("SUPABASE_TABLE", "transactions")
    if not url or not key:
        raise RuntimeError("Set SUPABASE_URL and SUPABASE_KEY in .env first.")
    sb = create_client(url, key)
    page_size = int(os.getenv("SUPABASE_PAGE_SIZE", "1000"))
    start = 0
    while True:
        response = (
            sb.table(table)
            .select("*")
            .order("transaction_id")
            .range(start, start + page_size - 1)
            .execute()
        )
        rows = response.data or []
        for row in rows:
            yield row
        if len(rows) < page_size:
            break
        start += page_size


def all_source_rows(source):
    if source == "csv":
        path = Path(os.getenv("TRANSACTIONS_CSV", "data/transactions.csv"))
        if not path.is_absolute():
            path = BASE / path
        return read_csv_rows(path)
    return read_supabase_rows()


def flush_customers(customers, states):
    updates = []
    for cid, state in states.items():
        update = {
            "$setOnInsert": {"customer_id": cid},
            "$set": {"updated_at": state["updated_at"]},
        }
        if state["devices"]:
            update["$addToSet"] = {"devices": {"$each": sorted(state["devices"])}}
        updates.append(UpdateOne({"customer_id": cid}, update, upsert=True))
    if updates:
        customers.bulk_write(updates, ordered=False)


def ingest(source, minimum=5000):
    client, db = get_database()
    tx = db["transactions"]
    customers = db["customers"]
    seen = 0
    rejected = 0
    last_report = 0
    customer_ops = {}
    tx_ops = []
    try:
        for raw in all_source_rows(source):
            doc = normalize_transaction(raw)
            if not doc:
                rejected += 1
                continue
            seen += 1
            cid = doc["customer_id"]
            # Customer device history is embedded as a small, deduplicated array.
            state = customer_ops.setdefault(cid, {"devices": set(), "updated_at": doc["transaction_time"]})
            if doc["transaction_time"] > state["updated_at"]:
                state["updated_at"] = doc["transaction_time"]
            if doc.get("device_id"):
                state["devices"].add(doc["device_id"])
            tx_ops.append(UpdateOne({"transaction_id": doc["transaction_id"]}, {"$set": doc}, upsert=True))
            if len(tx_ops) >= 1000:
                flush_customers(customers, customer_ops)
                tx.bulk_write(tx_ops, ordered=False)
                customer_ops, tx_ops = {}, []
                if seen - last_report >= 10000:
                    print(f"  processed {seen:,} valid rows...")
                    last_report = seen
        if customer_ops:
            flush_customers(customers, customer_ops)
        if tx_ops:
            tx.bulk_write(tx_ops, ordered=False)
        total = tx.count_documents({})
        print(f"Valid source rows processed: {seen}; rejected rows: {rejected}; transactions in MongoDB: {total}")
        if total < minimum:
            print(f"WARNING: assignment requires at least {minimum:,} transactions; only {total:,} currently in the collection.")
        elif seen >= minimum:
            print(f"PASS: at least {minimum:,} transactions are present.")
    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["all"])
    parser.add_argument("--source", choices=["csv", "supabase"], default="csv")
    parser.add_argument("--minimum", type=int, default=5000)
    args = parser.parse_args()
    ingest(args.source, args.minimum)

if __name__ == "__main__":
    main()
