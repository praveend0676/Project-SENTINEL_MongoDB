# Project SENTINEL — Feature Engineering

## Important
This is a configurable starter project. Table/column names in `config/settings.json` are placeholders and MUST be changed to match your Supabase schema. Numeric reason-code thresholds are intentionally blank until supplied by your class. Do not claim final match rates until the real schema, thresholds, split boundaries and client features table are mapped.

## Step 1 — Inspect Supabase schema
In Supabase → SQL Editor → New query, run:

```sql
SELECT table_name, column_name, data_type, is_nullable, ordinal_position
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;
```

Identify customer, merchant, device, transaction, payment outcome, label and client features tables, plus primary/foreign keys.

## Step 2 — Open in VS Code
Extract the ZIP and open the `SENTINEL_Feature_Engineering` folder. Open Terminal (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If activation is blocked:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Step 3 — Add Supabase credentials
Copy `.env.example` to `.env`, then add your project URL and a read-only/publishable key. Never paste keys into chat, source code, or Git. Do not use a service-role key for this exercise.

```powershell
Copy-Item .env.example .env
```

## Step 4 — Map schema
Edit `config/settings.json`. Replace all example table and column names with exact names. The transaction mapping must identify transaction ID, customer ID, timestamp and amount. Map coordinate columns and device ID if available. Map the client feature column names. Set `sample_limit_per_table` to the assignment sample size.

## Step 5 — Verify access and export
```powershell
python -m src.inspect_schema
python -m src.load_supabase
```
CSV files are exported to `data/raw/`. The feature reference table is saved as `client_features.csv`.

## Step 6 — Data quality
```powershell
python -m src.data_quality
```
Creates `outputs/data_quality_report.xlsx` with column types, null counts, null percentages, distinct values and duplicate-row counts.

## Step 7 — Rebuild features
```powershell
python -m src.feature_engineering
```
Creates `outputs/engineered_features.csv`. It computes amount/current 90-day prior mean, prior-90-day new-device flag, Haversine distance when transaction coordinate columns exist, midnight–5 AM night flag, prior-hour transaction count and prior-24-hour transaction amount. Current transaction is excluded from rolling history.

## Step 8 — Reason codes
Enter confirmed class thresholds and high-risk MCC values in `config/settings.json`, then run:
```powershell
python -m src.reason_codes
```
R01 and R03 are available from the supplied project definitions. Other rules require exact thresholds and/or source fields. R04 failed attempts and R06 account age are not inferred without their exact source fields. Do not invent thresholds.

## Step 9 — Compare with client features
```powershell
python -m src.compare_features
```
Creates `outputs/feature_match_report.xlsx` and `outputs/mismatch_details.csv`. Confirm numeric tolerance/rounding expected by your instructor.

## Full run order
```powershell
python -m src.inspect_schema
python -m src.load_supabase
python -m src.data_quality
python -m src.feature_engineering
python -m src.reason_codes
python -m src.compare_features
```

## Leakage cautions
- All rolling features use prior transactions only; labels/outcomes arriving after transaction time must not be predictors.
- Preserve the instructor's exact warmup/train/validation/holdout boundaries. Do not randomly split time-ordered data.
- The project materials identify Jan–Feb 2026 as holdout; do not train/tune on holdout.
- Timestamp timezone must be confirmed. Night-hour calculation uses the timestamp's local displayed hour.
- The data-quality script is a baseline; add split counts and amount-outlier analysis once the actual split and amount columns are confirmed.
