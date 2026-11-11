import json, time, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pandas as pd
from fastapi.testclient import TestClient
from app.main import app
cases=pd.read_csv(ROOT/"evaluation/validation_10_transactions_with_ground_truth.csv")
client=TestClient(app)
results=[]
for _,row in cases.iterrows():
    response=client.post("/explain",json={"transaction_id":row.transaction_id})
    item={"transaction_id":row.transaction_id,"ground_truth_label":int(row.fraud_label),
          "http_status":response.status_code,"response":response.json()}
    results.append(item)
(ROOT/"outputs/explanation_responses.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
pd.DataFrame([{"transaction_id":x["transaction_id"],"ground_truth_label":x["ground_truth_label"],
               "risk_level":x["response"].get("risk_level"),"recommended_action":x["response"].get("recommended_action"),
               "reason_count":len(x["response"].get("reason_codes",[])),"http_status":x["http_status"]}
              for x in results]).to_csv(ROOT/"outputs/explanation_responses.csv",index=False)
print(f"Saved {len(results)} responses to outputs/")
