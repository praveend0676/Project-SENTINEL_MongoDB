from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}

DATA_SOURCE = os.getenv("DATA_SOURCE", "csv").lower()
TRANSACTIONS_CSV = ROOT / os.getenv("TRANSACTIONS_CSV", "data/transactions_with_features.csv")
POLICY_DIR = ROOT / "policy_corpus"
OUTPUT_DIR = ROOT / "outputs"
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "sentinel_knowledge")
USE_QDRANT = env_bool("USE_QDRANT")
USE_NEO4J = env_bool("USE_NEO4J")
USE_SUPABASE = env_bool("USE_SUPABASE")
USE_LLM = env_bool("USE_LLM")
