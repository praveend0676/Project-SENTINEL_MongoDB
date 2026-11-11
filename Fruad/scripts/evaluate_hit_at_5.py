import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.config import USE_QDRANT
from app.services.qdrant_service import retrieve_policy

questions = json.loads((ROOT / "evaluation/retrieval_questions.json").read_text(encoding="utf-8"))
rows = []
for item in questions:
    hits = retrieve_policy(item["question"], limit=5)
    docs = [h["document"] for h in hits]
    hit = int(item["expected_document"] in docs or any(item["expected_document"] in d for d in docs))
    rows.append({"question": item["question"], "expected_document": item["expected_document"],
                 "top5_documents": docs, "hit_at_5": hit})
score = sum(x["hit_at_5"] for x in rows) / len(rows) if rows else 0
report = {"metric": "hit@5", "queries": len(rows), "hits": sum(x["hit_at_5"] for x in rows),
          "hit_at_5": score, "results": rows,
          "retrieval_mode": "Qdrant" if USE_QDRANT else "local lexical baseline"}
(ROOT / "outputs/hit_at_5_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))
