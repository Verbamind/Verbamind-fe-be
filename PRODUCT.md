# VerbaMind — Product Context

## CAPABILITY

VerbaMind is an offline-first Windows desktop application for psychologists to record, encrypt, transcribe, and analyze counseling sessions. It transforms dual-channel audio recordings (patient + psychologist) into structured BIRP (Behavior, Intervention, Response, Plan) clinical documentation using on-device AI — Whisper for speech-to-text, Speech Emotion Recognition for non-verbal analysis, and Qwen2.5:7B-Instruct with Retrieval-Augmented Generation (RAG) for clinical note synthesis. All processing runs locally via a PySide6 GUI fronting a FastAPI backend service, and all audio is AES-256 encrypted at rest with Windows DPAPI-bound key protection, ensuring no patient data ever leaves the machine.

## CONSTRAINTS

### Fixed Rules & Invariants
- **Offline-first, all localhost.** No cloud services, no external API calls, no telemetry. FastAPI backend runs exclusively on 127.0.0.1.
- **AES-256 encryption at rest.** All audio files are encrypted immediately after recording using a randomly generated AES-256 key. The encrypted files carry the `.vera` extension.
- **Windows DPAPI key protection.** The AES-256 key is generated once per installation during license activation and sealed via Windows DPAPI. The encrypted audio cannot be opened on any other machine — no password required from the user.
- **Dual-channel recording.** The system requires exactly two audio input channels: one for the patient and one for the psychologist. Channel role assignment is configured by the user via the GUI.
- **BIRP output format.** AI-generated clinical summaries must produce JSON output conforming to BIRP structure: `Behavior`, `Intervention`, `Response`, `Plan`. No other clinical note formats are supported.
- **Windows-only.** The application targets the Windows desktop platform exclusively, packaged via Nuitka and Inno Setup.
- **License-key activation with hardware binding.** The application requires a valid license key verified against Hardware ID before first use. AES key generation and DPAPI binding occurs only after activation succeeds.
- **MySQL for metadata.** Session metadata, transcripts, SER results, BIRP output, and file locations are stored in a local MySQL database. Audio blobs are never stored in the database — only their encrypted file paths.

### Security Boundaries
- Audio files are never stored in plaintext on disk at any point.
- Decryption occurs only in memory during playback, transcription, or analysis.
- The AES key is never exposed to the user or written to disk in plaintext.
- Each installation's AES key is unique — recordings from one installation cannot be decrypted on another, even if the `.vera` file is transferred.

## IMPLEMENTATION CONTRACT

### Actors
| Actor | Description |
|---|---|
| **Psychologist (User)** | The sole human actor. Initiates sessions, configures audio channels, starts/stops recording, triggers AI pipeline processing, reviews transcripts, inspects BIRP output, manages patient records, and adjusts settings. |
| **System (VerbaMind)** | Manages the full pipeline from audio acquisition through encryption, decryption, transcription, emotion recognition, RAG retrieval, LLM generation, and database persistence. Enforces security invariants automatically. |

### Surfaces
| Surface | Technology | Role |
|---|---|---|
| **Desktop GUI** | PySide6 | Primary interaction point. Dashboard, session recording, playback, transcript viewer, BIRP summary viewer, patient/session management, settings, license activation. Visual style emulates Windows classic (Control Panel/settings) with Segoe UI font, `#f0f0f0` backgrounds, and `#0a5fc4` accent. |
| **Backend API** | FastAPI (localhost) | REST service handling all business logic: recording control, playback, AI pipeline orchestration, encryption/decryption, database operations. Exposed only on 127.0.0.1. |

### States and Transitions

The core session lifecycle follows a strict linear pipeline:

```
[Record Session]
      │
      ▼
[AES-256 Encrypt → .vera file]
      │
      ▼
[Idle / Stored]
      │ (user initiates analysis)
      ▼
[DPAPI Unseal → AES Key in memory]
      │
      ▼
[Whisper STT ──┬── SER]
      │              │
      ▼              ▼
[Verbatim]    [Non-Verbal Data]
      │              │
      └──────┬───────┘
             ▼
    [Merged Verbatim]
             │
             ▼
       [RAG Retrieval]
             │
             ▼
  [Qwen2.5:7B → BIRP JSON]
             │
             ▼
     [Persist to MySQL]
```

