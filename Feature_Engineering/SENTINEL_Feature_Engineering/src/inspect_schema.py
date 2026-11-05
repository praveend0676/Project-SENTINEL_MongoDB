import os
from dotenv import load_dotenv
from supabase import create_client
from src.common import load_config
def main():
    load_dotenv()
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        raise SystemExit("Set SUPABASE_URL and SUPABASE_KEY in .env")
    sb=create_client(os.getenv("SUPABASE_URL"),os.getenv("SUPABASE_KEY"))
    for logical,table in load_config()["tables"].items():
        try:
            rows=sb.table(table).select("*").limit(1).execute().data or []
            print(f"{logical} -> {table}: {list(rows[0]) if rows else 'no rows or no access'}")
        except Exception as e: print(f"{logical} -> {table}: ERROR {e}")
if __name__=="__main__": main()
