# VerbaMind — Construction Blueprint

**Objective:** Build an offline-first Windows desktop AI application for counseling session documentation using TDD methodology with ECC orchestration.

**Status:** Phase 0 — Foundation Complete | Ready for Phase 1

---

## Dependency Graph

```
Step 1 (Scaffolding)
    │
    ▼
Step 2 (Database Schema) ─────────────────────────────┐
    │                                                  │
    ▼                                                  ▼
Step 3 (Security Core) ◄──────────────── Step 6 (SER Module)
    │                                           │
    ▼                                           │
Step 4 (Audio Module)                           │
    │                                           │
    ▼                                           │
Step 5 (Whisper STT)                            │
    │                                           │
    ├────── Step 7 (Merged Verbatim) ◄──────────┘
    │           │
    │           ▼
    │      Step 8 (RAG + Qwen2.5)
    │
    ├────── Step 9 (GUI — Dashboard & Recording) ──┐
    │                                               │
    ├────── Step 10 (GUI — Transcript & BIRP) ──────┤
    │                                               │
    ├────── Step 11 (GUI — Settings & Activation) ──┤
    │                                               │
    ▼                                               ▼
Step 12 (Integration)
    │
    ▼
Step 13 (Testing & Polish)
    │
    ▼
Step 14 (Packaging)
```

**Parallel opportunities:**
- Steps 9-11 (GUI) can run in parallel with Steps 5-8 (AI Pipeline) once API contracts are defined in Step 1
- Step 6 (SER) can run in parallel with Step 5 (Whisper)
- Steps 9, 10, 11 (GUI modules) can run in parallel with each other

---

## Step 1: Project Scaffolding

**Context Brief:**
VerbaMind is a PySide6 + FastAPI desktop app. This step creates the Python project skeleton with proper package structure, dependency management, and both entry points (GUI + backend). The backend runs as a FastAPI service on 127.0.0.1; the GUI is a PySide6 application that spawns the backend as a subprocess.

**Dependencies:** None

**Files to touch:**
```
verbamind/
├── __init__.py
├── main.py                  # GUI entry point (PySide6)
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Configuration management
│   └── api/
│       ├── __init__.py
│       └── router.py        # API router skeleton
├── config/
│   └── config.example.json
├── pyproject.toml
├── requirements.txt
└── README.md
```

**Task List:**
1. Create `verbamind/` package with `__init__.py`
2. Create `verbamind/backend/` package with `__init__.py`
3. Write `pyproject.toml` with PySide6, FastAPI, uvicorn, sqlalchemy, pycryptodome, whisper, pyaudio dependencies
4. Write `requirements.txt` (pinned versions)
5. Create `verbamind/config/config.py` — reads config.json, exposes settings dict
6. Create `verbamind/config/config.example.json` — template with all keys
7. Create `verbamind/backend/main.py` — minimal FastAPI app with health endpoint
8. Create `verbamind/backend/api/router.py` — placeholder router
9. Create `verbamind/main.py` — minimal PySide6 window with "VerbaMind" title
10. Verify: `python -m verbamind.backend.main` starts on `http://127.0.0.1:8000/health`
11. Verify: `python -m verbamind.main` opens an empty PySide6 window

**Verification:**
```bash
python -m verbamind.backend.main  # Health check returns 200
python -m verbamind.main          # Window opens (300ms startup max)
```

**Exit Criteria:**
- Backend serves `/health` returning `{"status": "ok"}`
- GUI launches a PySide6 QMainWindow with title "VerbaMind"
- Config loads from `config/config.json` with graceful fallback to defaults

---

## Step 2: Database Schema

**Context Brief:**
VerbaMind stores all metadata in MySQL: patients, psychologists, sessions, transcripts, SER results, BIRP output, and audit logs. Audio files are stored on disk (`.vera` encrypted), with only file paths in the database. This step creates the full schema via SQLAlchemy models and Alembic migrations.

