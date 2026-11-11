from app.config import USE_NEO4J

def get_neighbourhood(txn: dict) -> dict:
    if not USE_NEO4J:
        return {"mode":"local_demo","shared_device_customers":None,
                "related_transaction_count":None,
                "note":"Neo4j disabled; graph context unavailable in local demo."}
    from neo4j import GraphDatabase
    import os
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"],
        auth=(os.getenv("NEO4J_USER","neo4j"), os.environ["NEO4J_PASSWORD"]))
    query = """
    MATCH (c:Customer {customer_id:$customer_id})
    OPTIONAL MATCH (c)-[:USED_DEVICE]->(d:Device)
    WITH c, collect(DISTINCT d) AS devices
    UNWIND CASE WHEN size(devices)=0 THEN [null] ELSE devices END AS d
    OPTIONAL MATCH (other:Customer)-[:USED_DEVICE]->(d)
    WITH count(DISTINCT other) AS linked_customers
    RETURN linked_customers
    """
    try:
        with driver.session(database=os.getenv("NEO4J_DATABASE","neo4j")) as session:
            rec=session.run(query,customer_id=txn.get("customer_id")).single()
            count=rec["linked_customers"] if rec else 0
        return {"mode":"neo4j","shared_device_customers":count,
                "related_transaction_count":None}
    finally:
        driver.close()
