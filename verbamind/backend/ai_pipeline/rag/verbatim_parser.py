# ==============================================================================
# verbatim_parser.py — adapted from Verbamind_RAG src/utils/json_parser.py
# ==============================================================================

import json
from pathlib import Path
from typing import Any, Dict, List


def muat_file_verbatim(path_file_json: str) -> Dict[str, Any]:
    path_obj = Path(path_file_json)
    if not path_obj.exists():
        raise FileNotFoundError(
            f"File verbatim tidak ditemukan pada path: {path_file_json}. "
            f"Pastikan file hasil Speech-to-Text sudah tersedia sebelum "
            f"menjalankan pipeline RAG."
        )
    with open(path_obj, "r", encoding="utf-8") as file_handle:
        data_json = json.load(file_handle)
    return data_json


def gabungkan_transkrip_menjadi_narasi(
    data_verbatim: Dict[str, Any],
    sertakan_nama_speaker: bool = True,
    sertakan_label_emosi: bool = False,
) -> str:
    daftar_transkrip: List[Dict[str, str]] = data_verbatim.get("transkrip", [])
    if not daftar_transkrip:
        raise ValueError(
            "Field 'transkrip' pada file verbatim.json kosong atau tidak "
            "ditemukan. Periksa kembali format file input Anda."
        )
    baris_narasi: List[str] = []
    for baris in daftar_transkrip:
        teks_ucapan = baris.get("teks", "").strip()
        nama_speaker = baris.get("speaker", "Tidak diketahui")
        label_emosi = baris.get("emosi", "")
        if not teks_ucapan:
            continue
        prefix = ""
        if sertakan_nama_speaker:
            if sertakan_label_emosi and label_emosi:
                prefix = f"{nama_speaker} [isyarat suara: {label_emosi}]: "
            else:
                prefix = f"{nama_speaker}: "
        baris_narasi.append(f"{prefix}{teks_ucapan}")
    return "\n".join(baris_narasi)


def ekstrak_id_sesi(data_verbatim: Dict[str, Any]) -> str:
    return data_verbatim.get("id_sesi", "SESI-TIDAK-DIKETAHUI")


# Aliases for backward compatibility with TDD tests
load_verbatim_file = muat_file_verbatim
merge_transkrip_to_narrative = gabungkan_transkrip_menjadi_narasi
