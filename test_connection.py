from src.db import get_database

client, db = get_database()

try:
    print("MongoDB Connection Successful!")

    print("Ping:", db.command("ping"))

    print("Database:", db.name)

    print("Collections:", db.list_collection_names())

finally:
    client.close()