"""Embed the included educational policy corpus with EURI Gemini Embedding 2 and upsert to Qdrant."""
import os, sys, uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT/".env")
from openai import OpenAI
from qdrant_client import QdrantClient, models

collection=os.getenv("QDRANT_COLLECTION","sentinel_knowledge")
dim=int(os.getenv("EMBEDDING_DIMENSIONS","3072"))
euri=OpenAI(api_key=os.environ["EURI_API_KEY"],
            base_url=os.getenv("EURI_BASE_URL","https://api.euron.one/api/v1/euri"))
qdrant=QdrantClient(url=os.environ["QDRANT_URL"],api_key=os.environ["QDRANT_API_KEY"])
if collection not in [c.name for c in qdrant.get_collections().collections]:
    qdrant.create_collection(collection_name=collection,
        vectors_config=models.VectorParams(size=dim,distance=models.Distance.COSINE))
qdrant.create_payload_index(collection_name=collection,field_name="document_type",
                             field_schema=models.PayloadSchemaType.KEYWORD,wait=True)
points=[]
for path in sorted((ROOT/"policy_corpus").glob("*.txt")):
    text=path.read_text(encoding="utf-8")
    response=euri.embeddings.create(model=os.getenv("EURI_EMBEDDING_MODEL","gemini-embedding-2-preview"),
                                    input=text,dimensions=dim)
    vector=response.data[0].embedding
    if len(vector)!=dim: raise ValueError(f"Expected {dim} dims, got {len(vector)}")
    points.append(models.PointStruct(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL,path.name)),
        vector=vector,
        payload={"source_document":path.name,"document_type":"playbooks",
                 "chunk_number":0,"text":text}))
qdrant.upsert(collection_name=collection,points=points,wait=True)
print(f"Upserted {len(points)} policy chunks into {collection}")
