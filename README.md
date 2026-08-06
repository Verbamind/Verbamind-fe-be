# VerbaMind

AI-assisted counseling session documentation — offline Windows desktop app.

## Quick Start

```powershell
.\setup.ps1           # Create venv + install all dependencies
.\.venv\Scripts\Activate.ps1
pytest                # Run tests
```

## Stack

- **GUI:** PySide6
- **Backend:** FastAPI (localhost)
- **DB:** SQLite (aiosqlite + SQLAlchemy)
- **AI:** Whisper + SER + Qwen2.5:7B
- **Security:** AES-256 + Windows DPAPI
