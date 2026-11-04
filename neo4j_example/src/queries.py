SHARED_DEVICES = """
MATCH (c:Customer)-[r:USED_DEVICE]->(d:Device)
WHERE r.last_seen >= datetime() - duration('P7D')
WITH d, collect(DISTINCT c.customer_id) AS customers, max(r.last_seen) AS latest_activity
WHERE size(customers) >= 3
RETURN d.device_id AS device_id, size(customers) AS distinct_customers,
       customers, latest_activity
ORDER BY distinct_customers DESC
"""

# Two hops: Customer -> Device -> Customer; inspect the connected customer's fraud payment.
FRAUD_WITHIN_TWO_HOPS = """
MATCH (nearby:Customer)-[:USED_DEVICE]->(d:Device)<-[:USED_DEVICE]-(fraudCustomer:Customer)
MATCH (fraudCustomer)-[p:PAID]->(m:Merchant)
WHERE p.fraud_label = 1 AND nearby.customer_id <> fraudCustomer.customer_id
RETURN DISTINCT nearby.customer_id AS nearby_customer,
       fraudCustomer.customer_id AS fraud_customer, d.device_id AS shared_device,
       p.transaction_id AS fraud_transaction, p.amount AS amount,
       p.time AS transaction_time, m.merchant_id AS merchant_id
ORDER BY transaction_time DESC
"""

SHARED_DEVICE_MERCHANTS = """
MATCH (c:Customer)-[u:USED_DEVICE]->(d:Device)
WHERE u.last_seen >= datetime() - duration('P7D')
WITH d, collect(DISTINCT c.customer_id) AS customer_ids
WHERE size(customer_ids) >= 3
MATCH (payer:Customer)-[p:PAID]->(m:Merchant)
WHERE p.device_id = d.device_id AND payer.customer_id IN customer_ids
RETURN m.merchant_id AS merchant_id, count(p) AS payments_from_shared_devices,
       count(DISTINCT d.device_id) AS shared_devices, sum(p.amount) AS total_amount,
       sum(CASE WHEN p.fraud_label = 1 THEN 1 ELSE 0 END) AS fraud_payments
ORDER BY payments_from_shared_devices DESC
LIMIT 10
"""
