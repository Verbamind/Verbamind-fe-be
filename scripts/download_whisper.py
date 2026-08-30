"""Download Whisper model once into the local whisper cache (offline-first).

Usage:
    python scripts/download_whisper.py [small|base|medium]

Whisper stores downloaded models in %USERPROFILE%\\.cache\\whisper.
After this one-time download, the app runs fully offline.
"""

import sys


def main() -> None:
    size = sys.argv[1] if len(sys.argv) > 1 else "small"
    import whisper

    print(f"[INFO] Mengunduh whisper '{size}' (sekali saja, ~460MB untuk small)...")
    model = whisper.load_model(size)
    print(f"[SUKSES] Model '{size}' siap. Multilingual, dir: cache whisper lokal.")
    _ = model


if __name__ == "__main__":
    main()
