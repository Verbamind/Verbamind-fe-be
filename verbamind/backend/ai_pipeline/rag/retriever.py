"""RAG Retriever — FAISS semantic search over clinical knowledge base.

Uses Ollama embeddings (nomic-embed-text) so the backend does not pull
PyTorch/sentence-transformers. FAISS index is built by knowledge_ingest.
"""

from pathlib import Path

try:
    from langchain_community.vectorstores import FAISS
    from langchain_ollama import OllamaEmbeddings
except ImportError:
    OllamaEmbeddings = None  # type: ignore
    FAISS = None  # type: ignore

NAMA_MODEL_EMBEDDING = "nomic-embed-text"
JUMLAH_DOKUMEN_RETRIEVAL = 4
OLLAMA_URL = "http://localhost:11434"


class RAGRetriever:
    def __init__(self, index_dir: str):
        self._index_dir = Path(index_dir)
        self._index: FAISS | None = None
        self._embeddings = None

    def _init_embeddings(self):
        if OllamaEmbeddings is None:
            raise ImportError("langchain-ollama not installed")
        self._embeddings = OllamaEmbeddings(
            model=NAMA_MODEL_EMBEDDING,
            base_url=OLLAMA_URL,
        )

    def load_index(self):
        if not self._index_dir.exists() or not any(self._index_dir.iterdir()):
            raise FileNotFoundError(
                f"Index FAISS tidak ditemukan di: {self._index_dir}\n"
                f"Jalankan ingest_knowledge terlebih dahulu."
            )
        if FAISS is None:
            raise ImportError("langchain-community not installed")
        self._init_embeddings()
        self._index = FAISS.load_local(
            folder_path=str(self._index_dir),
            embeddings=self._embeddings,
            allow_dangerous_deserialization=True,
        )

    def retrieve(self, query: str, top_k: int = JUMLAH_DOKUMEN_RETRIEVAL) -> str:
        if self._index is None:
            self.load_index()
        hasil = self._index.similarity_search(query=query, k=top_k)
        if not hasil:
            return "(Tidak ada konteks referensi tambahan yang ditemukan.)"
        potongan = []
        for nomor, doc in enumerate(hasil, start=1):
            sumber = doc.metadata.get("source", "sumber tidak diketahui")
            potongan.append(
                f"[Referensi {nomor} - sumber: {Path(sumber).name}]\n{doc.page_content}"
            )
        return "\n\n".join(potongan)
