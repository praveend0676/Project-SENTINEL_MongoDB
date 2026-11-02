from pymongo import ASCENDING, DESCENDING
from src.db import get_database

client, db = get_database()
try:
    tx = db["transactions"]
    print("Creating indexes...")
    print("customer_id index:", tx.create_index([("customer_id", ASCENDING)], name="idx_customer_id"))
    print("transaction_time index:", tx.create_index([("transaction_time", DESCENDING)], name="idx_transaction_time_desc"))
    print("Indexes now:", tx.index_information())
    query = {"customer_id": "DEMO-CUSTOMER"}
    print("EXPLAIN AFTER INDEX:")
    print(tx.find(query).explain().get("queryPlanner", {}).get("winningPlan"))
finally:
    client.close()