**Dependencies:** Step 1 (project scaffolding)

**Files to touch:**
```
verbamind/backend/
├── database/
│   ├── __init__.py
│   ├── connection.py         # SQLAlchemy engine + session
│   ├── base.py               # Declarative base
│   └── models/
│       ├── __init__.py
│       ├── patient.py
│       ├── psychologist.py
│       ├── session.py
│       ├── transcript.py
│       ├── ser_result.py
│       ├── birp_result.py
│       └── audit_log.py
├── alembic.ini
└── alembic/
    ├── env.py
    └── versions/
```

**Task List:**
1. Create `verbamind/backend/database/connection.py` — SQLAlchemy async engine, session factory
2. Create `verbamind/backend/database/base.py` — declarative Base
3. Create model files for: Patient, Psychologist, Session, Transcript, SERResult, BIRPResult, AuditLog
4. Setup Alembic: `alembic init alembic`, configure env.py for async
5. Generate initial migration: `alembic revision --autogenerate -m "initial_schema"`
6. Write tests: model creation, relationship integrity, cascade deletes
7. Run migration against local MySQL

**Verification:**
```bash
alembic upgrade head                                        # All tables created
python -m pytest tests/database/ -v --cov=verbamind.backend.database  # >= 80% coverage
```

**Exit Criteria:**
- All 7 models defined with proper relationships and cascades
- Alembic migration runs successfully against local MySQL
- Tests verify: create patient + session → add transcript → cascade delete session removes transcript
- Coverage >= 80%

---

## Step 3: Security Core

**Context Brief:**
All audio is AES-256 encrypted at rest with keys protected by Windows DPAPI. The AES key is generated once during activation, sealed via DPAPI, and stored as `config/key.dat`. Decryption happens only in memory. This step implements the encryption/decryption module and DPAPI key wrapping.

**Dependencies:** Step 1 (project scaffolding)

**Files to touch:**
```
verbamind/backend/
├── security/
│   ├── __init__.py
│   ├── encryptor.py         # AES-256 encrypt/decrypt (streaming + in-memory)
│   ├── key_manager.py       # DPAPI seal/unseal, key generation, key lifecycle
│   └── activation.py        # License key validation, HWID generation
├── tests/
│   └── test_security.py
```

**Task List:**
1. Create `encryptor.py` — `encrypt_file(input_path, output_path, key)`, `decrypt_file(input_path, output_path, key)`, `encrypt_bytes(data, key)`, `decrypt_bytes(data, key)`
2. Create `key_manager.py` — `generate_aes_key()`, `protect_with_dpapi(key)`, `unprotect_with_dpapi(blob)`, `is_key_initialized()`, `initialize_key()`
3. Create `activation.py` — `get_hardware_id()`, `validate_license_key(key, hwid)`, `is_activated()`
4. Write tests: encrypt → decrypt roundtrip, tampered ciphertext detection, DPAPI seal → unseal roundtrip, key uniqueness per generation, HWID stability
5. Test on actual Windows DPAPI (requires Windows host)

**Verification:**
```bash
python -m pytest tests/test_security.py -v --cov=verbamind.backend.security  # >= 80%
```

**Exit Criteria:**
- `encrypt_file()` + `decrypt_file()` roundtrip produces identical plaintext
- `generate_aes_key()` produces unique 256-bit keys on every call
- `protect_with_dpapi()` + `unprotect_with_dpai()` roundtrip recovers the original key
- Tampered `.vera` file raises a clear exception on decrypt
- HWID is stable across restarts (same machine → same HWID)

---

## Step 4: Audio Module

**Context Brief:**
The audio module handles dual-channel recording and playback. Two microphones are mapped to Patient and Psychologist via PyAudio/SoundDevice. Recorded audio is immediately encrypted and saved as `.vera`. Playback reads `.vera`, decrypts in memory, and streams to output device.

**Dependencies:** Step 3 (Security Core)

