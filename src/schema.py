from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation


def _first(row, *names, default=None):
    for name in names:
        if name in row and row[name] not in (None, ""):
            return row[name]
    return default


def _money(value):
    if value is None or value == "":
        return None
    try:
        return float(Decimal(str(value)))
    except (InvalidOperation, ValueError):
        return None


def _date(value):
    if isinstance(value, datetime):
        dt = value
    else:
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def normalize_transaction(row):
    """Map common SENTINEL/source field-name variants to the assignment schema.

    Inspect and adapt this mapping to the actual Project Work 4/5 schema before ingestion.
    No synthetic/guessed data is generated here.
    """
    tx_id = _first(row, "transaction_id", "id", "txn_id")
    customer_id = _first(row, "customer_id", "customerId", "user_id")
    tx_time = _date(_first(row, "transaction_time", "time", "created_at", "timestamp"))
    amount = _money(_first(row, "transaction_amount", "amount", "transaction_value"))
    if tx_id is None or customer_id is None or tx_time is None or amount is None:
        return None

    label = _first(row, "fraud_label", "is_fraud", "fraud", default=None)
    if isinstance(label, str):
        label = 1 if label.strip().lower() in {"1", "true", "yes", "fraud"} else (0 if label.strip().lower() in {"0", "false", "no", "legitimate"} else None)
    elif label is not None:
        try:
            label = int(label)
        except (TypeError, ValueError):
            label = None
    if label not in (0, 1):
        label = None

    return {
        "transaction_id": str(tx_id),
        "customer_id": str(customer_id),
        "merchant_id": str(_first(row, "merchant_id", "merchantId", default="unknown")),
        "merchant_category": str(_first(row, "merchant_category", "mcc", "category", default="unknown")),
        "device_id": (str(_first(row, "device_id", "deviceId")) if _first(row, "device_id", "deviceId") is not None else None),
        "transaction_time": tx_time,
        "transaction_amount": amount,
        "fraud_label": label,
        "currency": str(_first(row, "currency", default="INR")),
        "source": "sentinel_project_work_4_5",
    }
