"""TDD tests for BIRP generation pipeline — Qwen2.5 LLM + RAG integration.

Tests cover:
1. Verbatim parser (from Verbamind_RAG json_parser.py)
2. BIRP prompt templates
3. LLM wrapper (Qwen2.5 via Ollama)
4. RAG retriever (FAISS)
5. BIRP generator (combined RAG + LLM pipeline)
6. Knowledge ingest (FAISS build)
7. BIRP router API

RED phase: tests defined, imports will fail since modules don't exist yet.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_dir():
    """Temporary directory for file-based tests."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def sample_merged_verbatim():
    """Sample merged verbatim segments ready for BIRP generation."""
    return [
        {
            "speaker": "psychologist",
            "text": "Selamat pagi, bagaimana perasaan Anda hari ini?",
            "start": 0.0,
            "end": 3.0,
            "emotion": "calm",
            "emotion_confidence": 0.9,
        },
        {
            "speaker": "patient",
            "text": "Saya merasa cemas karena besok ada presentasi penting.",
            "start": 3.5,
            "end": 8.0,
            "emotion": "anxious",
            "emotion_confidence": 0.85,
        },
        {
            "speaker": "psychologist",
            "text": "Coba ceritakan lebih detail tentang kecemasan itu.",
            "start": 9.0,
            "end": 12.0,
            "emotion": "calm",
            "emotion_confidence": 0.9,
        },
        {
            "speaker": "patient",
            "text": "Saya takut gagal dan mengecewakan orang lain. Jantung saya berdebar kencang.",
            "start": 13.0,
            "end": 18.0,
            "emotion": "fearful",
            "emotion_confidence": 0.92,
        },
    ]


@pytest.fixture
def sample_verbatim_json():
    """Sample verbatim.json content matching Verbamind_RAG format."""
    return {
        "id_sesi": "SESI-001",
        "transkrip": [
            {"speaker": "Psikolog", "teks": "Selamat pagi, bagaimana perasaan Anda hari ini?", "emosi": "Tenang"},
            {"speaker": "Pasien", "teks": "Saya merasa cemas karena besok ada presentasi penting.", "emosi": "Cemas"},
            {"speaker": "Psikolog", "teks": "Coba ceritakan lebih detail tentang kecemasan itu.", "emosi": "Tenang"},
            {"speaker": "Pasien", "teks": "Saya takut gagal dan mengecewakan orang lain.", "emosi": "Takut"},
        ],
    }


@pytest.fixture
def sample_knowledge_text():
    """Sample knowledge base text for ingestion."""
    return """PEDOMAN KODE ETIK PSIKOLOGI INDONESIA

1. Prinsip Penghormatan terhadap Martabat Manusia
Psikolog wajib menghormati martabat setiap individu tanpa diskriminasi apapun.

2. Prinsip Kerahasiaan
Psikolog wajib menjaga kerahasiaan seluruh informasi yang diperoleh selama proses konseling.

3. Prinsip Tanggung Jawab Profesional
Psikolog wajib memberikan layanan sesuai dengan kompetensi dan keahlian yang dimiliki.

TERAPI KOGNITIF-PERILAKU (CBT)

CBT menggunakan teknik restrukturisasi kognitif untuk mengidentifikasi dan mengubah pola pikir negatif.
Teknik utama meliputi:
- Identifikasi pikiran otomatis negatif
- Pemeriksaan bukti untuk dan melawan kepercayaan tersebut
- Pengembangan perspektif alternatif yang lebih seimbang
- Penugasan pekerjaan rumah (homework)

Untuk kecemasan presentasi, teknik eksposur bertahap dan relaksasi sering digunakan."""


# ---------------------------------------------------------------------------
# 1. Verbatim Parser Tests (from Verbamind_RAG json_parser.py)
# ---------------------------------------------------------------------------


