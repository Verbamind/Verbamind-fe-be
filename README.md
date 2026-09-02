# VerbaMind

**Offline-first Windows desktop app** untuk dokumentasi sesi konseling berbantuan AI (format BIRP). Semua proses berjalan lokal (localhost) — tidak ada cloud, tidak ada telemetri.

VerbaMind merekam sesi konseling dual-channel (psikolog + pasien), mengenkripsi audio, mentranskripsi ucapan (Whisper), menganalisis isyarat non-verbal suara (loudness + pitch), lalu menyusun catatan klinis format **BIRP** (Behavior, Intervention, Response, Plan) menggunakan Qwen2.5 dengan Retrieval-Augmented Generation (RAG).

## Tech Stack

| Layer | Teknologi |
|---|---|
| GUI | PySide6 (Windows classic aesthetic, Segoe UI) |
| Backend | FastAPI (127.0.0.1 only) |
| Database | SQLite (aiosqlite + SQLAlchemy) |
| STT | faster-whisper (CTranslate2) — model `small` |
| Nonverbal | SpeechToNonverbalInformation (loudness + pitch, fuzzy inference) |
| LLM | Qwen2.5 via Ollama (default `qwen2.5:7b-instruct`) |
| RAG | LangChain + FAISS + Ollama embeddings (`nomic-embed-text`) |
| Encryption | AES-256-GCM |
| Packaging | Nuitka + Inno Setup |

---

## Prerequisites

- **Windows 10/11** (x64)
- **Python 3.10+**
- **Ollama** (untuk LLM + RAG)
- **Git** (opsional, untuk clone)
- **Inno Setup 6** (untuk build installer — opsional)

---

## Installation (Development)

### 1. Clone repository

```powershell
git clone https://github.com/Verbamind/Verbamind-fe-be.git
cd Verbamind-fe-be
```

### 2. Setup environment

```powershell
# Otomatis: buat venv + install semua dependencies
.\setup.ps1

# Manual (jika tidak pakai setup.ps1):
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

### 3. Siapkan model

```powershell
# LLM + embedding via Ollama
ollama pull qwen2.5:7b-instruct
ollama pull nomic-embed-text

# Model Whisper (diunduh sekali ke cache lokal)
python scripts/download_whisper.py small
```

### 4. Verifikasi instalasi

```powershell
pytest tests/ -q
```

Expected: `171 passed`.

---

## Menjalankan Aplikasi

VerbaMind terdiri dari **dua proses** yang harus dijalankan bersamaan (backend + GUI).

### 1. Backend (FastAPI, localhost)

```powershell
.\.venv\Scripts\Activate.ps1
python -m verbamind.backend.main
```

Buka `http://127.0.0.1:8000/docs` untuk dokumentasi API (Swagger UI).

### 2. GUI (desktop)

```powershell
.\.venv\Scripts\Activate.ps1
python -m verbamind.main
```

> **Autentikasi**: backend & GUI berbagi token rahasia yang di-generate otomatis di `config/api_token.txt` (dibuat saat pertama kali dijalankan). GUI mengirim header `X-VerbaMind-Token` di setiap request. File token di-ignore oleh git.

---

## API Endpoints

| Method | Endpoint | Deskripsi |
|---|---|---|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/dashboard/stats` | Statistik dashboard |
| GET | `/api/v1/patients` | Daftar pasien |
| POST | `/api/v1/patients` | Tambah pasien |
| GET | `/api/v1/patients/{id}` | Detail pasien |
| DELETE | `/api/v1/patients/{id}` | Hapus pasien |
| GET | `/api/v1/sessions` | Daftar sesi |
| POST | `/api/v1/sessions` | Buat sesi |
| GET | `/api/v1/sessions/{id}` | Detail sesi (transkrip + BIRP) |
| PUT | `/api/v1/sessions/{id}/birp` | Simpan/edit BIRP |
| DELETE | `/api/v1/sessions/{id}/audio` | Hapus audio (auto-delete policy) |
| POST | `/api/v1/sessions/{id}/keep-audio` | Pertahankan audio |
| GET | `/api/v1/audit` | Log audit (filter aksi & tanggal) |
| POST | `/api/v1/stt/transcribe` | Transkripsi audio |
| POST | `/api/v1/nonverbal/analyze` | Analisis nonverbal (loudness + pitch) |
| POST | `/api/v1/process` | **Pipeline penuh**: STT → nonverbal → merge → RAG + LLM → BIRP |
| POST | `/api/v1/birp/generate` | Generate BIRP dari verbatim |

Semua endpoint memerlukan header `X-VerbaMind-Token`.

---

## Alur AI (Pipeline `/api/v1/process`)

```
Rekam (.vera terenkripsi)
   → decrypt (in-memory)
   → split channel (Channel 1 = pasien, Channel 2 = psikolog)
   → Whisper STT (kedua channel)
   → SpeechToNonverbalInformation (hanya channel pasien)
   → merge (verbatim + isyarat nonverbal)
   → RAG retrieval (FAISS)
   → LLM Qwen2.5 → BIRP {behavior, intervention, response, plan}
   → persist ke SQLite (Transcript, NonverbalResult, BIRPResult)
