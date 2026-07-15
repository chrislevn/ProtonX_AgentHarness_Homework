# ProtonX AgentHarness Homework

## Homework 1 — AI Agent with Tool Registry

An AI agent (Claude) with a tool registry that runs every tool call through a 6-step pipeline:

**Validate Schema → Authenticate → Check Scopes → Rate Limit → Audit Log → Execute**

### Tools

- **Google Drive** — search and read files from a Drive folder
- **Read File** — read local files
- **RAG Memory** — save/recall memories (Qdrant + OpenAI embeddings)

### Roles

| Role  | API Key        | Permissions                 |
|-------|----------------|-----------------------------|
| admin | `sk-admin-001` | read + write (memory:write) |
| user  | `sk-user-002`  | read only                   |

### Setup

```bash
cd Homework1
pip install -r requirements.txt
```

Requires:
- `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` (prompted on first run, saved to `.env`)
- Qdrant running on `localhost:6333` (for memory)
- Google service account JSON + `GOOGLE_DRIVE_FOLDER_ID` (for Drive)

### Run

```bash
python main.py    # CLI chat
python server.py  # Web UI at http://localhost:9003
```