Key transition rules:
- A recording cannot be transcribed or analyzed while it is actively recording.
- Encryption is automatic and immediate — the user never sees plaintext audio files.
- The AI pipeline can be re-triggered on an existing encrypted recording (e.g., after model or knowledge base updates).
- Deletion of a session removes all associated data: audio file, transcript, BIRP output, and database rows.

### Tech Stack Decisions

| Layer | Choice | Rationale |
|---|---|---|
| GUI Framework | **PySide6** | Native Windows look-and-feel, LGPL licensing, QComboBox and QSplitter for dual-channel config and resizable panels, production desktop tooling. |
| Backend | **FastAPI** (localhost) | Clean REST separation from GUI, async support for AI pipeline orchestration, auto-generated OpenAPI docs for debugging, easy to spawn as a subprocess from the GUI. |
| Database | **MySQL** | Structured relational data for patients, sessions, transcripts, and BIRP output. Local installation or bundled portable MySQL. |
| Speech-to-Text | **OpenAI Whisper** | Offline-capable, strong Indonesian language support, word-level timestamps and speaker diarization via post-processing. |
| Speaker Emotion Recognition | **SER model** (local) | Extracts non-verbal emotional features from voice for enriched verbatim context. |
| LLM | **Qwen2.5:7B-Instruct** | Runs locally on consumer hardware (7B parameters), instruction-tuned for structured JSON output, strong multilingual (Indonesian) support. |
| RAG | **Local Knowledge Base** | Retrieves relevant therapeutic frameworks, diagnostic criteria, and prior session context to ground BIRP generation. |
| Audio Encryption | **AES-256 (pycryptodome)** | Industry standard symmetric encryption, fast on modern CPUs, zero plaintext disk exposure. |
| Key Protection | **Windows DPAPI** | No password management burden, machine-bound key isolation, built into Windows — zero external dependencies. |
| Packaging | **Nuitka + Inno Setup** | Nuitka compiles Python to native code (no source distribution), Inno Setup produces a professional Windows `.exe` installer with license key entry, hardware verification, and first-run activation flow. |

### Interface / Data Implications

1. **Dual-channel GUI configuration.** The recording UI must expose two `QComboBox` widgets for the user to select which physical microphone maps to "Patient" and which maps to "Psychologist". This mapping must be persisted per-session or as a default in settings.

2. **Session navigation.** The sidebar (left column, QListWidget) provides navigation between Dashboard, Patients, Recording, and Audit Log. Each is a separate page within a QStackedWidget. Active sessions display a recording status LED (green `#2ecc57` when recording, gray `#c9c9c9` when idle).

3. **Playback with decryption transparency.** When a user opens a past recording for playback, the system silently unseals the AES key via DPAPI, decrypts in memory, and streams the audio. The user never interacts with keys or encryption directly.

4. **BIRP viewer.** AI output is rendered as structured JSON within the GUI — fields for Behavior, Intervention, Response, and Plan — with the ability to view merged verbatim and non-verbal annotations alongside.

5. **Audit trail.** All actions (session creation, recording, deletion, AI pipeline execution) are logged to the audit page and database. No user authentication beyond the license activation — single-user desktop assumption.

6. **Offline model bundling.** Whisper, SER, and Qwen2.5:7B models are bundled in the `models/` directory during installation. First launch may require model validation or download confirmation if models exceed installer size limits.

## NON-GOALS

- **Cloud synchronization or multi-device access.** No data leaves the local machine. No cloud backup, no sync, no web dashboard.
- **Multi-user or role-based access.** Single-user desktop application. No login, no RBAC, no admin/psychologist role separation.
- **Mobile or web support.** Windows desktop only. No Android, iOS, macOS, or browser-based variant.
- **Real-time collaboration.** No concurrent multi-user session access, shared editing, or live transcript streaming.
- **Integration with clinic management systems or EMR/EHR.** No HL7/FHIR, no external API endpoints, no export to third-party clinical systems beyond the BIRP JSON output.
- **Video recording.** Audio only. No support for camera input or video session capture.
- **Telehealth / remote counseling.** No network audio streaming, no remote session orchestration. Recording requires local microphone input.
- **Support for non-Indonesian languages.** Transcription and LLM are optimized for Bahasa Indonesia. No multi-language guarantees.
- **Automatic speaker diarization without channel separation.** The dual-channel approach is the source of speaker identity. No ML-based diarization on a mixed mono stream.