class TestVerbatimParser:
    """Tests for the verbatim JSON parser — adapted from Verbamind_RAG."""

    def test_load_verbatim_file_success(self, temp_dir, sample_verbatim_json):
        """Should parse a valid verbatim.json into a dict."""
        file_path = temp_dir / "verbatim.json"
        file_path.write_text(json.dumps(sample_verbatim_json, ensure_ascii=False), encoding="utf-8")

        from verbamind.backend.ai_pipeline.rag.verbatim_parser import load_verbatim_file

        data = load_verbatim_file(str(file_path))
        assert isinstance(data, dict)
        assert "id_sesi" in data
        assert "transkrip" in data

    def test_load_verbatim_file_not_found(self):
        """Should raise FileNotFoundError for missing files."""
        from verbamind.backend.ai_pipeline.rag.verbatim_parser import load_verbatim_file

        with pytest.raises(FileNotFoundError):
            load_verbatim_file("nonexistent/file.json")

    def test_merge_transkrip_to_narrative_with_speakers(self, sample_verbatim_json):
        """Should merge transcript entries into a narrative with speaker labels."""
        from verbamind.backend.ai_pipeline.rag.verbatim_parser import merge_transkrip_to_narrative

        narrative = merge_transkrip_to_narrative(sample_verbatim_json, include_speaker=True)
        assert "Psikolog:" in narrative
        assert "Pasien:" in narrative
        assert "Selamat pagi" in narrative
        assert "Saya merasa cemas" in narrative

    def test_merge_transkrip_to_narrative_without_speakers(self, sample_verbatim_json):
        """Should merge transcript entries into plain narrative without speakers."""
        from verbamind.backend.ai_pipeline.rag.verbatim_parser import merge_transkrip_to_narrative

        narrative = merge_transkrip_to_narrative(sample_verbatim_json, include_speaker=False)
        assert "Psikolog:" not in narrative
        assert "Pasien:" not in narrative
        assert "Selamat pagi" in narrative

    def test_merge_transkrip_to_narrative_with_emotions(self, sample_verbatim_json):
        """Should include emotion labels in narrative when requested."""
        from verbamind.backend.ai_pipeline.rag.verbatim_parser import merge_transkrip_to_narrative

        narrative = merge_transkrip_to_narrative(
            sample_verbatim_json, include_speaker=True, include_emotion=True
        )
        assert "Pasien (Cemas):" in narrative
        assert "Pasien (Takut):" in narrative

    def test_merge_transkrip_empty_list(self):
        """Should raise ValueError for empty transcript list."""
        from verbamind.backend.ai_pipeline.rag.verbatim_parser import merge_transkrip_to_narrative

        with pytest.raises(ValueError):
            merge_transkrip_to_narrative({"id_sesi": "TEST", "transkrip": []})

    def test_merge_transkrip_skips_empty_text(self, sample_verbatim_json):
        """Should skip transcript entries with empty text."""
        data = {
            "id_sesi": "TEST",
            "transkrip": [
                {"speaker": "Psikolog", "teks": "Halo", "emosi": ""},
                {"speaker": "Pasien", "teks": "", "emosi": ""},
                {"speaker": "Psikolog", "teks": "Selamat tinggal", "emosi": ""},
            ],
        }
        from verbamind.backend.ai_pipeline.rag.verbatim_parser import merge_transkrip_to_narrative

        narrative = merge_transkrip_to_narrative(data, include_speaker=False)
        assert "Halo" in narrative
        assert "Selamat tinggal" in narrative

    def test_extract_session_id(self, sample_verbatim_json):
        """Should extract session ID from verbatim data."""
        from verbamind.backend.ai_pipeline.rag.verbatim_parser import extract_session_id

        session_id = extract_session_id(sample_verbatim_json)
        assert session_id == "SESI-001"

    def test_extract_session_id_missing(self):
        """Should return fallback when session ID is missing."""
        from verbamind.backend.ai_pipeline.rag.verbatim_parser import extract_session_id

        session_id = extract_session_id({"transkrip": []})
        assert session_id == "SESI-TIDAK-DIKETAHUI"


# ---------------------------------------------------------------------------
# 2. BIRP Prompt Template Tests
# ---------------------------------------------------------------------------


