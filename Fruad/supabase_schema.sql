-- Adapt table and column names to your actual Supabase Project Work 4/5 schema.
create table if not exists public.transactions (
  transaction_id text primary key,
  customer_id text,
  merchant_id text,
  merchant_category text,
  device_id text,
  transaction_time timestamptz,
  transaction_amount numeric,
  currency text,
  payment_method text,
  transaction_status text,
  average_transaction_value numeric,
  amount_to_avg_ratio numeric,
  is_new_device boolean,
  hour_of_day integer,
  is_night boolean,
  failed_transactions integer,
  txn_count_last_1h integer,
  txn_amount_last_24h numeric,
  reason_codes jsonb
);
-- Import data/transactions_with_features.csv through the Supabase Table Editor.
-- Do NOT import fraud_label into the API's live feature table if you want strict label isolation.
