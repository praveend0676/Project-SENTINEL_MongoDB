"""Load the synthetic Neo4j transaction sample into a simple customer-device-merchant graph."""
import os, sys
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT/".env")
from neo4j import GraphDatabase
df=pd.read_csv(ROOT/"data/transactions_sentinel_neo4j.csv").fillna("")
driver=GraphDatabase.driver(os.environ["NEO4J_URI"],
    auth=(os.getenv("NEO4J_USER","neo4j"),os.environ["NEO4J_PASSWORD"]))
def load(tx, rows):
    tx.run("CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (n:Customer) REQUIRE n.customer_id IS UNIQUE")
    tx.run("CREATE CONSTRAINT device_id IF NOT EXISTS FOR (n:Device) REQUIRE n.device_id IS UNIQUE")
    tx.run("CREATE CONSTRAINT merchant_id IF NOT EXISTS FOR (n:Merchant) REQUIRE n.merchant_id IS UNIQUE")
    tx.run("CREATE CONSTRAINT transaction_id IF NOT EXISTS FOR (n:Transaction) REQUIRE n.transaction_id IS UNIQUE")
    tx.run("""
    UNWIND $rows AS r
    MERGE (c:Customer {customer_id:r.customer_id})
    MERGE (d:Device {device_id:r.device_id})
    MERGE (m:Merchant {merchant_id:r.merchant_id})
    MERGE (t:Transaction {transaction_id:r.transaction_id})
    SET t.amount=toFloat(r.transaction_amount), t.category=r.merchant_category,
        t.transaction_time=r.transaction_time, t.status=r.transaction_status
    MERGE (c)-[:USED_DEVICE]->(d)
    MERGE (c)-[:MADE_TRANSACTION]->(t)
    MERGE (t)-[:PAID]->(m)
    """,rows=rows)
rows=df.to_dict("records")
with driver.session(database=os.getenv("NEO4J_DATABASE","neo4j")) as session:
    for start in range(0,len(rows),500):
        session.execute_write(load,rows[start:start+500])
driver.close()
print(f"Loaded {len(rows)} synthetic transaction rows into Neo4j.")
