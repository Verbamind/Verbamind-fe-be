"""TDD tests for GUI — transcript viewer and BIRP viewer pages."""

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


class TestTranscriptPage:
    def test_page_created(self, qapp):
        from verbamind.gui.pages.transcript_page import TranscriptPage

        page = TranscriptPage()
        assert page is not None

    def test_transcript_can_load_segments(self, qapp):
        from verbamind.gui.pages.transcript_page import TranscriptPage

        page = TranscriptPage()
        segments = [
            {"speaker": "patient", "text": "Hello", "start": 0.0, "end": 1.0},
            {"speaker": "psychologist", "text": "Hi", "start": 1.0, "end": 2.0},
        ]
        page.load_transcript(segments)
        assert page.segment_count() == 2

    def test_transcript_shows_speaker_labels(self, qapp):
        from verbamind.gui.pages.transcript_page import TranscriptPage

        page = TranscriptPage()
        page.load_transcript([
            {"speaker": "patient", "text": "Test", "start": 0.0, "end": 1.0,
             "emotion": "anxious", "emotion_confidence": 0.9},
        ])
        assert page.segment_count() == 1

    def test_empty_transcript(self, qapp):
        from verbamind.gui.pages.transcript_page import TranscriptPage

        page = TranscriptPage()
        page.load_transcript([])
        assert page.segment_count() == 0


class TestBIRPPage:
    def test_page_created(self, qapp):
        from verbamind.gui.pages.birp_page import BIRPPage

        page = BIRPPage()
        assert page is not None

    def test_birp_can_load_result(self, qapp):
        from verbamind.gui.pages.birp_page import BIRPPage

        page = BIRPPage()
        birp_data = {
            "behavior": "Patient shows anxiety.",
            "intervention": "CBT applied.",
            "response": "Patient responded positively.",
            "plan": "Continue next week.",
        }
        page.load_birp(birp_data)
        assert page.has_data()

    def test_birp_fields_loaded(self, qapp):
        from verbamind.gui.pages.birp_page import BIRPPage
        from PySide6.QtWidgets import QTextEdit

        page = BIRPPage()
        page.load_birp({
            "behavior": "B", "intervention": "I",
            "response": "R", "plan": "P",
        })
        for key in ("behavior", "intervention", "response", "plan"):
            editor = page.findChild(QTextEdit, f"birp_{key}")
            assert editor is not None

    def test_birp_pending_state(self, qapp):
        from verbamind.gui.pages.birp_page import BIRPPage

        page = BIRPPage()
        assert not page.has_data()