```

---

## Setup RAG (opsional, untuk konteks klinis)

### 1. Install Ollama + model

```powershell
# Install dari https://ollama.com
ollama pull qwen2.5:7b-instruct
ollama serve
```

### 2. Siapkan knowledge base

```powershell
mkdir data\knowledge_base
# Taruh file .txt / .pdf berisi kode etik / teori psikologi di folder ini
```

### 3. Build FAISS index

```powershell
python -m verbamind.backend.ai_pipeline.rag.knowledge_ingest
```

> Model embedding `nomic-embed-text` dijalankan via Ollama (harus sudah `ollama pull nomic-embed-text`). Folder `data/` dan `faiss_index/` di-ignore oleh git.

---

## Testing

```powershell
# Full test suite
pytest tests/ -q

# Test spesifik
pytest tests/test_database.py -v
pytest tests/test_security.py -v
pytest tests/test_speech_to_nonverbal.py -v
pytest tests/test_birp.py -v
pytest tests/test_process_api.py -v

# Lint
ruff check verbamind
```

---

## Build Installer (Nuitka + Inno Setup)

### Prasyarat Build

1. **Inno Setup 6** — https://jrsoftware.org/isinfo.php
2. **VC++ Redistributable** — `vc_redist.x64.exe` dari https://aka.ms/vs/17/release/vc_redist.x64.exe → simpan di `installer\`
3. **Icon** — `installer\verbamind.ico` (256x256)
4. **Semua dependencies** — `pip install -r requirements.txt`

### Langkah Build

1. Compile dengan Nuitka: `.\installer\build_optimized.bat`
   - `dist\VerbaMind.dist\VerbaMind.exe` (GUI)
   - `dist\backend.dist\backend.exe` (Backend)
2. Siapkan model ML di `models/` (whisper / speech_to_nonverbal / llm) untuk fully-offline.
3. Buka `installer\verbamind.iss` di Inno Setup Studio → Compile (Ctrl+F9).
4. Output: `installer\output\VerbaMind-Setup-0.1.0.exe`.

---

## Struktur Project

```
verbamind/
├── main.py              # GUI entry point (PySide6)
├── backend/
│   ├── main.py          # FastAPI entry point
│   ├── api/             # Route handlers (patients, sessions, process, birp, audit, …)
│   ├── ai_pipeline/     # STT, nonverbal, merge, RAG, LLM, BIRP
│   ├── audio/           # Recorder, Player, SessionManager
│   ├── database/        # SQLAlchemy models + connection
│   └── ...
├── gui/
│   ├── windows/         # QMainWindow
│   ├── pages/           # Dashboard, Patients, Recording, Audit, Settings, …
│   ├── dialogs/         # Verbatim + BIRP modal
│   ├── widgets/         # Sidebar, icons, spinner, level meter, …
│   └── styles/          # Theme (QSS)
├── ai/
│   ├── stt/             # Whisper (placeholder)
│   ├── speech_to_nonverbal/  # Deteksi isyarat nonverbal
│   └── llm/             # Qwen2.5 (placeholder)
├── security/            # AES-256, DPAPI, token, activation
├── tests/               # pytest + fixtures
├── models/              # Bundled ML models (whisper / speech_to_nonverbal / llm)
├── installer/           # Nuitka + Inno Setup scripts
├── scripts/             # Dev utilities (download_whisper, security_scan, …)
└── config/              # config.json + token/key (git-ignored)
```

---

## Keamanan

- Audio dienkripsi **AES-256-GCM** saat direkam (format `.vera`)
- Plaintext hanya ada di memory, tidak pernah di disk
- **Autentikasi token** (`X-VerbaMind-Token`) antara GUI dan backend — menutup celah DNS-rebinding / akses proses lokal
- **Path guard** — endpoint audio hanya menerima path di dalam folder `recordings/` (mencegah path traversal)
- Semua data pasien lokal — tidak pernah dikirim ke cloud

---

## Lisensi

Proprietary — VerbaMind