**Files to touch:**
```
verbamind/backend/
├── audio/
│   ├── __init__.py
│   ├── recorder.py           # Dual-channel recording controller
│   ├── player.py             # Decrypt + playback controller
│   ├── device_manager.py     # Audio device enumeration, channel mapping
│   └── session_manager.py    # Create/open/delete recording sessions
├── tests/
│   └── test_audio.py
```

**Task List:**
1. Create `device_manager.py` — `list_input_devices()`, `list_output_devices()`, `validate_device_index(idx)`
2. Create `recorder.py` — `start_recording(patient_device_idx, psychiatrist_device_idx)`, `stop_recording()`, `get_recording_status()`
3. Create `player.py` — `play_recording(filepath)`, `stop_playback()`, `seek(position_ms)`
4. Create `session_manager.py` — `create_session(patient_id, metadata)`, `open_session(session_id)`, `close_session()`, `delete_session(session_id)`
5. Integration: recorder → encrypt on stop → save as `.vera` → session_manager tracks file path
6. Write tests: mock audio devices, verify encryption is called on stop, verify playback decrypts before streaming

**Verification:**
```bash
python -m pytest tests/test_audio.py -v --cov=verbamind.backend.audio  # >= 80%
```

**Exit Criteria:**
- Recording produces a `.vera` file that can be decrypted and verified
- Playback streams decrypted audio without writing plaintext to disk
- Session CRUD operations reflect correctly in database
- Device enumeration works without crashing on missing devices

---

## Step 5: Whisper STT Integration

**Context Brief:**
Whisper transcribes the decrypted audio into verbatim text with speaker labels and timestamps. Since audio is dual-channel (separate tracks for patient and psychologist), speaker identification comes from channel assignment. Output is a structured transcript with word-level timestamps.

**Dependencies:** Step 3 (Security Core), Step 4 (Audio Module)

**Files to touch:**
```
verbamind/backend/
├── ai_pipeline/
│   ├── __init__.py
│   ├── stt.py               # Whisper wrapper: transcribe, tokenize, timestamp
│   ├── transcript_formatter.py  # Format Whisper output → internal transcript schema
├── tests/
│   └── test_stt.py
```

**Task List:**
1. Create `stt.py` — `load_model(model_size="large-v3")`, `transcribe_channel(audio_data, language="id")`, `transcribe_session(session_path, channel_map)`
2. Create `transcript_formatter.py` — `format_whisper_output(raw_segments)`, `merge_channels(patient_transcript, psych_transcript)`
3. Handle whisper model loading (from `models/whisper/` or first-run download)
4. Write tests: mock whisper with sample audio, verify segment structure, verify Indonesian language detection, verify timestamp ordering

**Verification:**
```bash
python -m pytest tests/test_stt.py -v --cov=verbamind.backend.ai_pipeline  # >= 80%
```

**Exit Criteria:**
- `transcribe_session()` returns structured segments with: text, start_time, end_time, speaker_label
- Transcript segments are ordered by timestamp
- Model loads from `models/whisper/` directory without external network access
- Empty or silent audio returns empty transcript (no crash)

---

## Step 6: SER Module

**Context Brief:**
Speech Emotion Recognition extracts non-verbal features from each audio channel: emotion classification (neutral, happy, sad, angry, anxious, etc.), voice quality markers (pitch, volume, pace), and notable non-verbal events (sighs, pauses, laughter, crying). These annotations enrich the merged verbatim for better BIRP generation.

**Dependencies:** Step 3 (Security Core), Step 4 (Audio Module)

**Can run in parallel with:** Step 5 (Whisper STT)

**Files to touch:**
```
verbamind/backend/
├── ai_pipeline/
│   ├── ser.py               # SER model wrapper
│   ├── non_verbal_annotator.py  # Annotate transcript segments with SER data
├── tests/
│   └── test_ser.py
```

