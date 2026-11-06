import os
from dotenv import load_dotenv
load_dotenv()

EURI_API_KEY = os.getenv("EURI_API_KEY")
EURI_BASE_URL = os.getenv("EURI_BASE_URL", "https://api.euron.one/api/v1/euri")
EMBEDDING_MODEL = os.getenv("EURI_EMBEDDING_MODEL", "gemini-embedding-2-preview")
VECTOR_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "3072"))

COLLECTION = os.getenv("QDRANT_COLLECTION", "sentinel_knowledge")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(ROOT, "corpus")
OUT = os.path.join(ROOT, "outputs")
CHUNK = 3000
OVERLAP = 400
MIN_DOCS = 200
