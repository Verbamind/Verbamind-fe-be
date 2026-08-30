"""Label Bahasa Indonesia untuk kategori isyarat non-verbal suara.

Kategori berasal dari Verbamind_SpeechToNonverbalInformation
(loudness + pitch via fuzzy inference): Very Low / Low / No Significant Change /
High / Very High, plus Unvoiced untuk pitch.
"""

NONVERBAL_LABELS = {
    "Very Low": "Sangat Rendah",
    "Low": "Rendah",
    "No Significant Change": "Tidak Signifikan",
    "High": "Tinggi",
    "Very High": "Sangat Tinggi",
    "Unvoiced": "Tanpa Suara",
}


def nonverbal_label(category) -> str:
    """Petakan kategori isyarat non-verbal ke Bahasa Indonesia.

    Kategori yang tidak dikenal dikembalikan apa adanya; kosong → "—".
    """
    if not category:
        return "—"
    return NONVERBAL_LABELS.get(str(category), str(category))
