from src.db import get_driver, DATABASE
from src.queries import SHARED_DEVICES, FRAUD_WITHIN_TWO_HOPS, SHARED_DEVICE_MERCHANTS

QUERIES = [
    ("Devices shared by 3+ customers in 7 days", SHARED_DEVICES),
    ("Customers within 2 hops of a fraud payment", FRAUD_WITHIN_TWO_HOPS),
    ("Top merchants paid through shared devices", SHARED_DEVICE_MERCHANTS),
]

if __name__ == "__main__":
    driver = get_driver()
    try:
        with driver.session(database=DATABASE) as session:
            for title, query in QUERIES:
                print("\n" + title + "\n" + "-" * len(title))
                records = session.run(query).data()
                if not records:
                    print("No matching records in this dataset/time window.")
                else:
                    for record in records[:20]:
                        print(record)
                    print(f"Displayed {min(20, len(records))} of {len(records)} records.")
    finally:
        driver.close()
