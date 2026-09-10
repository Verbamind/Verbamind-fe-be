"""TDD tests for the session-id / filename sanitizer (security-critical).

RED phase: `verbamind.security.filename_sanitizer` does not exist yet, so the
import below fails until the GREEN phase.

Motivation: session IDs flow from user-controlled API input (e.g.
`POST /api/v1/birp/generate` → `session_id`) straight into a filename in
`BIRPGenerator._save`: `f"BIRP_{session_id}_{ts}.json"`. A hostile value such
as `..\\..\\evil` would escape the output directory (path traversal). The
sanitizer guarantees the produced fragment is filesystem-safe:
  * non-empty
  * only [A-Za-z0-9_-]
  * never a path separator, never a leading/trailing dot
  * never a Windows reserved device name
  * bounded length
"""

import re

from verbamind.security.filename_sanitizer import (
    MAX_LENGTH,
    WINDOWS_RESERVED,
    sanitize_filename_part,
)


class TestSanitizeBasics:
    def test_none_returns_fallback(self):
        assert sanitize_filename_part(None) == "SESI"

    def test_empty_string_returns_fallback(self):
        assert sanitize_filename_part("") == "SESI"

    def test_whitespace_only_returns_fallback(self):
        assert sanitize_filename_part("   \t  ") == "SESI"

    def test_all_disallowed_chars_returns_fallback(self):
        assert sanitize_filename_part("!!!///\\\\") == "SESI"

    def test_plain_id_unchanged(self):
        assert sanitize_filename_part("SES-1") == "SES-1"

    def test_db_id_unchanged(self):
        assert sanitize_filename_part("DB-123") == "DB-123"

    def test_underscore_preserved(self):
        assert sanitize_filename_part("SES_1") == "SES_1"

    def test_non_string_coerced(self):
        assert sanitize_filename_part(123) == "123"

    def test_custom_fallback(self):
        assert sanitize_filename_part("", fallback="X") == "X"

    def test_empty_custom_fallback_coerces_to_default(self):
        assert sanitize_filename_part("", fallback="") == "SESI"

    def test_disallowed_custom_fallback_coerces_to_default(self):
        assert sanitize_filename_part("!!!", fallback="@@@") == "SESI"


class TestPathTraversalNeutralization:
    def test_forward_slash_removed(self):
        assert sanitize_filename_part("a/b") == "a_b"

    def test_backslash_removed(self):
        assert sanitize_filename_part("a\\b") == "a_b"

    def test_parent_traversal_neutralized(self):
        assert sanitize_filename_part("..\\..\\evil") == "evil"

    def test_unix_traversal_neutralized(self):
        assert sanitize_filename_part("../etc/passwd") == "etc_passwd"

    def test_absolute_windows_path_neutralized(self):
        assert sanitize_filename_part("C:\\Users\\x") == "C_Users_x"

    def test_dots_removed(self):
        assert "." not in sanitize_filename_part("a.b.c")


class TestReservedNames:
    def test_windows_reserved_con(self):
        assert sanitize_filename_part("CON") == "CON_"

    def test_windows_reserved_com1(self):
        assert sanitize_filename_part("COM1") == "COM1_"

    def test_windows_reserved_lpt9(self):
        assert sanitize_filename_part("LPT9") == "LPT9_"

    def test_reserved_case_insensitive(self):
        assert sanitize_filename_part("con") == "con_"

    def test_no_reserved_name_passes_through(self):
        for name in WINDOWS_RESERVED:
            out = sanitize_filename_part(name)
            assert out.upper() not in WINDOWS_RESERVED


class TestLengthAndBounds:
    def test_long_input_truncated(self):
        out = sanitize_filename_part("A" * 500)
        assert len(out) <= MAX_LENGTH
        assert len(out) == MAX_LENGTH

    def test_max_length_constant_reasonable(self):
        assert MAX_LENGTH >= 1
        assert MAX_LENGTH <= 255


class TestInvariants:
    """Property-style checks across a corpus of hostile inputs."""

    HOSTILE = [
        "..",
        "..\\..\\",
        "/etc/passwd",
        "C:\\Windows\\System32\\cmd.exe",
        "a/b\\c",
        "con",
        "CON",
        "COM1",
        "LPT1",
        "NUL",
        "prn.txt",
        "  leading and trailing  ",
        "unicode-émoji😀",
        "a" * 300,
        "...",
        "\\",
        "/",
        "",
        "   ",
        "SES-1",
        "DB-123",
    ]

    def test_output_matches_safe_charset(self):
        for value in self.HOSTILE:
            out = sanitize_filename_part(value)
            assert re.fullmatch(r"[A-Za-z0-9_-]+", out), f"{value!r} -> {out!r}"

    def test_never_empty(self):
        for value in self.HOSTILE:
            assert sanitize_filename_part(value) != ""

    def test_never_starts_with_dot(self):
        for value in self.HOSTILE:
            assert not sanitize_filename_part(value).startswith(".")

    def test_never_ends_with_dot_or_space(self):
        for value in self.HOSTILE:
            out = sanitize_filename_part(value)
            assert not out.endswith(".")
            assert not out.endswith(" ")

    def test_deterministic(self):
        for value in self.HOSTILE:
            assert sanitize_filename_part(value) == sanitize_filename_part(value)


class TestBIRPOutputSanitization:
    """Integration — BIRPGenerator._save must stay inside output_dir."""

    def test_save_sanitizes_hostile_session_id(self, tmp_path):
        from verbamind.backend.ai_pipeline.birp_generator import BIRPGenerator

        output_dir = tmp_path / "output"
        gen = BIRPGenerator(retriever=None, llm=None, output_dir=str(output_dir))

        birp = {
            "behavior": "B",
            "intervention": "I",
            "response": "R",
            "plan": "P",
        }
        path = gen._save("..\\..\\evil", birp)

        resolved_output = output_dir.resolve()
        assert resolved_output in path.resolve().parents
        assert path.exists()
        assert path.name.startswith("BIRP_")
        assert path.name.endswith(".json")

    def test_save_plain_session_id_unchanged(self, tmp_path):
        from verbamind.backend.ai_pipeline.birp_generator import BIRPGenerator

        output_dir = tmp_path / "output"
        gen = BIRPGenerator(retriever=None, llm=None, output_dir=str(output_dir))

        path = gen._save("SES-1", {"behavior": "B"})

        assert output_dir.resolve() in path.resolve().parents
        assert "SES-1" in path.name
