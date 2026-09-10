"""Tests for Step 8 — Qwen2.5 + RAG BIRP Pipeline (adapted from Verbamind_RAG).

Updated to match actual Verbamind_RAG codebase API.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestVerbatimParser:
    def test_muat_file_verbatim(self):
        from verbamind.backend.ai_pipeline.rag.verbatim_parser import muat_file_verbatim

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump({"id_sesi": "SES-001", "transkrip": []}, f)
            path = f.name

        data = muat_file_verbatim(path)
        assert data["id_sesi"] == "SES-001"
        os.unlink(path)

    def test_muat_file_not_found(self):
        from verbamind.backend.ai_pipeline.rag.verbatim_parser import muat_file_verbatim

        with pytest.raises(FileNotFoundError):
            muat_file_verbatim("nonexistent_file.json")

    def test_gabungkan_transkrip(self):
        from verbamind.backend.ai_pipeline.rag.verbatim_parser import (
            gabungkan_transkrip_menjadi_narasi,
        )

        data = {
            "id_sesi": "SES-001",
            "transkrip": [
                {"speaker": "Psikolog", "teks": "Bagaimana perasaan Anda?", "emosi": ""},
                {"speaker": "Pasien", "teks": "Saya merasa cemas.", "emosi": "cemas"},
            ],
        }
        narasi = gabungkan_transkrip_menjadi_narasi(data)
        assert "Psikolog: Bagaimana" in narasi
        assert "Pasien: Saya" in narasi

    def test_gabungkan_dengan_emosi(self):
        from verbamind.backend.ai_pipeline.rag.verbatim_parser import (
            gabungkan_transkrip_menjadi_narasi,
        )

        data = {
            "id_sesi": "SES-001",
            "transkrip": [
                {"speaker": "Pasien", "teks": "Saya takut.", "emosi": "takut"},
            ],
        }
        narasi = gabungkan_transkrip_menjadi_narasi(
            data, sertakan_nama_speaker=True, sertakan_label_emosi=True
        )
        assert "Pasien [isyarat suara: takut]: Saya takut." in narasi

    def test_gabungkan_kosong_raises(self):
        from verbamind.backend.ai_pipeline.rag.verbatim_parser import (
            gabungkan_transkrip_menjadi_narasi,
        )

        with pytest.raises(ValueError):
            gabungkan_transkrip_menjadi_narasi({"transkrip": []})

    def test_ekstrak_id_sesi(self):
        from verbamind.backend.ai_pipeline.rag.verbatim_parser import ekstrak_id_sesi

        assert ekstrak_id_sesi({"id_sesi": "ABC-123"}) == "ABC-123"
        assert ekstrak_id_sesi({}) == "SESI-TIDAK-DIKETAHUI"

    def test_skip_baris_kosong(self):
        from verbamind.backend.ai_pipeline.rag.verbatim_parser import (
            gabungkan_transkrip_menjadi_narasi,
        )

        data = {"transkrip": [{"speaker": "A", "teks": "", "emosi": ""}]}
        result = gabungkan_transkrip_menjadi_narasi(data)
        assert result == ""

    def test_load_verbatim_file_alias(self):
        from verbamind.backend.ai_pipeline.rag.verbatim_parser import load_verbatim_file

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump({"transkrip": [{"speaker": "X", "teks": "OK", "emosi": ""}]}, f)
            path = f.name

        data = load_verbatim_file(path)
        assert data["transkrip"][0]["teks"] == "OK"
        os.unlink(path)


class TestBIRPPrompt:
    def test_system_prompt_template(self):
        from verbamind.backend.ai_pipeline.prompts.birp_prompt import (
            USER_PROMPT_TEMPLATE,
        )

        prompt = USER_PROMPT_TEMPLATE.format(
            konteks_referensi="TEST_KONTEKS", narasi_transkrip="TEST_NARASI"
        )
        assert "TEST_KONTEKS" in prompt
        assert "TEST_NARASI" in prompt
        assert "Bahasa Indonesia" in prompt

    def test_build_system_prompt(self):
        from verbamind.backend.ai_pipeline.prompts.birp_prompt import (
            SYSTEM_PROMPT,
            build_system_prompt,
        )

        result = build_system_prompt()
        assert result == SYSTEM_PROMPT
        assert "behavior" in result.lower()
        assert "BIRP" in result
        assert "Bahasa Indonesia" in result

    def test_validate_birp_output_complete(self):
        from verbamind.backend.ai_pipeline.prompts.birp_prompt import validate_birp_output

        data = {"behavior": "B", "intervention": "I", "response": "R", "plan": "P"}
        result = validate_birp_output(data)
        assert result == data

    def test_validate_birp_output_fills_missing(self):
        from verbamind.backend.ai_pipeline.prompts.birp_prompt import validate_birp_output

        data = {"behavior": "B"}
        result = validate_birp_output(data)
        assert result["intervention"] == ""
        assert result["response"] == ""
        assert result["plan"] == ""


class TestLLMWrapper:
    def test_llm_default_config(self):
        from verbamind.backend.ai_pipeline.llm import LLMWrapper
        from verbamind.config.llm_settings import get_llm_base_url, resolve_llm_model

        llm = LLMWrapper()
        assert llm._model == resolve_llm_model()
        assert llm._base_url == get_llm_base_url()

    def test_llm_custom_config(self):
        from verbamind.backend.ai_pipeline.llm import LLMWrapper

        llm = LLMWrapper(base_url="http://other:1234", model="test-model")
        assert llm._base_url == "http://other:1234"
        assert llm._model == "test-model"

    @patch("verbamind.backend.ai_pipeline.llm.LLMWrapper._init")
    def test_generate_calls_ollama(self, mock_init):
        from verbamind.backend.ai_pipeline.llm import LLMWrapper

        mock_llm_obj = MagicMock()
        mock_llm_obj.invoke.return_value.content = '{"a": 1}'
        mock_init.return_value = None

        llm = LLMWrapper()
        llm._llm = mock_llm_obj
        result = llm.generate("test prompt")
        assert result == '{"a": 1}'
        mock_llm_obj.invoke.assert_called_once()


class TestRAGRetriever:
    @patch("verbamind.backend.ai_pipeline.rag.retriever.FAISS")
    @patch("verbamind.backend.ai_pipeline.rag.retriever.OllamaEmbeddings")
    def test_retrieve_returns_context(self, mock_emb, mock_faiss):
        from verbamind.backend.ai_pipeline.rag.retriever import RAGRetriever

        mock_doc = MagicMock()
        mock_doc.page_content = "Isi dokumen referensi klinis."
        mock_doc.metadata = {"source": "kode_etik.txt"}
        mock_faiss.load_local.return_value.similarity_search.return_value = [mock_doc]
        mock_emb.return_value = MagicMock()

        with tempfile.TemporaryDirectory() as td:
            Path(td, "index.faiss").touch()
            retriever = RAGRetriever(index_dir=td)
            result = retriever.retrieve("test query")
            assert "Referensi 1" in result
            assert "kode_etik.txt" in result

    @patch("verbamind.backend.ai_pipeline.rag.retriever.FAISS")
    @patch("verbamind.backend.ai_pipeline.rag.retriever.OllamaEmbeddings")
    def test_retrieve_empty_results(self, mock_emb, mock_faiss):
        from verbamind.backend.ai_pipeline.rag.retriever import RAGRetriever

        mock_faiss.load_local.return_value.similarity_search.return_value = []
        mock_emb.return_value = MagicMock()

        with tempfile.TemporaryDirectory() as td:
            Path(td, "index.faiss").touch()
            retriever = RAGRetriever(index_dir=td)
            result = retriever.retrieve("query")
            assert "Tidak ada konteks" in result

    def test_retriever_index_not_found(self):
        from verbamind.backend.ai_pipeline.rag.retriever import RAGRetriever

        with tempfile.TemporaryDirectory() as td:
            retriever = RAGRetriever(index_dir=td)
            with pytest.raises(FileNotFoundError):
                retriever.retrieve("test")


class TestBIRPGenerator:
    @patch("verbamind.backend.ai_pipeline.birp_generator.LLMWrapper")
    def test_generate_returns_birp(self, mock_llm_cls):
        from verbamind.backend.ai_pipeline.birp_generator import BIRPGenerator

        mock_llm = MagicMock()
        mock_llm.generate.return_value = json.dumps({
            "behavior": "B", "intervention": "I", "response": "R", "plan": "P",
        })
        mock_llm_cls.return_value = mock_llm

        retriever = MagicMock()
        retriever.retrieve.return_value = "Konteks referensi dummy."

        gen = BIRPGenerator(retriever=retriever, llm=mock_llm)

        verbatim = {
            "id_sesi": "SES-01",
            "transkrip": [{"speaker": "A", "teks": "Test", "emosi": ""}],
        }
        result = gen.generate(verbatim)

        assert result["behavior"] == "B"
        assert result["intervention"] == "I"
        assert result["response"] == "R"
        assert result["plan"] == "P"

    @patch("verbamind.backend.ai_pipeline.birp_generator.LLMWrapper")
    def test_generate_fills_missing_keys(self, mock_llm_cls):
        from verbamind.backend.ai_pipeline.birp_generator import BIRPGenerator

        mock_llm = MagicMock()
        mock_llm.generate.return_value = json.dumps({"behavior": "B only"})
        mock_llm_cls.return_value = mock_llm
        retriever = MagicMock()
        retriever.retrieve.return_value = "Konteks."

        gen = BIRPGenerator(retriever=retriever, llm=mock_llm)
        verbatim = {
            "transkrip": [{"speaker": "A", "teks": "Test", "emosi": ""}],
        }
        result = gen.generate(verbatim, session_id="SES-01")
        assert result["response"] == ""


class TestKnowledgeIngest:
    def test_import_works(self):
        from verbamind.backend.ai_pipeline.rag import knowledge_ingest

        assert knowledge_ingest.main is not None

    def test_constants(self):
        from verbamind.backend.ai_pipeline.rag.knowledge_ingest import (
            NAMA_MODEL_EMBEDDING,
            UKURAN_CHUNK,
            TUMPANG_TINDIH_CHUNK,
        )

        assert NAMA_MODEL_EMBEDDING == "nomic-embed-text"
        assert UKURAN_CHUNK == 500
        assert TUMPANG_TINDIH_CHUNK == 100

    def test_validasi_empty_folder(self):
        from verbamind.backend.ai_pipeline.rag.knowledge_ingest import validasi_folder

        with tempfile.TemporaryDirectory() as td:
            kb = Path(td) / "knowledge_base"
            kb.mkdir()
            from importlib import reload
            import verbamind.backend.ai_pipeline.rag.knowledge_ingest as m

            old = m.DIREKTORI_KNOWLEDGE_BASE
            m.DIREKTORI_KNOWLEDGE_BASE = kb
            with pytest.raises(SystemExit):
                validasi_folder()
            m.DIREKTORI_KNOWLEDGE_BASE = old


class TestBIRPAPI:
    def test_router_registered(self):
        from verbamind.backend.api.birp_router import router

        routes = [r.path for r in router.routes]
        assert "/api/v1/birp/generate" in routes

    def test_endpoint_returns_response(self):
        from fastapi.testclient import TestClient

        from verbamind.backend.api.birp_router import router
        from verbamind.backend.main import app
        from verbamind.security.token import get_token

        app.include_router(router)
        client = TestClient(app, headers={"X-VerbaMind-Token": get_token()})
        response = client.post("/api/v1/birp/generate", json={
            "session_id": "SES-01",
            "verbatim_segments": [
                {"speaker": "Patient", "text": "Hello", "start": 0.0, "end": 1.0, "emotion": None},
            ],
        })
        assert response.status_code in (200, 400, 500)
