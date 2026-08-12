# VerbaMind

**Offline-first Windows desktop app** untuk dokumentasi sesi konseling berbantuan AI (format BIRP). Semua proses berjalan lokal (localhost) — tidak ada cloud, tidak ada telemetri.

VerbaMind merekam sesi konseling dual-channel (psikolog + pasien), mengenkripsi audio, mentranskripsi ucapan (Whisper), menganalisis isyarat non-verbal suara (loudness + pitch), lalu menyusun catatan klinis format **BIRP** (Behavior, Intervention, Response, Plan) menggunakan Qwen2.5:7B dengan Retrieval-Augmented Generation (RAG).

## Tech Stack

| Layer | Teknologi |
|---|---|
| GUI | PySide6 (Windows classic aesthetic, Segoe UI) |
| Backend | FastAPI (127.0.0.1 only) |
| Database | SQLite (aiosqlite + SQLAlchemy) |
| STT | OpenAI Whisper |
| SER | Speech Nonverbal Cue Detection (loudness + pitch, fuzzy inference) |
| LLM | Qwen2.5:7B-Instruct via Ollama |
| RAG | LangChain + FAISS + sentence-transformers |
| Encryption | AES-256-GCM + Windows DPAPI |
| Packaging | Nuitka + Inno Setup |

---

## Prerequisites

- **Windows 10/11** (x64)
- **Python 3.10+**
- **Git** (opsional, untuk clone)
- **Ollama** (untuk RAG/LLM — opsional saat development)
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

### 3. Verifikasi instalasi

```powershell
pytest tests/ --cov=verbamind --cov-report=term
```

Expected: `160 passed`, coverage `85%+`.

---

## Menjalankan Aplikasi

### GUI (desktop)

```powershell
.\.venv\Scripts\Activate.ps1
python -m verbamind.main
```

### Backend (FastAPI, localhost)

```powershell
.\.venv\Scripts\Activate.ps1
python -m verbamind.backend.main
```

Buka `http://127.0.0.1:8000/docs` untuk dokumentasi API (Swagger UI).

### API Endpoints

| Method | Endpoint | Deskripsi |
|---|---|---|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/stt/transcribe` | Transkripsi audio |
| POST | `/api/v1/ser/analyze` | Analisis nonverbal (loudness + pitch) |
| POST | `/api/v1/birp/generate` | Generate catatan BIRP (RAG + LLM) |

---

## Setup RAG (untuk fitur BIRP penuh)

RAG butuh Ollama + knowledge base + FAISS index.

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

### 4. Jalankan pipeline RAG

```powershell
python -m verbamind.backend.ai_pipeline.birp_generator
```

> Model embedding (`paraphrase-multilingual-MiniLM-L12-v2`) diunduh otomatis sekali saja ke cache lokal (~470MB), lalu sepenuhnya offline.

---

## Testing

```powershell
# Full test suite dengan coverage
pytest tests/ --cov=verbamind --cov-report=term

# Test spesifik
pytest tests/test_database.py -v
pytest tests/test_security.py -v
pytest tests/test_ser.py -v
pytest tests/test_birp.py -v

# Security scan
python scripts/security_scan.py

# Manual database test
python scripts/test_db.py
```

---

## Build Installer (Nuitka + Inno Setup)

### Prasyarat Build

1. **Inno Setup 6** — https://jrsoftware.org/isinfo.php
2. **VC++ Redistributable** — download `vc_redist.x64.exe` dari https://aka.ms/vs/17/release/vc_redist.x64.exe → simpan di `installer\`
3. **Icon** — `installer\verbamind.ico` (256x256)
4. **Semua dependencies** — `pip install -r requirements.txt`

### Langkah Build

#### 1. Compile dengan Nuitka

```powershell
.\installer\build_optimized.bat
```

Menghasilkan:
- `dist\VerbaMind.dist\VerbaMind.exe` (GUI)
- `dist\backend.dist\backend.exe` (Backend)

Waktu: 10-30 menit (tergantung CPU).

#### 2. Siapkan model ML (opsional, untuk fully-offline)

```
models/
├── whisper/          # Whisper model (.pt)
├── ser/              # SER model (jika ada)
└── llm/              # qwen2.5-7b-instruct-q4_k_m.gguf
```

> Tanpa model, app tetap jalan — STT/SER/BIRP pakai mode mock/placeholder.

#### 3. Compile installer dengan Inno Setup

```
Buka installer\verbamind.iss di Inno Setup Studio → Compile (Ctrl+F9)
```

Output: `installer\output\VerbaMind-Setup-0.1.0.exe`

#### 4. Test installer

1. Jalankan `.exe` di Windows bersih / VM
2. Verifikasi: license key page → VC++ install → app launch
3. Test uninstall (harus bersih tanpa sisa)

---

## Struktur Project

```
verbamind/
├── main.py              # GUI entry point (PySide6)
├── backend/
│   ├── main.py          # FastAPI entry point
│   ├── api/             # Route handlers (health, STT, SER, BIRP)
│   ├── ai_pipeline/     # STT, SER, merge, RAG, LLM, BIRP
│   ├── audio/           # Recorder, Player, SessionManager
│   ├── database/        # SQLAlchemy models + connection
│   └── ...
├── gui/
│   ├── windows/         # QMainWindow
│   ├── pages/           # Dashboard, Recording, Patients, dll
│   ├── widgets/         # Sidebar, StatusLED, dll
│   └── styles/          # Theme (QSS)
├── ai/
│   ├── stt/             # Whisper (placeholder)
│   ├── ser/             # Nonverbal cue detection
│   └── llm/             # Qwen2.5 (placeholder)
├── security/            # AES-256, DPAPI, activation
├── tests/               # pytest + fixtures
├── models/              # Bundled ML models
├── installer/           # Nuitka + Inno Setup scripts
├── scripts/             # Dev utilities (test_db, security_scan, render_gui)
├── config/
└── plans/               # Blueprint & docs
```

---

## Keamanan

- Audio dienkripsi AES-256-GCM saat direkam (format `.vera`)
- Kunci AES dilindungi Windows DPAPI (machine-bound)
- Plaintext hanya ada di memory, tidak pernah di disk
- Aktivasi via license key + Hardware ID binding
- Semua data pasien lokal — tidak pernah dikirim ke cloud

Lihat `DECISIONS.md` untuk log keputusan arsitektur, `PRODUCT.md` untuk konteks produk.

---

## Lisensi

Proprietary — VerbaMind
