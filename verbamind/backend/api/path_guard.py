"""Path guard — restrict audio/recording paths to the recordings directory.

Prevents path traversal and arbitrary file read/delete via the localhost API.
"""

from pathlib import Path

from verbamind.config.paths import recordings_dir

ALLOWED_AUDIO_SUFFIXES = {".vera", ".wav", ".mp3", ".m4a", ".flac", ".ogg"}


def recordings_root() -> Path:
    return recordings_dir()


def _is_inside(path: Path, root: Path) -> bool:
    return root == path or root in path.parents


def resolve_audio_path(audio_path: str) -> Path:
    """Resolve an audio path and require it to be inside recordings/ with a
    supported suffix. Raises ValueError on violation.
    """
    p = Path(audio_path).resolve()
    if not _is_inside(p, recordings_root()):
        raise ValueError("audio_path harus berada di dalam folder recordings")
    if p.suffix.lower() not in ALLOWED_AUDIO_SUFFIXES:
        raise ValueError("format audio tidak didukung")
    return p


def safe_delete_recording(path: str | None) -> None:
    """Delete a file only if it resolves inside recordings/ (never elsewhere)."""
    if not path:
        return
    p = Path(path).resolve()
    if _is_inside(p, recordings_root()) and p.is_file():
        try:
            p.unlink()
        except OSError:
            pass