class TestBIRPPrompt:
    """Tests for the BIRP prompt template generation."""

    def test_build_system_prompt_structure(self):
        """Should produce a system prompt containing BIRP instructions."""
        from verbamind.backend.ai_pipeline.prompts.birp_prompt import build_system_prompt

        context = "Referensi: Kode Etik Psikologi"
        narrative = "Psikolog: Halo\nPasien: Saya cemas"
        prompt = build_system_prompt(context, narrative)

        assert "Verbamind" in prompt
        assert "behavior" in prompt
        assert "intervention" in prompt
        assert "response" in prompt
        assert "plan" in prompt
        assert context in prompt
        assert narrative in prompt

    def test_build_system_prompt_contains_json_instruction(self):
        """Should instruct JSON output format."""
        from verbamind.backend.ai_pipeline.prompts.birp_prompt import build_system_prompt

        prompt = build_system_prompt("konteks", "narasi")
        assert "JSON" in prompt

    def test_build_system_prompt_indonesian(self):
        """Should use Indonesian language instructions."""
        from verbamind.backend.ai_pipeline.prompts.birp_prompt import build_system_prompt

        prompt = build_system_prompt("konteks", "narasi")
        assert "Anda adalah" in prompt

    def test_build_system_prompt_empty_context(self):
        """Should handle empty context gracefully."""
        from verbamind.backend.ai_pipeline.prompts.birp_prompt import build_system_prompt

        prompt = build_system_prompt("", "narasi transkrip")
        # Empty context placeholder should still be included
        assert "narasi transkrip" in prompt

    def test_default_prompt_exists(self):
        """Should have a default prompt template accessible."""
        from verbamind.backend.ai_pipeline.prompts.birp_prompt import SYSTEM_PROMPT_TEMPLATE

        assert isinstance(SYSTEM_PROMPT_TEMPLATE, str)
        assert len(SYSTEM_PROMPT_TEMPLATE) > 100


# ---------------------------------------------------------------------------
# 3. LLM Wrapper Tests (Qwen2.5 via Ollama)
# ---------------------------------------------------------------------------


class TestLLMWrapper:
    """Tests for the Qwen2.5 LLM wrapper."""

    def test_llm_wrapper_exists(self):
        """Should be importable."""
        from verbamind.backend.ai_pipeline.llm import LLMWrapper

        assert LLMWrapper is not None

    def test_llm_wrapper_has_generate_method(self):
        """Should expose a generate method."""
        from verbamind.backend.ai_pipeline.llm import LLMWrapper

        llm = LLMWrapper(base_url="http://localhost:11434", model="qwen2.5:7b-instruct")
        assert hasattr(llm, "generate")
        assert callable(llm.generate)

    def test_llm_wrapper_has_generate_json_method(self):
        """Should expose a generate_json method for structured output."""
        from verbamind.backend.ai_pipeline.llm import LLMWrapper

        llm = LLMWrapper(base_url="http://localhost:11434", model="qwen2.5:7b-instruct")
        assert hasattr(llm, "generate_json")
        assert callable(llm.generate_json)

    @patch("verbamind.backend.ai_pipeline.llm.ChatOllama")
    def test_generate_calls_ollama(self, mock_chat_ollama):
        """Should call the Ollama API via ChatOllama."""
        from verbamind.backend.ai_pipeline.llm import LLMWrapper

        mock_instance = MagicMock()
        mock_instance.invoke.return_value.content = '{"behavior": "test"}'
        mock_chat_ollama.return_value = mock_instance

        llm = LLMWrapper(base_url="http://localhost:11434", model="qwen2.5:7b-instruct")
        result = llm.generate("Test prompt")

        assert mock_instance.invoke.called
        assert result == '{"behavior": "test"}'

    @patch("verbamind.backend.ai_pipeline.llm.ChatOllama")
    def test_generate_json_parses_output(self, mock_chat_ollama):
        """Should parse JSON output into a dictionary."""
        from verbamind.backend.ai_pipeline.llm import LLMWrapper

        mock_instance = MagicMock()
        mock_instance.invoke.return_value.content = '{"key": "value"}'
        mock_chat_ollama.return_value = mock_instance

        llm = LLMWrapper(base_url="http://localhost:11434", model="qwen2.5:7b-instruct")
        result = llm.generate_json("Test prompt")

        assert isinstance(result, dict)
        assert result == {"key": "value"}

    @patch("verbamind.backend.ai_pipeline.llm.ChatOllama")
    def test_generate_json_invalid_output_raises(self, mock_chat_ollama):
        """Should raise on invalid JSON output."""
        from verbamind.backend.ai_pipeline.llm import LLMWrapper

        mock_instance = MagicMock()
        mock_instance.invoke.return_value.content = "not json at all"
        mock_chat_ollama.return_value = mock_instance

        llm = LLMWrapper(base_url="http://localhost:11434", model="qwen2.5:7b-instruct")
        with pytest.raises((ValueError, json.JSONDecodeError)):
            llm.generate_json("Test prompt")

    def test_llm_default_values(self):
        """Should have sensible defaults."""
        from verbamind.backend.ai_pipeline.llm import LLMWrapper

        llm = LLMWrapper()
        assert llm.base_url == "http://localhost:11434"
        assert llm.model == "qwen2.5:7b-instruct"
        assert llm.temperature == 0.3