**Task List:**
1. Create `ser.py` — `load_model()`, `analyze_audio(audio_data)`, `segment_emotions(audio_data, timestamps)`
2. Create `non_verbal_annotator.py` — `annotate_segment(segment, ser_data)`, `generate_non_verbal_summary(annotations)`
3. Output per-segment: dominant_emotion, intensity, voice_quality markers
4. Output per-session: overall emotional arc, notable events list
5. Write tests: mock SER with synthetic audio, verify annotation structure

**Verification:**
```bash
python -m pytest tests/test_ser.py -v --cov=verbamind.backend.ai_pipeline  # >= 80%
```

**Exit Criteria:**
- `analyze_audio()` returns per-segment emotion data with confidence scores
- Silent segments return neutral/undefined (no crash)
- Annotations map correctly to transcript segments by timestamp

---

## Step 7: Merged Verbatim Engine

**Context Brief:**
Combines Whisper transcripts (verbal text, timestamps, speaker labels) with SER annotations (emotions, non-verbal markers) into a single enriched verbatim document. This is the input to the RAG + LLM pipeline.

**Dependencies:** Step 5 (Whisper STT), Step 6 (SER Module)

**Files to touch:**
```
verbamind/backend/
├── ai_pipeline/
│   ├── merged_verbatim.py   # Combine STT + SER → enriched transcript
├── tests/
│   └── test_merged_verbatim.py
```

**Task List:**
1. Create `merged_verbatim.py` — `merge(verbal_transcript, non_verbal_data)`, `export_json(merged)`, `export_text(merged)`
2. Align SER annotations with STT timestamps (fuzzy matching for timing drift)
3. Generate session-level summary: total duration, speaker ratio, emotional distribution
4. Write tests: mock STT + SER output, verify merge correctness, verify edge cases (overlapping, missing segments)

**Verification:**
```bash
python -m pytest tests/test_merged_verbatim.py -v --cov=verbamind.backend.ai_pipeline
```

**Exit Criteria:**
- Merged output contains every STT segment enriched with SER annotation
- Timestamp alignment handles ±500ms drift gracefully
- JSON export matches the schema expected by the RAG/LLM pipeline
- Text export is human-readable for the transcript viewer

---

## Step 8: RAG + Qwen2.5 Integration

**Context Brief:**
The merged verbatim is fed into a RAG pipeline that retrieves relevant therapeutic frameworks and clinical guidelines, then Qwen2.5:7B-Instruct generates a structured BIRP JSON output. The LLM runs locally via llama.cpp or Ollama. The RAG knowledge base contains Indonesian-language therapeutic references.

**Dependencies:** Step 7 (Merged Verbatim)

**Files to touch:**
```
verbamind/backend/
├── ai_pipeline/
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── retriever.py    # Vector search over knowledge base
│   │   ├── indexer.py      # Embed + index new documents
│   │   └── knowledge_base/ # Therapeutic reference documents
│   ├── llm.py              # Qwen2.5 wrapper (llama.cpp / Ollama)
│   ├── birp_generator.py   # RAG + LLM → BIRP JSON pipeline
├── tests/
│   └── test_birp.py
```

**Task List:**
1. Create `rag/indexer.py` — embed documents, build vector index (FAISS or ChromaDB)
2. Create `rag/retriever.py` — `retrieve(query, top_k=5)` → relevant context chunks
3. Create `llm.py` — `load_model()`, `generate(prompt, system_prompt)`, `generate_json(prompt, system_prompt, schema)`
4. Create `birp_generator.py` — `generate_birp(merged_verbatim, session_context)` → BIRP JSON
5. Design BIRP prompt template with RAG context injection
6. Write tests: mock LLM output, verify JSON schema compliance, verify RAG retrieval relevance

**Verification:**
```bash
python -m pytest tests/test_birp.py -v --cov=verbamind.backend.ai_pipeline
```

