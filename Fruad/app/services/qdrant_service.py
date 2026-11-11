from pathlib import Path
import re
from app.config import POLICY_DIR, USE_QDRANT, QDRANT_COLLECTION

def _lexical_search(question: str, limit: int = 5) -> list[dict]:
    q=set(re.findall(r"[a-z0-9]+",question.lower()))
    hits=[]
    for path in sorted(POLICY_DIR.glob("*.txt")):
        text=path.read_text(encoding="utf-8")
        words=set(re.findall(r"[a-z0-9]+",text.lower()))
        score=len(q & words)/max(len(q),1)
        hits.append({"document":path.name,"chunk_number":0,
                     "score":float(score),"text":text[:1600]})
    return sorted(hits,key=lambda x:x["score"],reverse=True)[:limit]

def retrieve_policy(question: str, limit: int = 5) -> list[dict]:
    if not USE_QDRANT:
        return _lexical_search(question,limit)
    from qdrant_client import QdrantClient
    from openai import OpenAI
    from qdrant_client.models import Filter, FieldCondition, MatchAny
    import os
    client=OpenAI(api_key=os.environ["EURI_API_KEY"],
                  base_url=os.getenv("EURI_BASE_URL","https://api.euron.one/api/v1/euri"))
    emb=client.embeddings.create(model=os.getenv("EURI_EMBEDDING_MODEL","gemini-embedding-2-preview"),
                                 input=question,dimensions=int(os.getenv("EMBEDDING_DIMENSIONS","3072")))
    vector=emb.data[0].embedding
    qdrant=QdrantClient(url=os.environ["QDRANT_URL"],api_key=os.environ["QDRANT_API_KEY"])
    result=qdrant.query_points(collection_name=QDRANT_COLLECTION,query=vector,
                               limit=limit,with_payload=True,with_vectors=False)
    out=[]
    for p in result.points:
        payload=p.payload or {}
        out.append({"document":payload.get("source_document","unknown"),
                    "chunk_number":int(payload.get("chunk_number",0)),
                    "score":float(p.score),
                    "text":payload.get("text","")})
    return out
