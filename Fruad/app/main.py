from fastapi import FastAPI, HTTPException
from app.config import USE_QDRANT
from app.schemas import ExplainRequest
from app.services.transaction_service import get_transaction_with_source
from app.services.neo4j_service import get_neighbourhood
from app.services.qdrant_service import retrieve_policy
from app.services.explanation_service import make_explanation
from app.utils.reason_codes import fired_reasons

app=FastAPI(title="SENTINEL Fraud Investigator API",version="1.0.0",
            description="Evidence-grounded transaction explanation demo.")

@app.get("/health")
def health():
    return {"status":"ok","service":"sentinel-fraud-investigator-api"}

@app.post("/explain")
def explain(request: ExplainRequest):
    txn, txn_source = get_transaction_with_source(request.transaction_id)
    if not txn:
        raise HTTPException(status_code=404,detail="Transaction not found")
    reasons=fired_reasons(txn)
    graph=get_neighbourhood(txn)
    question="Explain fraud risk for this transaction. Relevant reason signals: "+", ".join(
        x["code"] for x in reasons)
    policies=retrieve_policy(question,limit=5)
    result=make_explanation(txn,graph,reasons,policies)
    citations=[{"document":p["document"],"chunk_number":p["chunk_number"],
                "relevance_score":round(p["score"],4),
                "supporting_excerpt":p["text"][:500]} for p in policies]
    return {"transaction_id":txn["transaction_id"],**result,
            "reason_codes":reasons,"policy_citations":citations,
            "evidence":{"transaction_source":txn_source,
                        "graph_source":"Neo4j" if graph.get("mode")=="neo4j" else "not_connected",
                        "policy_source":"Qdrant" if USE_QDRANT else "local_policy_corpus",
                        "graph_context":graph}}
