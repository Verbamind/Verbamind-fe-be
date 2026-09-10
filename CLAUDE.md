# VerbaMind — Agent Project Memory

Offline-first Windows desktop app (PySide6 GUI + FastAPI backend) for BIRP clinical
notes. STT = faster-whisper, LLM/RAG = Ollama (qwen2.5 + nomic-embed-text), DB = SQLite,
encryption = AES-256-GCM, packaging = Nuitka + Inno Setup.

## Critical: packaging / build gotchas (the class of bug that keeps recurring)

These are the rules that were learned the hard way. Read before touching any
`.py`, `installer/`, or build config.

1. **Nuitka compiles `.py` into the exe at build time — it does NOT read `.py` at
   runtime.** Every Python source change requires a **Nuitka rebuild** of the affected
   exe, then an **Inno Setup recompile**. There is no hot-reload.

2. **Runtime `import <native>` inside a function is invisible to Nuitka.**
   Nuitka's static analysis only follows top-level imports. Any native C extension
   (e.g. `faiss`) imported lazily inside a function is silently dropped from the
   standalone exe. Symptom: works in dev, crashes only in the packaged app with
   `ImportError` at the moment the import is first hit. Fix: add an explicit
   `--include-package=<native>` (or `--include-module=<submodule>`) in
   `installer/build_optimized.bat`. This was the FAISS/BIRP bug.

3. **`--include-package=<native>` can CRASH Nuitka** (an `AssertionError` was observed
   with `av`). Prefer `--include-module=<specific.sub>` over whole-package includes for
   native libs, and verify the build completes early after adding any new include.

4. **Frozen detection must use `__compiled__`, not `sys.frozen`.**
   Nuitka sets `sys.modules["__main__"].__compiled__`, not `sys.frozen`
   (`verbamind/config/paths.py::is_frozen`).

5. **Bundled resource lookup uses `app_install_dir()`** = frozen
   `Path(sys.executable).resolve().parent.parent` (backend at `{app}\backend\backend.exe`
   → `{app}`). Locates `faiss_index\` and `models\whisper-small\`. Don't re-derive this.

6. **`build_optimized.bat` skips a target if its output exe already exists.**
   Force a rebuild by deleting `dist\<target>.dist` first.

7. **The GUI spawns the backend with no stdout/stderr redirection**
   (`verbamind/main.py::_spawn_backend`) — backend logs are invisible in the packaged
   app. Run `backend.exe` manually with redirection to debug.

## Build environment

- MSVC: `C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat`
- Use the venv python (`.venv\Scripts\python.exe`) — global python lacks `faster_whisper`.
- Inno Setup: `C:\Program Files (x86)\Inno Setup 6\ISCC.exe` (~20 min lzma2/ultra64
  compile; run detached, poll for completion).
- Ollama at `localhost:11434`; models: LLM `qwen2.5:3b-instruct`, embeddings `nomic-embed-text`.

## Runtime data layout

`%APPDATA%\VerbaMind` — `api_token.txt`, `verbamind.db`, `recordings\`, `output_hasil\`,
`settings.json`, `.activated` / `.license`. Installed app at `%LOCALAPPDATA%\VerbaMind`.
DB `audit_logs.created_at` is UTC (local = UTC+7).
