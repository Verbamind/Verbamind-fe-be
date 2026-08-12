"""RAG Retriever — FAISS semantic search over clinical knowledge base.

Adapted from Verbamind_RAG src/main_rag.py — muat_index_faiss + ambil_konteks_relevan.
"""

from pathlib import Path

try:
    from langchain_community.vectorstores import FAISS
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    HuggingFaceEmbeddings = None  # type: ignore
    FAISS = None  # type: ignore

NAMA_MODEL_EMBEDDING = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
JUMLAH_DOKUMEN_RETRIEVAL = 4


class RAGRetriever:
    def __init__(self, index_dir: str):
        self._index_dir = Path(index_dir)
        self._index: FAISS | None = None
        self._embeddings = None

    def _init_embeddings(self):
        if HuggingFaceEmbeddings is None:
            raise ImportError("langchain-huggingface not installed")
        self._embeddings = HuggingFaceEmbeddings(
            model_name=NAMA_MODEL_EMBEDDING,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
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