**Exit Criteria:**
- `generate_birp()` returns valid JSON with Behavior, Intervention, Response, Plan keys
- RAG retrieval returns relevant context for sample verbatim inputs
- LLM fallback: if model unavailable, returns clear error (no silent failure)
- BIRP output validates against expected JSON schema

---

## Step 9: GUI — Dashboard & Recording

**Context Brief:**
PySide6 GUI with Windows classic aesthetic (from `ui-verbamind-a.html`). The main window has a sidebar navigation (Dashboard, Patients, Recording, Audit Log) and a QStackedWidget content area. The recording view has dual QComboBox for microphone assignment, recording controls, and a live LED status indicator.

**Dependencies:** Step 1 (project scaffolding)

**Can run in parallel with:** Step 10, Step 11, Steps 5-8

**Files to touch:**
```
verbamind/
├── ui/
│   ├── __init__.py
│   ├── main_window.py       # QMainWindow with sidebar + stack
│   ├── dashboard/
│   │   ├── __init__.py
│   │   └── dashboard_page.py
│   ├── recording/
│   │   ├── __init__.py
│   │   ├── recording_page.py    # Dual-channel config, recording controls
│   │   └── device_config.py     # QComboBox microphone selector
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── sidebar.py
│   │   ├── status_led.py
│   │   └── patient_list.py
│   ├── styles/
│   │   └── theme.py         # Color tokens, font config from HTML mockup
│   └── api_client.py        # Async HTTP client to FastAPI backend
├── tests/
│   └── test_ui_recording.py
```

**Task List:**
1. Create `theme.py` — color tokens (`--win-bg: #f0f0f0`, `--accent: #0a5fc4`, etc.) from HTML mockup
2. Create `api_client.py` — async client for FastAPI endpoints using aiohttp/httpx
3. Create `main_window.py` — QMainWindow, sidebar (QListWidget), QStackedWidget
4. Create `sidebar.py` — Dashboard, Patients, Recording, Audit Log navigation
5. Create `dashboard_page.py` — session list, recent activity, quick actions
6. Create `device_config.py` — enumerate audio devices, QComboBox for Patient/Psychologist channel
7. Create `recording_page.py` — record/stop/pause buttons, VU meter placeholder, status LED
8. Write tests: widget rendering, navigation switching, device enumeration display

**Verification:**
```bash
python -m verbamind.main          # GUI launches, sidebar navigates
python -m pytest tests/test_ui_recording.py -v
```

**Exit Criteria:**
- Main window renders with sidebar + content area matching HTML mockup aesthetic
- Sidebar navigation switches QStackedWidget pages correctly
- Recording page shows dual QComboBox populated with actual audio devices
- Status LED changes color (green=recording, gray=idle)

---

## Step 10: GUI — Transcript & BIRP Viewer

**Context Brief:**
After the AI pipeline completes, the psychologist views the merged verbatim transcript and BIRP output. The transcript viewer shows time-stamped segments with speaker labels and emotion annotations. The BIRP viewer displays the structured JSON in a readable card layout.

**Dependencies:** Step 1, Step 7-8 (backend API for transcript + BIRP)

**Can run in parallel with:** Step 9, Step 11

**Files to touch:**
```
verbamind/ui/
├── transcript/
│   ├── __init__.py
│   ├── transcript_page.py      # Verbatim viewer with scrollable segments
│   └── transcript_segment.py   # Single segment widget (speaker, text, emotion)
├── birp/
│   ├── __init__.py
│   ├── birp_page.py            # BIRP card view
│   └── birp_card.py            # Individual BIRP field card (Behavior, etc.)
├── tests/
│   └── test_ui_transcript_birp.py
```

**Task List:**
1. Create `transcript_segment.py` — QWidget showing speaker label, timestamp, text, emotion tag
2. Create `transcript_page.py` — QScrollArea with transcript segments, speaker filtering
3. Create `birp_card.py` — QGroupBox styled card for each BIRP field
4. Create `birp_page.py` — 4-card layout (Behavior, Intervention, Response, Plan), copy/export buttons
5. Wire both views to `api_client.py` endpoints
6. Write tests: segment rendering, BIRP card rendering, data binding from mock API

