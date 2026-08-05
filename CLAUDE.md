# CLAUDE.md — VerbaMind

## Project Identity
**Offline-first Windows desktop app** for AI-assisted counseling session documentation (BIRP format). All localhost — no cloud, no telemetry.

## Stack
| Layer | Tech |
|---|---|
| GUI | PySide6 (Windows classic aesthetic, Segoe UI) |
| Backend | FastAPI (127.0.0.1 only) |
| DB | MySQL (local) |
| STT | OpenAI Whisper |
| SER | Speech Emotion Recognition (local model) |
| LLM | Qwen2.5:7B-Instruct via RAG |
| Encryption | AES-256 + Windows DPAPI (pycryptodome) |
| Packaging | Nuitka + Inno Setup |

## Conventions

### Code Style
- **Python 3.10+** with type hints on all public functions
- **PEP 8** enforced by ruff
- Module naming: `snake_case` files, `snake_case` functions, `PascalCase` classes
- PySide6 widget naming: `snake_case` with descriptive suffix (`record_btn`, `patient_combo`)

### Project Structure
```
verbamind/
├── main.py              # GUI entry point (PySide6)
├── backend/
│   ├── main.py          # FastAPI entry point
│   ├── api/             # Route handlers
│   ├── services/        # Business logic
│   ├── models/          # SQLAlchemy models
│   └── core/            # Config, security, deps
├── gui/
│   ├── windows/         # QMainWindow subclasses
│   ├── widgets/         # Reusable QWidget subclasses
│   └── resources/       # QRC, icons, styles
├── ai/
│   ├── stt/             # Whisper integration
│   ├── ser/             # Emotion recognition
│   ├── rag/             # Retrieval pipeline
│   └── llm/             # Qwen2.5 interface
├── security/
│   ├── encryption.py    # AES-256
│   ├── dpapi.py         # Windows DPAPI wrapper
│   └── activation.py    # License + HWID
├── tests/
├── models/              # Bundled ML models
├── config/
└── plans/               # Blueprint & planning docs
```

### Testing
- **pytest** with 80%+ coverage target
- **RED → GREEN → REFACTOR** TDD cycle for all features
- Unit tests in `tests/unit/`, integration in `tests/integration/`, E2E in `tests/e2e/`
- Run: `pytest --cov=verbamind --cov-report=term`

### Git
- Conventional commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`
- One logical change per commit
- Branch naming: `feat/<name>`, `fix/<name>`

### Security
- Never commit secrets, keys, or `.vera` files
- Security review mandatory for: encryption, auth, DB queries, file I/O, activation flow
- All audio encrypted at rest — plaintext only in memory

### ECC Workflow
- Use `orch-add-feature` for new capabilities
- Use `tdd-workflow` for implementation
- Use `verification-loop` before commits
- Run `code-reviewer` + `security-reviewer` after every feature slice
