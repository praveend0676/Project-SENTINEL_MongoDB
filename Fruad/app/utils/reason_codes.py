REASON_DESCRIPTIONS = {
 "R01_NEW_DEVICE": "The device was not observed for this customer in the available prior history.",
 "R02_GEO_MISMATCH": "The available customer and merchant location context indicates a geographic anomaly.",
 "R03_ODD_HOUR": "The transaction occurred between midnight and 5 AM.",
 "R04_FAILED_ATTEMPTS": "At least three failed attempts were recorded in the preceding 24 hours.",
 "R05_AMOUNT_SPIKE": "The transaction amount is at least three times the prior customer average.",
 "R06_NEW_ACCOUNT": "The account age is below 30 days.",
 "R07_VELOCITY": "At least four prior transactions occurred in the preceding hour.",
 "R08_HIGH_RISK_MCC": "The merchant category is in the higher-attention categories used by this demo."
}

HIGH_RISK_CATEGORIES = {"electronics", "gaming", "gift_cards"}


def _truthy(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "t"}
    return bool(value)


def _number(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _hour_from_timestamp(value):
    if not isinstance(value, str) or not value.strip():
        return None
    from datetime import datetime
    text = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text).hour
    except ValueError:
        return None


def _derive_reasons(row: dict) -> list[str]:
    """Derive reason codes from feature columns when no precomputed list is supplied.

    Uses the same transparent demo thresholds documented in REASON_DESCRIPTIONS.
    Missing fields are skipped, never guessed.
    """
    codes: list[str] = []

    if _truthy(row.get("is_new_device")):
        codes.append("R01_NEW_DEVICE")

    hour = _number(row.get("hour_of_day"))
    if hour is None:
        hour = _hour_from_timestamp(row.get("transaction_time"))
    if hour is not None and 0 <= hour < 5:
        codes.append("R03_ODD_HOUR")

    failed = _number(row.get("failed_transactions"))
    if failed is not None and failed >= 3:
        codes.append("R04_FAILED_ATTEMPTS")

    ratio = _number(row.get("amount_to_avg_ratio"))
    if ratio is None:
        amount = _number(row.get("transaction_amount"))
        average = _number(row.get("average_transaction_value"))
        if amount is not None and average and average > 0:
            ratio = amount / average
    if ratio is not None and ratio >= 3:
        codes.append("R05_AMOUNT_SPIKE")

    age = _number(row.get("account_age_days"))
    if age is None:
        age = _number(row.get("account_age"))
    if age is not None and age < 30:
        codes.append("R06_NEW_ACCOUNT")

    velocity = _number(row.get("txn_count_last_1h"))
    if velocity is not None and velocity >= 4:
        codes.append("R07_VELOCITY")

    category = str(row.get("merchant_category") or "").strip().lower()
    if category in HIGH_RISK_CATEGORIES:
        codes.append("R08_HIGH_RISK_MCC")

    return codes


def fired_reasons(row: dict) -> list[dict]:
    import json
    raw = row.get("reason_codes")
    if raw is None:
        codes = _derive_reasons(row)
    else:
        if isinstance(raw, str):
            try: raw = json.loads(raw)
            except Exception: raw = []
        if not isinstance(raw, (list, tuple)):
            raw = []
        codes = [c for c in raw if c in REASON_DESCRIPTIONS]
    return [{"code": c, "description": REASON_DESCRIPTIONS.get(c, c)} for c in codes]