# ---------------------------------------------------------------------------
# 4. RAG Retriever Tests
# ---------------------------------------------------------------------------


class TestRAGRetriever:
    """Tests for the FAISS-based RAG retriever."""

    def test_retriever_exists(self):
        """Should be importable."""
        from verbamind.backend.ai_pipeline.rag.retriever import RAGRetriever

        assert RAGRetriever is not None

    @patch("verbamind.backend.ai_pipeline.rag.retriever.HuggingFaceEmbeddings")
    @patch("verbamind.backend.ai_pipeline.rag.retriever.FAISS")
    def test_retrieve_returns_context_string(self, mock_faiss, mock_embeddings, temp_dir):
        """Should return a context string from FAISS search."""
        from verbamind.backend.ai_pipeline.rag.retriever import RAGRetriever

        # Setup mocks
        mock_embedding_instance = MagicMock()
        mock_embeddings.return_value = mock_embedding_instance

        mock_faiss_instance = MagicMock()
        mock_doc = MagicMock()
        mock_doc.page_content = "Sample knowledge base text content."
        mock_doc.metadata = {"source": "test.txt"}
        mock_faiss_instance.similarity_search.return_value = [mock_doc]
        mock_faiss.load_local.return_value = mock_faiss_instance

        index_dir = temp_dir / "faiss_index"
        index_dir.mkdir()
        (index_dir / "index.faiss").write_text("dummy")  # so iterdir() returns non-empty

        retriever = RAGRetriever(index_path=str(index_dir))
        context = retriever.retrieve("Test query")

        assert isinstance(context, str)
        assert "Sample knowledge base" in context
        mock_faiss_instance.similarity_search.assert_called_once()

    @patch("verbamind.backend.ai_pipeline.rag.retriever.HuggingFaceEmbeddings")
    @patch("verbamind.backend.ai_pipeline.rag.retriever.FAISS")
    def test_retrieve_empty_results(self, mock_faiss, mock_embeddings, temp_dir):
        """Should handle empty FAISS results gracefully."""
        from verbamind.backend.ai_pipeline.rag.retriever import RAGRetriever

        mock_embedding_instance = MagicMock()
        mock_embeddings.return_value = mock_embedding_instance

        mock_faiss_instance = MagicMock()
        mock_faiss_instance.similarity_search.return_value = []
        mock_faiss.load_local.return_value = mock_faiss_instance

        index_dir = temp_dir / "faiss_index"
        index_dir.mkdir()
        (index_dir / "index.faiss").write_text("dummy")

        retriever = RAGRetriever(index_path=str(index_dir))
        context = retriever.retrieve("Test query")

        assert isinstance(context, str)
        # Should return a fallback message, not empty
        assert len(context) > 0

    @patch("verbamind.backend.ai_pipeline.rag.retriever.HuggingFaceEmbeddings")
    @patch("verbamind.backend.ai_pipeline.rag.retriever.FAISS")
    def test_retrieve_respects_k_documents(self, mock_faiss, mock_embeddings, temp_dir):
        """Should respect the k parameter for number of documents."""
        from verbamind.backend.ai_pipeline.rag.retriever import RAGRetriever

        mock_embedding_instance = MagicMock()
        mock_embeddings.return_value = mock_embedding_instance

        mock_faiss_instance = MagicMock()
        mock_doc = MagicMock()
        mock_doc.page_content = "Test content"
        mock_doc.metadata = {"source": "test.txt"}
        mock_faiss_instance.similarity_search.return_value = [mock_doc] * 3
        mock_faiss.load_local.return_value = mock_faiss_instance

        index_dir = temp_dir / "faiss_index"
        index_dir.mkdir()
        (index_dir / "index.faiss").write_text("dummy")

        retriever = RAGRetriever(index_path=str(index_dir))
        retriever.retrieve("query", k=3)

        assert mock_faiss_instance.similarity_search.call_args[1]["k"] == 3

    def test_retriever_index_not_found(self, temp_dir):
        """Should raise a clear error when FAISS index is missing."""
        from verbamind.backend.ai_pipeline.rag.retriever import RAGRetriever

        retriever = RAGRetriever(index_path=str(temp_dir / "nonexistent"))
        with pytest.raises(FileNotFoundError):
            retriever.retrieve("query")

    def test_retriever_uses_multilingual_embedding(self):
        """Should use the multilingual embedding model for Indonesian."""
        from verbamind.backend.ai_pipeline.rag.retriever import RAGRetriever, EMBEDDING_MODEL_NAME

        assert "multilingual" in EMBEDDING_MODEL_NAME.lower()


