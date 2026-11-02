"""Run CRUD, index/explain, and aggregation demonstrations against Atlas."""
from datetime import datetime, timedelta, timezone
from src.db import get_database
from pymongo.errors import DuplicateKeyError, BulkWriteError


def main():
    client, db = get_database()
    tx = db["transactions"]
    try:
        # 1) insert_one: dedicated demo record; duplicate-key is harmless on reruns.
        demo_one = {
            "transaction_id": "DEMO-TX-INSERT-ONE", "customer_id": "DEMO-CUSTOMER",
            "merchant_id": "DEMO-MERCHANT", "merchant_category": "education",
            "device_id": "DEMO-DEVICE", "transaction_time": datetime.now(timezone.utc),
            "transaction_amount": 1250.0, "fraud_label": 0, "source": "demo_only"
        }
        try:
            tx.insert_one(demo_one)
            print("insert_one inserted demo record")
        except DuplicateKeyError:
            print("insert_one demo record already exists from a previous run")

        # 2) insert_many: two dedicated demo records; ignore duplicate IDs on reruns.
        demos = [
            {"transaction_id": "DEMO-TX-BULK-1", "customer_id": "DEMO-CUSTOMER", "merchant_id": "DEMO-MERCHANT", "merchant_category": "education", "device_id": "DEMO-DEVICE", "transaction_time": datetime.now(timezone.utc), "transaction_amount": 800.0, "fraud_label": 0, "source": "demo_only"},
            {"transaction_id": "DEMO-TX-BULK-2", "customer_id": "DEMO-CUSTOMER", "merchant_id": "DEMO-MERCHANT", "merchant_category": "retail", "device_id": "DEMO-DEVICE", "transaction_time": datetime.now(timezone.utc), "transaction_amount": 2200.0, "fraud_label": 1, "source": "demo_only"},
        ]
        try:
            tx.insert_many(demos, ordered=False)
            print("insert_many inserted 2 demo records")
        except BulkWriteError as exc:
            non_duplicate_errors = [e for e in exc.details.get("writeErrors", []) if e.get("code") != 11000]
            if non_duplicate_errors:
                raise
            print("insert_many demo records already exist from a previous run")

        # 3) find with filter and projection
        sample = list(tx.find({"transaction_amount": {"$gte": 1000}}, {"_id": 0, "transaction_id": 1, "customer_id": 1, "transaction_amount": 1}).limit(5))
        print("find/filter/projection sample:", sample)

        # 4) update_many: mark demo rows with a review flag (does not modify source data)
        update_result = tx.update_many({"source": "demo_only"}, {"$set": {"training_demo_reviewed": True}})
        print("update_many modified:", update_result.modified_count)

        # 5) explain before indexes
        query = {"customer_id": "DEMO-CUSTOMER"}
        print("EXPLAIN BEFORE INDEX (run this before create_indexes.py for meaningful comparison):")
        print(tx.find(query).explain().get("queryPlanner", {}).get("winningPlan"))

        # 6) Aggregation: fraud rate per merchant category. Null labels excluded from denominator.
        labelled = tx.count_documents({"fraud_label": {"$in": [0, 1]}})
        source_labelled = tx.count_documents({"source": "sentinel_project_work_4_5", "fraud_label": {"$in": [0, 1]}})
        fraud_rate = list(tx.aggregate([
            {"$match": {"fraud_label": {"$in": [0, 1]}}},
            {"$group": {"_id": "$merchant_category", "transactions": {"$sum": 1}, "fraud_count": {"$sum": {"$cond": [{"$eq": ["$fraud_label", 1]}, 1, 0]}}}},
            {"$project": {"_id": 0, "merchant_category": "$_id", "transactions": 1, "fraud_count": 1, "fraud_rate": {"$cond": [{"$gt": ["$transactions", 0]}, {"$divide": ["$fraud_count", "$transactions"]}, 0]}}},
            {"$sort": {"fraud_rate": -1}}
        ]))
        print("Labelled transactions:", labelled, "| labelled source rows:", source_labelled)
        if source_labelled == 0:
            print("NOTE: the Supabase source has no fraud_label column; only labelled demo rows contribute below.")
        print("Fraud rate per merchant category:", fraud_rate)

        # 7) Top 10 customers by total transaction amount in last 24 hours
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        top_customers = list(tx.aggregate([
            {"$match": {"transaction_time": {"$gte": cutoff}}},
            {"$group": {"_id": "$customer_id", "total_amount_24h": {"$sum": "$transaction_amount"}, "transaction_count": {"$sum": 1}}},
            {"$sort": {"total_amount_24h": -1}}, {"$limit": 10},
            {"$project": {"_id": 0, "customer_id": "$_id", "total_amount_24h": 1, "transaction_count": 1}}
        ]))
        print("Top 10 customers by amount in last 24 hours (now):", top_customers)

        # 7b) Same pipeline anchored to the latest transaction in the dataset (useful for historical data).
        latest = tx.find_one({"source": "sentinel_project_work_4_5"}, sort=[("transaction_time", -1)])
        if latest:
            dataset_cutoff = latest["transaction_time"] - timedelta(hours=24)
            top_customers_dataset = list(tx.aggregate([
                {"$match": {"transaction_time": {"$gte": dataset_cutoff}}},
                {"$group": {"_id": "$customer_id", "total_amount_24h": {"$sum": "$transaction_amount"}, "transaction_count": {"$sum": 1}}},
                {"$sort": {"total_amount_24h": -1}}, {"$limit": 10},
                {"$project": {"_id": 0, "customer_id": "$_id", "total_amount_24h": 1, "transaction_count": 1}}
            ]))
            print("Top 10 customers by amount in the latest 24h of the dataset:", top_customers_dataset)

        # 8) delete_one: delete only a dedicated demo document
        delete_result = tx.delete_one({"transaction_id": "DEMO-TX-INSERT-ONE"})
        print("delete_one deleted demo record count:", delete_result.deleted_count)
    finally:
        client.close()

if __name__ == "__main__":
    main()
