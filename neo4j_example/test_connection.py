from src.db import get_driver, DATABASE

if __name__ == "__main__":
    driver = get_driver()
    try:
        with driver.session(database=DATABASE) as session:
            record = session.run("RETURN 'Project SENTINEL' AS message").single()
            print("Successfully connected to Neo4j!")
            print(record["message"])
    finally:
        driver.close()
