from functools import lru_cache
from app.config import TRANSACTIONS_CSV, USE_SUPABASE


@lru_cache(maxsize=1)
def _csv() -> "pd.DataFrame":
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError(
            "pandas is required for local CSV mode. Install it with `pip install pandas`, "
            "or connect a live transaction store by setting USE_SUPABASE=true in .env."
        ) from exc
    if not TRANSACTIONS_CSV.exists():
        raise FileNotFoundError(f"Transaction file not found: {TRANSACTIONS_CSV}")
    return pd.read_csv(TRANSACTIONS_CSV).fillna(value={"device_id": "", "reason_codes": "[]"})


def _supabase_row(transaction_id: str) -> dict | None:
    import os
    from supabase import create_client
    client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    table = os.getenv("SUPABASE_TABLE", "transactions")
    result = (
        client.table(table)
        .select("*")
        .eq("transaction_id", transaction_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def _from_csv(transaction_id: str) -> dict | None:
    try:
        df = _csv()
    except RuntimeError:
        return None
    rows = df[df["transaction_id"].astype(str) == str(transaction_id)]
    if rows.empty:
        return None
    return rows.iloc[0].to_dict()


def get_transaction_with_source(transaction_id: str) -> tuple[dict | None, str]:
    """Look up a transaction, preferring the live store and falling back to the CSV.

    Returns ``(row, source)`` where source is "Supabase", "CSV" or "not_found".
    A live-store error (e.g. a statement timeout) is swallowed so the request
    degrades gracefully to the bundled CSV instead of failing.
    """
    if USE_SUPABASE:
        try:
            row = _supabase_row(transaction_id)
            if row is not None:
                return row, "Supabase"
        except Exception:
            pass
    row = _from_csv(transaction_id)
    if row is not None:
        return row, "CSV"
    return None, "not_found"


def get_transaction(transaction_id: str) -> dict | None:
    row, _ = get_transaction_with_source(transaction_id)
    return row