**Verification:**
```bash
python -m pytest tests/test_ui_transcript_birp.py -v
```

**Exit Criteria:**
- Transcript page renders segments with speaker label, timestamp, text, emotion color
- BIRP page renders 4 cards with JSON field content
- Both views handle empty/null data gracefully (no crash)

---

## Step 11: GUI — Settings & Activation

**Context Brief:**
Settings page for audio defaults, database path configuration, model management. The activation flow is a dedicated dialog shown on first launch: enter license key → validate against HWID → generate AES key → DPAPI seal → app unlocks.

**Dependencies:** Step 1, Step 3 (activation module)

**Can run in parallel with:** Step 9, Step 10

**Files to touch:**
```
verbamind/ui/
├── settings/
│   ├── __init__.py
│   ├── settings_page.py       # Settings form
│   └── activation_dialog.py   # License key input, HWID display, activation flow
├── tests/
│   └── test_ui_settings.py
```

**Task List:**
1. Create `activation_dialog.py` — QDialog: license key QLineEdit, activate button, status feedback, HWID display
2. Create `settings_page.py` — default microphone selection, database path, model directory, theme toggle
3. Wire activation to backend `activation.py` module via `api_client.py`
4. Check activation status on app launch → show dialog if not activated
5. Write tests: activation flow mock, settings persistence

**Verification:**
```bash
python -m pytest tests/test_ui_settings.py -v
```

**Exit Criteria:**
- Activation dialog appears on first launch, accepts license key, shows success/failure
- Settings changes persist across restarts
- Invalid license key shows clear error message

---

## Step 12: Integration

**Context Brief:**
Wire the GUI to the backend. The PySide6 app spawns the FastAPI backend as a subprocess on launch (or connects to an already-running instance). All GUI actions go through `api_client.py` → FastAPI endpoints. Full end-to-end flow: Record → Encrypt → Decrypt → Transcribe → SER → Merge → RAG → LLM → BIRP → Display.

**Dependencies:** All backend steps (2-8), all GUI steps (9-11)

**Files to touch:**
```
verbamind/
├── main.py                    # Updated: spawn backend subprocess
├── backend/
│   ├── main.py                # Updated: all routers registered
│   └── api/
│       ├── router.py          # Updated: all endpoints
│       ├── endpoints/
│       │   ├── session.py
│       │   ├── patient.py
│       │   ├── pipeline.py    # Trigger AI pipeline
│       │   └── activation.py
├── ui/
│   └── api_client.py          # Updated: all endpoint wrappers
├── tests/
│   └── test_integration.py
```

**Task List:**
1. Update `main.py` — spawn backend on launch, kill on exit, show connection status
2. Register all API endpoints in backend router
3. Implement end-to-end pipeline endpoint: POST /pipeline/run/{session_id}
4. Wire recording UI → backend recording endpoints
5. Wire transcript/BIRP viewer → backend data endpoints
6. Write integration tests: full pipeline test with mock audio
7. End-to-end test on a clean session: record → analyze → view results

**Verification:**
```bash
python -m pytest tests/test_integration.py -v
python -m verbamind.main    # Manual walkthrough: record → analyze → view
```

**Exit Criteria:**
- GUI spawns and connects to backend subprocess automatically
- Recording → Encrypt → Decrypt → Transcribe → SER → Merge → RAG → LLM → BIRP complete
- BIRP output displays in GUI within 2 minutes of analysis trigger (mock models)
- Graceful error handling: backend crash shows reconnection prompt in GUI

---

## Step 13: Testing & Polish

**Context Brief:**
Comprehensive test coverage, security audit, and verification. Ensure 80%+ coverage across all modules. Run Playwright-style E2E tests on the desktop UI. Security audit for encryption, key handling, and data privacy.

