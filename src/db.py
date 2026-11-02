import os

from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()


def get_database():

    mongo_uri = os.getenv("MONGODB_URI")
    database_name = os.getenv(
        "MONGODB_DATABASE",
        "sentinel"
    )

    if not mongo_uri:
        raise ValueError("MONGODB_URI is missing")

    client = MongoClient(
        mongo_uri,
        serverSelectionTimeoutMS=10000
    )

    database = client[database_name]

    return client, database