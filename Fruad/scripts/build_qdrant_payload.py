"""Print the payload format expected by Qdrant ingestion.
Use this helper to adapt existing SENTINEL chunks; it does not upload without credentials."""
from pathlib import Path
import json
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.config import POLICY_DIR
for path in sorted(POLICY_DIR.glob("*.txt")):
    print(json.dumps({"source_document":path.name,"document_type":"playbooks",
                      "chunk_number":0,"text":path.read_text(encoding="utf-8")}))