## OPEN QUESTIONS

| # | Question | Impact |
|---|---|---|
| 1 | **How are Whisper, SER, and Qwen2.5 models distributed?** Bundled in the installer (large download, fully offline) vs. first-run download with validation. Affects installer size (potentially 3–8 GB) and user onboarding experience. | Packaging strategy |
| 2 | **MySQL deployment model.** Will MySQL be bundled as a portable instance (e.g., embedded or as a background service spawned by the app) or must the user install MySQL separately? Portable bundling increases installer complexity but simplifies setup for non-technical psychologists. | Deployment, user experience |
| 3 | **RAG knowledge base content and curation.** What therapeutic frameworks, diagnostic references, and clinical guidelines populate the RAG index? Who maintains and updates this content (built once, periodic updates)? The quality of BIRP output depends directly on this. | AI output quality, compliance |
| 4 | **Hardware ID verification mechanism.** Which hardware attributes are hashed for license binding (MAC address, CPU serial, motherboard UUID)? What is the tolerance for hardware changes (e.g., replacing a network adapter)? Needs a re-activation or deactivation flow. | Licensing, support burden |
| 5 | **License key distribution and management.** How are license keys generated, distributed, and validated? Is there a key server, or are keys pre-generated and shipped? What happens if offline validation fails? | Business model, piracy protection |
| 6 | **Qwen2.5:7B hardware requirements.** Minimum RAM/VRAM for acceptable inference speed? What is the fallback if the user's machine cannot run the model? CPU-only inference via llama.cpp or Ollama vs. GPU-accelerated? | Target hardware, user experience |
| 7 | **BIRP output editing and finalization.** Can the psychologist edit the AI-generated BIRP before saving/finalizing, or is it purely read-only? If editable, do edits feed back into the RAG system for future sessions? | Workflow design |
| 8 | **Session retention and storage management.** Are there automatic cleanup policies for old recordings and transcripts? What happens when disk space runs low? | Data lifecycle |
| 9 | **Dual-channel audio hardware.** What is the minimum supported hardware configuration? Does the app require a specific audio interface, or can it work with any two-microphone setup (e.g., USB + built-in)? | Hardware compatibility, documentation |

## HANDOFF

### Recommended Implementation Phases

```
Phase 1  → Database schema (MySQL: patients, sessions, transcripts, BIRP, audit log)
           + Security module (AES-256 encrypt/decrypt, DPAPI key wrapping)
           + FastAPI skeleton with encryption/decryption + recording endpoints

Phase 2  → Audio acquisition module (dual-channel recording, PyAudio/SoundDevice)
           + Whisper integration (STT with verbatim + timestamps)
           + SER integration (non-verbal feature extraction)

Phase 3  → RAG knowledge base (document ingestion, vector indexing, retrieval)
           + Qwen2.5:7B integration (prompt engineering for BIRP JSON)
           + Merged verbatim pipeline (STT + SER → enriched transcript → LLM)

Phase 4  → PySide6 GUI (dashboard, recording session with dual-channel config,
             playback, transcript viewer, BIRP viewer, session management,
             patient management, settings, license activation flow)
           + FastAPI ↔ GUI integration

Phase 5  → Installer packaging (Nuitka compilation, Inno Setup with activation flow)
           + End-to-end testing on clean Windows installs
           + Hardware ID binding + license key flow testing
```

### Critical Path Dependencies
- **Database schema** blocks all downstream persistence work (Phases 1–4).
- **Security module** (encrypt/decrypt/DPAPI) must be complete before audio recording can go end-to-end (Phase 2+).
- **Whisper + SER pipeline** must be functional before RAG and LLM can produce meaningful BIRP output (Phase 3 blocks on Phase 2).
- **GUI development** can partially parallelize with backend work but full integration tests require the backend to be available.
- **Packaging** cannot begin until the full application is stable — Nuitka compilation can surface runtime issues not caught in dev.

### First Gate
Before any implementation begins, resolve Open Questions #1 (model distribution), #2 (MySQL deployment), and #3 (RAG knowledge base) — these decisions fundamentally shape installer size, onboarding complexity, and AI output quality.