**Dependencies:** Step 12 (Integration)

**Files to touch:**
```
tests/
├── e2e/
│   └── test_full_flow.py     # Desktop E2E with pywinauto
├── coverage_report/
```

**Task List:**
1. Run full test suite with coverage: `pytest --cov=verbamind --cov-report=html`
2. Fill coverage gaps — any module below 80%
3. Desktop E2E test: launch app → activate → create patient → record → analyze → view BIRP
4. Security audit: verify no plaintext audio on disk, verify DPAPI isolation, verify no secrets in logs
5. Edge case testing: huge recordings, rapid start/stop, concurrent operations, disk full, DB connection lost
6. Generate verification report

**Verification:**
```bash
python -m pytest --cov=verbamind --cov-report=term-missing
python -m pytest tests/e2e/ -v
```

**Exit Criteria:**
- Overall coverage >= 80%
- No security issues found
- E2E test completes full session lifecycle successfully
- Verification report shows all phases PASS

---

## Step 14: Packaging

**Context Brief:**
Compile VerbaMind into a professional Windows installer. Nuitka compiles Python to native code (folder mode, not single-file). Inno Setup creates the installer with license key entry, HWID verification, and first-run activation flow. Models are either bundled or downloaded on first run.

**Dependencies:** Step 13 (Testing & Polish)

**Files to touch:**
```
installer/
├── verbaMind.iss             # Inno Setup script
├── build_optimized.bat       # Nuitka compilation script
├── slim_dist.ps1             # Dist cleanup script
└── README.txt                # Build instructions
```

**Task List:**
1. Nuitka compile backend (`--windows-console-mode=disable`, `--lto=yes`, PySide6 plugin)
2. Nuitka compile GUI (same settings, output as `VerbaMind.exe`)
3. Run `slim_dist.ps1` on both dist folders
4. Create Inno Setup script with: full metadata, license key input page, HWID display, VC++ redistributable, start menu shortcuts
5. Build installer and test on clean Windows VM
6. Verify: activation flow, recording, AI pipeline, BIRP output all work from installer

**Verification:**
```bash
# Build
.\build_optimized.bat
# Test installer on clean Windows
```

**Exit Criteria:**
- Installer produces a working VerbaMind installation on clean Windows
- First-launch activation flow works end-to-end
- Full AI pipeline runs from the installed application
- Uninstall removes all files cleanly (no leftover registry entries)

---

## Parallel Execution Summary

```
┌─────────────────────────────────────────────────────────────┐
│ WAVE 1 (serial)                                             │
│  Step 1 → Step 2 → Step 3 → Step 4                         │
│  (Scaffolding → DB Schema → Security → Audio)               │
├─────────────────────────────────────────────────────────────┤
│ WAVE 2 (parallel)                                           │
│  Step 5 (Whisper) ──┐                                       │
│  Step 6 (SER) ──────┤                                       │
│  Step 9 (GUI:Dash) ─┤  All can run simultaneously           │
│  Step 10 (GUI:Tran) ┤                                       │
│  Step 11 (GUI:Sett) ┘                                       │
├─────────────────────────────────────────────────────────────┤
│ WAVE 3 (serial, blocks on Wave 2)                           │
│  Step 7 → Step 8                                            │
│  (Merged Verbatim → RAG + Qwen2.5)                          │
├─────────────────────────────────────────────────────────────┤
│ WAVE 4 (blocks on all above)                                │
│  Step 12 (Integration)                                      │
├─────────────────────────────────────────────────────────────┤
│ WAVE 5 (blocks on Integration)                              │
│  Step 13 → Step 14                                          │
│  (Testing → Packaging)                                      │
└─────────────────────────────────────────────────────────────┘
```

**Estimated sessions:** 13-20 (3-5 if parallel agents used for Waves 2-3)

**First gate:** Resolve Open Questions #1-#3 from PRODUCT.md before Wave 2.
