import json, os
from app.config import USE_LLM

def make_explanation(txn: dict, graph: dict, reasons: list[dict], policies: list[dict]) -> dict:
    # Risk/action come from transparent rules; the LLM only writes a grounded narrative.
    risk = "HIGH" if len(reasons)>=3 else ("MEDIUM" if len(reasons)>=1 else "LOW")
    action = "REVIEW" if risk in {"HIGH","MEDIUM"} else "ALLOW_WITH_MONITORING"
    facts = {"transaction_id":txn.get("transaction_id"),"amount":txn.get("transaction_amount"),
             "currency":txn.get("currency","INR"),"merchant_category":txn.get("merchant_category"),
             "transaction_time":txn.get("transaction_time"),"reason_codes":reasons,
             "graph_context":graph,"policy_evidence":policies}
    summary = (f"{len(reasons)} configured risk signal(s) were observed for this transaction. "
               "Review the cited evidence; these signals are not proof of fraud.")
    if USE_LLM:
        from openai import OpenAI
        client=OpenAI(api_key=os.environ["LLM_API_KEY"],base_url=os.environ["LLM_BASE_URL"])
        prompt=("Write a concise investigator-facing risk summary using ONLY the supplied JSON facts. "
                "Do not add facts, change reason codes, change risk level or action, or invent citations. "
                "Return only a JSON object with risk_summary. Facts:\n"+json.dumps(facts,default=str))
        resp=client.chat.completions.create(model=os.environ["LLM_MODEL"],
            messages=[{"role":"user","content":prompt}],temperature=0)
        content=resp.choices[0].message.content or "{}"
        try: summary=json.loads(content).get("risk_summary",summary)
        except Exception: pass
    return {"risk_level":risk,"risk_summary":summary,"recommended_action":action}
