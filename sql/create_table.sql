-- Optional example source table only. If Project Work 4/5 already created a table,
-- use that existing schema instead of running this file blindly.
create table if not exists public.transactions (
    transaction_id text primary key,
    customer_id text not null,
    merchant_id text,
    merchant_category text,
    device_id text,
    transaction_time timestamptz not null,
    transaction_amount numeric(14,2) not null,
    fraud_label integer
);

create index if not exists idx_transactions_customer_id
    on public.transactions(customer_id);
create index if not exists idx_transactions_time
    on public.transactions(transaction_time);