# ---------------------------------------------------------------------------
# 5. BIRP Generator Tests (combined RAG + LLM pipeline)
# ---------------------------------------------------------------------------


class TestBIRPGenerator:
    """Tests for the BIRP generator that combines RAG and LLM."""

    def test_birp_generator_exists(self):
        """Should be importable."""
        from verbamind.backend.ai_pipeline.birp_generator import BIRPGenerator

        assert BIRPGenerator is not None

    @patch("verbamind.backend.ai_pipeline.birp_generator.LLMWrapper")
    @patch("verbamind.backend.ai_pipeline.birp_generator.RAGRetriever")
    def test_generate_birp_returns_valid_structure(
        self, mock_retriever_cls, mock_llm_cls, sample_merged_verbatim
    ):
        """Should return BIRP dict with all four required keys."""
        from verbamind.backend.ai_pipeline.birp_generator import BIRPGenerator

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = "Mock knowledge context"
        mock_retriever_cls.return_value = mock_retriever

        mock_llm = MagicMock()
        mock_llm.generate_json.return_value = {
            "behavior": "Klien tampak cemas",
            "intervention": "Psikolog menggunakan CBT",
            "response": "Klien merespons baik",
            "plan": "Lanjutkan sesi berikutnya",
        }
        mock_llm_cls.return_value = mock_llm

        generator = BIRPGenerator()
        result = generator.generate(sample_merged_verbatim)

        assert isinstance(result, dict)
        for key in ["behavior", "intervention", "response", "plan"]:
            assert key in result
            assert isinstance(result[key], str)
            assert len(result[key]) > 0

    @patch("verbamind.backend.ai_pipeline.birp_generator.LLMWrapper")
    @patch("verbamind.backend.ai_pipeline.birp_generator.RAGRetriever")
    def test_generate_birp_calls_retriever_with_verbatim_text(
        self, mock_retriever_cls, mock_llm_cls, sample_merged_verbatim
    ):
        """Should pass verbatim text as query to the RAG retriever."""
        from verbamind.backend.ai_pipeline.birp_generator import BIRPGenerator

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = "Mock context"
        mock_retriever_cls.return_value = mock_retriever

        mock_llm = MagicMock()
        mock_llm.generate_json.return_value = {
            "behavior": "OK", "intervention": "OK",
            "response": "OK", "plan": "OK",
        }
        mock_llm_cls.return_value = mock_llm

        generator = BIRPGenerator()
        generator.generate(sample_merged_verbatim)

        mock_retriever.retrieve.assert_called_once()

    @patch("verbamind.backend.ai_pipeline.birp_generator.LLMWrapper")
    @patch("verbamind.backend.ai_pipeline.birp_generator.RAGRetriever")
    def test_generate_birp_fills_missing_keys(
        self, mock_retriever_cls, mock_llm_cls, sample_merged_verbatim
    ):
        """Should fill missing BIRP keys with empty strings."""
        from verbamind.backend.ai_pipeline.birp_generator import BIRPGenerator

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = "Mock context"
        mock_retriever_cls.return_value = mock_retriever

        mock_llm = MagicMock()
        mock_llm.generate_json.return_value = {
            "behavior": "Only behavior",
            # missing intervention, response, plan
        }
        mock_llm_cls.return_value = mock_llm

        generator = BIRPGenerator()
        result = generator.generate(sample_merged_verbatim)

        assert result["behavior"] == "Only behavior"
        assert result["intervention"] == ""
        assert result["response"] == ""
        assert result["plan"] == ""

    @patch("verbamind.backend.ai_pipeline.birp_generator.LLMWrapper")
    @patch("verbamind.backend.ai_pipeline.birp_generator.RAGRetriever")
    def test_generate_birp_empty_verbatim_raises(
        self, mock_retriever_cls, mock_llm_cls
    ):
        """Should raise ValueError for empty verbatim."""
        from verbamind.backend.ai_pipeline.birp_generator import BIRPGenerator

        generator = BIRPGenerator()
        with pytest.raises(ValueError):
            generator.generate([])

    def test_verbatim_to_text_conversion(self, sample_merged_verbatim):
        """Should convert merged verbatim to a readable text format."""
        from verbamind.backend.ai_pipeline.birp_generator import BIRPGenerator

        generator = BIRPGenerator()
        text = generator._verbatim_to_text(sample_merged_verbatim)
        assert "Psychologist" in text
        assert "Patient" in text
        assert "presentasi" in text
        assert "cemas" in text.lower()


