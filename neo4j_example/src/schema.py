def create_schema(driver, database="neo4j"):
    constraints = [
        "CREATE CONSTRAINT customer_id_unique IF NOT EXISTS FOR (n:Customer) REQUIRE n.customer_id IS UNIQUE",
        "CREATE CONSTRAINT device_id_unique IF NOT EXISTS FOR (n:Device) REQUIRE n.device_id IS UNIQUE",
        "CREATE CONSTRAINT merchant_id_unique IF NOT EXISTS FOR (n:Merchant) REQUIRE n.merchant_id IS UNIQUE",
    ]
    with driver.session(database=database) as session:
        for query in constraints:
            session.run(query).consume()
    print("Uniqueness constraints created/verified.")
