"""Verbatim transcript parser — adapted from Verbamind_RAG's json_parser.py.

Parses verbatim.json (STT output) into narrative text for RAG retrieval
and LLM BIRP generation.

Source: https://github.com/Verbamind/Verbamind_RAG
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_verbatim_file(filepath: str | Path) -> dict[str, Any]:
    """Read a verbatim.json file and return parsed dictionary.

    Args:
        filepath: Path to the verbatim.json file.

    Returns:
        Dictionary with keys: 'id_sesi', 'transkrip' (list of segments).

    Raises:
        FileNotFoundError: If the file does not exist at the given path.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(
            f"File verbatim tidak ditemukan: {filepath}. "
            f"Pastikan file hasil Speech-to-Text sudah tersedia."
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def merge_transkrip_to_narrative(
    verbatim_data: dict[str, Any],
    include_speaker: bool = True,
    include_emotion: bool = False,
) -> str:
    """Combine transcript segments into a single narrative paragraph.

    Args:
        verbatim_data: Dictionary from load_verbatim_file().
        include_speaker: Prefix each line with speaker name (e.g., "Psikolog: ...").
        include_emotion: Include emotion labels in parentheses.

    Returns:
        Single narrative string with lines joined by newlines.

    Raises:
        ValueError: If 'transkrip' field is empty or missing.
    """
    segments: list[dict[str, str]] = verbatim_data.get("transkrip", [])

    if not segments:
        raise ValueError(
            "Field 'transkrip' pada file verbatim kosong atau tidak ditemukan."
        )

    lines: list[str] = []
    for seg in segments:
        text = seg.get("teks", "").strip()
        speaker = seg.get("speaker", "Tidak diketahui")
        emotion = seg.get("emosi", "")

        if not text:
            continue

        prefix = ""
        if include_speaker:
            if include_emotion and emotion:
                prefix = f"{speaker} ({emotion}): "
            else:
                prefix = f"{speaker}: "

        lines.append(f"{prefix}{text}")

    return "\n".join(lines)


def extract_session_id(verbatim_data: dict[str, Any]) -> str:
    """Extract session ID from verbatim data.

    Args:
        verbatim_data: Dictionary from load_verbatim_file().

    Returns:
        Session ID string, or 'SESI-TIDAK-DIKETAHUI' if missing.
    """
    return verbatim_data.get("id_sesi", "SESI-TIDAK-DIKETAHUI")