# ---------------------------------------------------------------------------
# 6. Knowledge Ingest Tests
# ---------------------------------------------------------------------------


class TestKnowledgeIngest:
    """Tests for the FAISS knowledge base ingestion."""

    @patch("verbamind.backend.ai_pipeline.rag.knowledge_ingest._check_dependencies")
    @patch("verbamind.backend.ai_pipeline.rag.knowledge_ingest.FAISS")
    @patch("verbamind.backend.ai_pipeline.rag.knowledge_ingest.HuggingFaceEmbeddings")
    @patch("verbamind.backend.ai_pipeline.rag.knowledge_ingest.RecursiveCharacterTextSplitter")
    @patch("verbamind.backend.ai_pipeline.rag.knowledge_ingest.TextLoader")
    def test_ingest_txt_files(
        self, mock_loader, mock_splitter, mock_embeddings, mock_faiss,
        mock_check_deps, temp_dir, sample_knowledge_text,
    ):
        """Should ingest .txt files from a directory and build FAISS index."""
        from verbamind.backend.ai_pipeline.rag.knowledge_ingest import ingest_knowledge_base

        # Setup mocks
        mock_doc = MagicMock()
        mock_loader.return_value.load.return_value = [mock_doc]
        mock_chunk = MagicMock()
        mock_splitter.return_value.split_documents.return_value = [mock_chunk]
        mock_embedding_instance = MagicMock()
        mock_embeddings.return_value = mock_embedding_instance
        mock_faiss_instance = MagicMock()
        mock_faiss.from_documents.return_value = mock_faiss_instance
        mock_check_deps.return_value = None

        kb_dir = temp_dir / "knowledge_base"
        kb_dir.mkdir()
        (kb_dir / "kode_etik.txt").write_text(sample_knowledge_text, encoding="utf-8")
        (kb_dir / "cbt.txt").write_text("Teknik CBT meliputi restrukturisasi kognitif.", encoding="utf-8")

        index_dir = temp_dir / "faiss_index"

        chunks_count = ingest_knowledge_base(
            knowledge_base_path=str(kb_dir),
            index_output_path=str(index_dir),
        )

        assert chunks_count > 0
        assert index_dir.exists()

    def test_ingest_empty_directory_raises(self, temp_dir):
        """Should raise error for empty knowledge base directory."""
        kb_dir = temp_dir / "knowledge_base"
        kb_dir.mkdir()

        from verbamind.backend.ai_pipeline.rag.knowledge_ingest import ingest_knowledge_base

        with pytest.raises(ValueError):
            ingest_knowledge_base(
                knowledge_base_path=str(kb_dir),
                index_output_path=str(temp_dir / "faiss_index"),
            )

    def test_ingest_missing_directory_raises(self, temp_dir):
        """Should raise error when knowledge base directory doesn't exist."""
        from verbamind.backend.ai_pipeline.rag.knowledge_ingest import ingest_knowledge_base

        with pytest.raises(FileNotFoundError):
            ingest_knowledge_base(
                knowledge_base_path=str(temp_dir / "does_not_exist"),
                index_output_path=str(temp_dir / "faiss_index"),
            )

    @patch("verbamind.backend.ai_pipeline.rag.knowledge_ingest._check_dependencies")
    @patch("verbamind.backend.ai_pipeline.rag.knowledge_ingest.FAISS")
    @patch("verbamind.backend.ai_pipeline.rag.knowledge_ingest.HuggingFaceEmbeddings")
    @patch("verbamind.backend.ai_pipeline.rag.knowledge_ingest.RecursiveCharacterTextSplitter")
    @patch("verbamind.backend.ai_pipeline.rag.knowledge_ingest.TextLoader")
    def test_ingest_skips_non_txt_files(
        self, mock_loader, mock_splitter, mock_embeddings, mock_faiss,
        mock_check_deps, temp_dir, sample_knowledge_text,
    ):
        """Should skip non-txt files in the knowledge base directory."""
        from verbamind.backend.ai_pipeline.rag.knowledge_ingest import ingest_knowledge_base

        # Setup mocks
        mock_doc = MagicMock()
        mock_loader.return_value.load.return_value = [mock_doc]
        mock_chunk = MagicMock()
        mock_splitter.return_value.split_documents.return_value = [mock_chunk]
        mock_embedding_instance = MagicMock()
        mock_embeddings.return_value = mock_embedding_instance
        mock_faiss_instance = MagicMock()
        mock_faiss.from_documents.return_value = mock_faiss_instance
        mock_check_deps.return_value = None

        kb_dir = temp_dir / "knowledge_base"
        kb_dir.mkdir()
        (kb_dir / "valid.txt").write_text(sample_knowledge_text, encoding="utf-8")
        (kb_dir / "image.png").write_text("not real png", encoding="utf-8")

        index_dir = temp_dir / "faiss_index"

        # Should not crash on non-txt files
        chunks_count = ingest_knowledge_base(
            knowledge_base_path=str(kb_dir),
            index_output_path=str(index_dir),
        )
        assert chunks_count > 0

    def test_ingest_dependency_check_fails(self, temp_dir, sample_knowledge_text):
        """Should raise ImportError when langchain dependencies are missing."""
        from verbamind.backend.ai_pipeline.rag.knowledge_ingest import ingest_knowledge_base, _check_dependencies

        kb_dir = temp_dir / "knowledge_base"
        kb_dir.mkdir()
        (kb_dir / "test.txt").write_text(sample_knowledge_text, encoding="utf-8")

        with patch("verbamind.backend.ai_pipeline.rag.knowledge_ingest._check_dependencies") as mock_check:
            mock_check.side_effect = ImportError("langchain not found")
            with pytest.raises(ImportError, match="langchain not found"):
                ingest_knowledge_base(
                    knowledge_base_path=str(kb_dir),
                    index_output_path=str(temp_dir / "faiss_index"),
                )


