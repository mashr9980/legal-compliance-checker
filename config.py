import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")
OLLAMA_PORT = os.getenv("OLLAMA_PORT", "11434")
OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"

MODEL_NAME = os.getenv("MODEL_NAME", "qwen3:1.7b")

TEMP_DIR = BASE_DIR / "temp_files"
REPORTS_DIR = BASE_DIR / "reports"

TEMP_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".pdf"}

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
MAX_CONCURRENT_REQUESTS = 3

LEGAL_CATEGORIES = [
    "termination",
    "payment", 
    "leave",
    "confidentiality",
    "liability",
    "intellectual_property",
    "dispute_resolution",
    "compliance",
    "other"
]