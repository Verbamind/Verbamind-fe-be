"""Filesystem-safe identifier sanitizer (security-critical).

Session IDs flow from user-controlled API input straight into filenames, e.g.
`BIRPGenerator._save` builds `f"BIRP_{session_id}_{ts}.json"`. A hostile value
such as `..\\..\\evil` would escape the output directory (path traversal). This
module guarantees the produced fragment is safe to interpolate into a path:

  * non-empty
  * only [A-Za-z0-9_-]
  * never a path separator, never a leading/trailing dot or space
  * never a Windows reserved device name (CON, COM1..9, LPT1..9, ...)
  * bounded length (MAX_LENGTH)
"""

DEFAULT_FALLBACK = "SESI"
MAX_LENGTH = 100

_ALLOWED = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)

WINDOWS_RESERVED = frozenset(
    ["CON", "PRN", "AUX", "NUL"]
    + [f"COM{i}" for i in range(1, 10)]
    + [f"LPT{i}" for i in range(1, 10)]
)


def _clean(value) -> str:
    """Map *value* to an allowed-charset string, collapsing bad runs to '_'."""
    if value is None:
        return ""
    out = []
    prev_underscore = False
    for ch in str(value):
        if ch in _ALLOWED:
            out.append(ch)
            prev_underscore = False
        elif out and not prev_underscore:
            out.append("_")
            prev_underscore = True
    return "".join(out).strip("_")


def sanitize_filename_part(value, fallback: str = DEFAULT_FALLBACK) -> str:
    """Return a filesystem-safe fragment derived from *value*.

    Guarantees a non-empty result containing only [A-Za-z0-9_-], never a
    Windows reserved device name, and never longer than MAX_LENGTH.
    """
    cleaned = _clean(value)
    if not cleaned:
        cleaned = _clean(fallback)
    if not cleaned:
        cleaned = DEFAULT_FALLBACK

    if cleaned.upper() in WINDOWS_RESERVED:
        cleaned = cleaned + "_"

    if len(cleaned) > MAX_LENGTH:
        cleaned = cleaned[:MAX_LENGTH].rstrip("_")

    return cleaned