# ---------------------------------------------------------------------------
# 7. BIRP Router API Tests
# ---------------------------------------------------------------------------


class TestBIRPAPI:
    """Tests for the BIRP generation API endpoint."""

    def test_router_exists(self):
        """Should be importable and have routes registered."""
        from verbamind.backend.api.birp_router import router

        assert router is not None
        routes = [r.path for r in router.routes]
        assert "/api/v1/birp/generate" in routes

    def test_generate_endpoint_exists(self):
        """The generate endpoint should be registered."""
        from verbamind.backend.api.birp_router import generate_birp

        assert callable(generate_birp)

    def test_router_accepts_verbatim_payload(self):
        """Should define a request model for the generate endpoint."""
        from verbamind.backend.api.birp_router import BIRPRequest

        req = BIRPRequest(
            session_id="SESI-001",
            merged_verbatim=[
                {"speaker": "patient", "text": "Hello", "start": 0.0, "end": 1.0, "emotion": "neutral", "emotion_confidence": 0.8},
            ],
        )
        assert req.session_id == "SESI-001"
        assert len(req.merged_verbatim) == 1

    def test_birp_request_validation_empty_verbatim(self):
        """Should reject empty merged_verbatim."""
        from verbamind.backend.api.birp_router import BIRPRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            BIRPRequest(session_id="TEST", merged_verbatim=[])

    @patch("verbamind.backend.api.birp_router.BIRPGenerator")
    def test_endpoint_returns_200_on_success(self, mock_generator_cls):
        """Should return 200 with BIRP data on successful generation."""
        from fastapi.testclient import TestClient
        from verbamind.backend.api.birp_router import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        mock_generator = MagicMock()
        mock_generator.generate.return_value = {
            "behavior": "Test behavior",
            "intervention": "Test intervention",
            "response": "Test response",
            "plan": "Test plan",
        }
        mock_generator_cls.return_value = mock_generator

        response = client.post("/api/v1/birp/generate", json={
            "session_id": "SESI-001",
            "merged_verbatim": [
                {"speaker": "patient", "text": "Hello", "start": 0.0, "end": 1.0, "emotion": "neutral"},
            ],
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["birp"]["behavior"] == "Test behavior"

    @patch("verbamind.backend.api.birp_router.BIRPGenerator")
    def test_endpoint_returns_422_on_empty_verbatim(self, mock_generator_cls):
        """Should return 422 when merged_verbatim is empty."""
        from fastapi.testclient import TestClient
        from verbamind.backend.api.birp_router import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        mock_generator = MagicMock()
        mock_generator.generate.side_effect = ValueError("kosong")
        mock_generator_cls.return_value = mock_generator

        response = client.post("/api/v1/birp/generate", json={
            "session_id": "SESI-001",
            "merged_verbatim": [
                {"speaker": "patient", "text": "Hello", "start": 0.0, "end": 1.0, "emotion": "neutral"},
            ],
        })

        assert response.status_code == 422

    @patch("verbamind.backend.api.birp_router.BIRPGenerator")
    def test_endpoint_returns_500_on_internal_error(self, mock_generator_cls):
        """Should return 500 when BIRP generation crashes."""
        from fastapi.testclient import TestClient
        from verbamind.backend.api.birp_router import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        mock_generator = MagicMock()
        mock_generator.generate.side_effect = RuntimeError("Something broke")
        mock_generator_cls.return_value = mock_generator

        response = client.post("/api/v1/birp/generate", json={
            "session_id": "SESI-001",
            "merged_verbatim": [
                {"speaker": "patient", "text": "Hello", "start": 0.0, "end": 1.0, "emotion": "neutral"},
            ],
        })

        assert response.status_code == 500
        assert "failed" in response.json()["detail"].lower()
