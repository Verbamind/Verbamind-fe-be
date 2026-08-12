# VerbaMind Installer — Build Instructions

## Prerequisites

1. **Python 3.10+** with all dependencies installed (`pip install -r requirements.txt`)
2. **Nuitka** (`pip install nuitka`)
3. **Inno Setup 6.x** — Download from https://jrsoftware.org/isinfo.php
4. **Visual C++ Redistributable** — Download `vc_redist.x64.exe` from Microsoft and place in `installer/`
5. **Icon file** — Place `verbamind.ico` in `installer/` (256x256 .ico format)

## Build Steps

### Step 1: Compile with Nuitka

```powershell
# From project root
.\installer\build_optimized.bat
```

This will:
- Compile GUI (`verbamind\main.py` → `dist\VerbaMind.dist\VerbaMind.exe`)
- Compile Backend (`verbamind\backend\main.py` → `dist\backend.dist\backend.exe`)
- Apply LTO (Link-Time Optimization) for smaller size
- Strip debug symbols, caches, tests via `slim_dist.ps1`

**Expected build time:** 10-30 minutes (depends on CPU)
**Expected output size:** 200-400 MB (before model bundling)

### Step 2: Add ML Models

Before packaging, copy model files:

```
models/
├── whisper/          # Whisper model (small/base/medium)
│   └── (model files)
├── ser/              # SER model files (if any)
│   └── (model files)
└── llm/              # Qwen2.5:7B GGUF
    └── qwen2.5-7b-instruct-q4_k_m.gguf
```

### Step 3: Create Installer with Inno Setup

1. Open `installer\verbamind.iss` in **Inno Setup Studio**
2. Click **Compile** (Ctrl+F9)
3. Output: `installer\output\VerbaMind-Setup-0.1.0.exe`

### Step 4: Test Installer

1. Run `VerbaMind-Setup-0.1.0.exe` on a clean Windows machine
2. Verify:
   - License key entry page appears
   - VC++ Redistributable installs silently
   - App launches after install
   - `recordings/`, `logs/` directories created on first run
3. Test uninstall — verify clean removal

## File Structure

```
installer/
├── build_optimized.bat   # Nuitka compilation script
├── slim_dist.ps1         # dist folder cleanup
├── verbamind.iss         # Inno Setup script
├── verbamind.ico         # App icon (YOU MUST ADD)
├── vc_redist.x64.exe     # VC++ runtime (YOU MUST ADD)
└── README.md             # This file
```

## Troubleshooting

### Nuitka build fails
- Ensure all `pip install -r requirements.txt` succeeded
- Try without `--lto=yes` if linker errors occur
- Check `--jobs` matches your CPU core count

### Inno Setup compile fails
- Ensure `dist\VerbaMind.dist\` and `dist\backend.dist\` exist
- Ensure `installer\verbamind.ico` exists
- Ensure `installer\vc_redist.x64.exe` exists

### App crashes on launch
- Check Windows Event Viewer for error details
- Verify VC++ Redistributable is installed
- Run from command prompt to see stderr: `VerbaMind.exe 2>error.log`
