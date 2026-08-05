# DECISIONS.md — Architecture Deviations Log

This document tracks every deviation from the original architecture design in `arsitektur-sistem-VerbaMind.md`.

---

## Decision 1: MySQL → SQLite

- **Date:** 2026-08-05
- **Original:** MySQL (local, either bundled portable or user-installed)
- **Deviation:** SQLite embedded via SQLAlchemy + aiosqlite async driver
- **Rationale:**
  1. **Target user is a non-technical psychologist.** Requiring MySQL installation creates a killer UX problem — psychologists cannot be expected to configure database services, root passwords, or port settings.
  2. **Single-user desktop app.** MySQL is designed for concurrent multi-user server workloads. For a solo user on a single laptop, an embedded file-based DB is the correct architectural fit.
  3. **Zero operational burden.** No service spawn logic, no background process, no port conflicts. The database is a single file (`verbamind.db`) alongside the application.
  4. **Installer simplicity.** Portable MySQL adds ~300 MB to installer and requires complex service management. SQLite adds ~2 MB (the library is built into Python).
  5. **SQLAlchemy ORM abstracts the dialect.** Switching from MySQL to SQLite is a connection-string change. SQLAlchemy models remain identical.
- **Impact:** `backend/core/db.py` uses `sqlite+aiosqlite` connection string. No `\d` commands, no service management. Alembic migrations remain unchanged aside from dialect-specific options.

---

## Decision 2: RAG → Deferred to Phase 6

- **Date:** 2026-08-05
- **Original:** Retrieval-Augmented Generation with local knowledge base (ChromaDB/FAISS + sentence-transformers)
- **Deviation:** RAG is intentionally skipped for MVP. Qwen2.5:7B-Instruct runs with pure prompt engineering (zero-shot + few-shot BIRP templates). RAG knowledge base will be merged from an external repository in a later phase.
- **Rationale:**
  1. User requested RAG be sourced from another repository (external merge).
  2. Prompt engineering alone is sufficient to produce BIRP JSON — the core value proposition (structured clinical notes from dual-channel audio) works without RAG.
  3. Decouples the critical path — RAG becomes a non-blocking Phase 6 enhancement.
- **Impact:** `backend/ai_pipeline/rag/` directory exists as a prepared slot with placeholder comments. Qwen2.5 BIRP generation uses only the merged verbatim transcript as input, no retrieval context. Prompt templates are in `backend/ai_pipeline/prompts/`.

---

## Decision 3: Model Distribution — Bundle in Installer

- **Date:** 2026-08-05
- **Original:** TBD (question #1 in PRODUCT.md)
- **Deviation:** All ML models bundled directly in installer (3-8 GB total). No first-run download.
- **Rationale:**
  1. Fully preserves the **offline-first invariant** — zero internet required at any point after install.
  2. Psycholgist's office environments may have restricted internet access.
  3. Pre-validated model versions eliminate runtime download failures.
- **Impact:** Installer uses Inno Setup disk spanning (`DiskSpanning=yes`, `DiskSliceSize= 2G`). Models live in `models/whisper/`, `models/ser/`, `models/llm/`. Model validation at application startup verifies file presence and integrity.
