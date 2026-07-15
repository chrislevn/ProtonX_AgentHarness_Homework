import os
from dotenv import load_dotenv

load_dotenv()

ENV_FILE = ".env"


def _write_env_key(name: str, value: str):
    lines = []
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            lines = f.readlines()
    for i, line in enumerate(lines):
        if line.startswith(name + "="):
            lines[i] = f"{name}={value}\n"
            break
    else:
        lines.append(f"{name}={value}\n")
    with open(ENV_FILE, "w") as f:
        f.writelines(lines)


def prompt_missing_keys():
    """On first run, ask for missing API keys and save them to .env."""
    for name in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
        if os.getenv(name):
            continue
        value = input(f"{name} is not set. Paste it here (saved to .env): ").strip()
        if value:
            os.environ[name] = value
            _write_env_key(name, value)

# LLM
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
LLM_MODEL = "claude-sonnet-5"

# Embeddings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536

# Qdrant
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
MEMORY_COLLECTION = "agent_memory"

# Google Drive
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "credentials.json")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")
