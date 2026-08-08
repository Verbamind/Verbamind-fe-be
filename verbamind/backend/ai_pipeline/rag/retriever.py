"""RAG Retriever — FAISS-based semantic search for clinical knowledge base.

Adapted from Verbamind_RAG's main_rag.py retrieval logic.
Uses multilingual embedding model for Indonesian text support.
"""

from __future__ import annotations

import logging
from pathlib import Path

# Import at module level for mock patching in tests
try:
    from langchain_community.vectorstores import FAISS  # noqa: F401
    from langchain_huggingface import HuggingFaceEmbeddings  # noqa: F401
except ImportError:
    FAISS = None  # type: ignore[assignment]
    HuggingFaceEmbeddings = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

# Must match the embedding model used during ingest_knowledge
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class RAGRetriever:
    """Retrieves relevant clinical knowledge from a FAISS vector store.

    The FAISS index must be pre-built by KnowledgeIngest before retrieval.
    """

    def __init__(
        self,
        index_path: str | Path = "faiss_index",
        embedding_model: str = EMBEDDING_MODEL_NAME,
        top_k: int = 4,
    ) -> None:
        """Initialize the retriever.

        Args:
            index_path: Path to the saved FAISS index directory.
            embedding_model: HuggingFace model name for embeddings.
            top_k: Number of top documents to retrieve.
        """
        self.index_path = Path(index_path)
        self.embedding_model = embedding_model
        self.top_k = top_k

    def _load_faiss_index(self):
        """Load the FAISS index from disk.

        Returns:
            Loaded FAISS vector store object.

        Raises:
            FileNotFoundError: If the FAISS index directory is missing or empty.
        """
        if not self.index_path.exists() or not any(self.index_path.iterdir()):
            raise FileNotFoundError(
                f"FAISS index tidak ditemukan di: {self.index_path}. "
                f"Jalankan ingest_knowledge.py terlebih dahulu."
            )

        model = HuggingFaceEmbeddings(
            model_name=self.embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        return FAISS.load_local(
            folder_path=str(self.index_path),
            embeddings=model,
            allow_dangerous_deserialization=True,
        )

    def retrieve(self, query: str, k: int | None = None) -> str:
        """Search the knowledge base for documents relevant to the query.

        Args:
            query: The query text (typically the verbatim narrative).
            k: Number of documents to retrieve (defaults to self.top_k).

        Returns:
            Combined context string from top-k retrieved documents.
        """
        num_docs = k if k is not None else self.top_k

        try:
            index = self._load_faiss_index()
            docs = index.similarity_search(query=query, k=num_docs)

            if not docs:
                return "(Tidak ada konteks referensi tambahan yang ditemukan.)"

            chunks = []
            for i, doc in enumerate(docs, start=1):
                source = doc.metadata.get("source", "sumber tidak diketahui")
                src_name = Path(source).name if source != "sumber tidak diketahui" else source
                chunks.append(f"[Referensi {i} - sumber: {src_name}]\n{doc.page_content}")

            return "\n\n".join(chunks)
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.warning(f"Retrieval failed: {e}; returning empty context")
            return "(Tidak ada konteks referensi tambahan yang ditemukan.)"
