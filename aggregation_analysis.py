from src.db import get_database
from pprint import pprint

client, db = get_database()

try:

    pipeline = [

        {
            "$match": {
                "fraud_label": {"$in": [0, 1]}
            }
        },

        {
            "$group": {
                "_id": "$merchant_category",

                "total_transactions": {
                    "$sum": 1
                },

                "fraud_transactions": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$fraud_label", 1]},
                            1,
                            0
                        ]
                    }
                },

                "genuine_transactions": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$fraud_label", 0]},
                            1,
                            0
                        ]
                    }
                }
            }
        },

        {
            "$project": {
                "_id": 0,
                "merchant_category": "$_id",
                "total_transactions": 1,
                "fraud_transactions": 1,
                "genuine_transactions": 1,

                "fraud_rate": {
                    "$multiply": [
                        {
                            "$divide": [
                                "$fraud_transactions",
                                "$total_transactions"
                            ]
                        },
                        100
                    ]
                }
            }
        },

        {
            "$sort": {
                "fraud_rate": -1
            }
        }
    ]

    results = list(
        db.transactions.aggregate(pipeline)
    )

    print("\nSENTINEL - FRAUD RATE PER MERCHANT CATEGORY")
    print("=" * 75)

    for result in results:
        print(
            f"{result['merchant_category']:15}"
            f" | Total: {result['total_transactions']:5}"
            f" | Fraud: {result['fraud_transactions']:4}"
            f" | Genuine: {result['genuine_transactions']:5}"
            f" | Fraud Rate: {result['fraud_rate']:.2f}%"
        )

finally:
    client.close()