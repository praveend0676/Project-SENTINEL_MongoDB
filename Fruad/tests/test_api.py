from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)

def test_health():
    assert client.get("/health").status_code==200

def test_known_transaction():
    import pandas as pd
    df=pd.read_csv("data/transactions_with_features.csv")
    tid=str(df.iloc[0]["transaction_id"])
    r=client.post("/explain",json={"transaction_id":tid})
    assert r.status_code==200
    body=r.json()
    assert body["transaction_id"]==tid
    assert "risk_summary" in body
    assert "policy_citations" in body

def test_unknown_transaction():
    assert client.post("/explain",json={"transaction_id":"NOT_A_REAL_ID"}).status_code==404
