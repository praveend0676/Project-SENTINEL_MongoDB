# Copy these cells into a VS Code Jupyter Notebook if required.
# Cell 1:
# %pip install -r requirements.txt

# Cell 2:
from src.db import get_database
client, db = get_database()
client.admin.command("ping")
print("Connected to MongoDB Atlas", db.name)

# Cell 3: inspect counts
print("customers:", db["customers"].count_documents({}))
print("transactions:", db["transactions"].count_documents({}))

# Cell 4: close when done
client.close()
