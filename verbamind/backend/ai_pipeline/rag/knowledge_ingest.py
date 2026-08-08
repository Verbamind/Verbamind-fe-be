# ==============================================================================
# knowledge_ingest.py — adapted from Verbamind_RAG src/ingest_knowledge.py
#
# Build FAISS vector index from clinical knowledge base (.txt + .pdf).
# Uses paraphrase-multilingual-MiniLM-L12-v2 (optimized for Bahasa Indonesia).
# ==============================================================================

import sys
from pathlib import Path

DIREKTORI_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
DIREKTORI_KNOWLEDGE_BASE = DIREKTORI_ROOT / "data" / "knowledge_base"
DIREKTORI_FAISS_INDEX = DIREKTORI_ROOT / "faiss_index"

NAMA_MODEL_EMBEDDING = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
UKURAN_CHUNK = 500
TUMPANG_TINDIH_CHUNK = 100


def validasi_folder() -> None:
    if not DIREKTORI_KNOWLEDGE_BASE.exists():
        print(f"[ERROR] Folder tidak ditemukan: {DIREKTORI_KNOWLEDGE_BASE}")
        sys.exit(1)
    txt = list(DIREKTORI_KNOWLEDGE_BASE.glob("*.txt"))
    pdf = list(DIREKTORI_KNOWLEDGE_BASE.glob("*.pdf"))
    total = len(txt) + len(pdf)
    if total == 0:
        print(f"[ERROR] Tidak ada file .txt/.pdf di: {DIREKTORI_KNOWLEDGE_BASE}")
        sys.exit(1)
    print(f"[INFO] {len(txt)} TXT + {len(pdf)} PDF ditemukan.")


def muat_semua_dokumen() -> list:
    from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyMuPDFLoader

    dokumen = []

    # Load TXT
    loader = DirectoryLoader(
        path=str(DIREKTORI_KNOWLEDGE_BASE),
        glob="*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=False,
    )
    dokumen = loader.load()
    print(f"[INFO] {len(dokumen)} dokumen dari .txt")

    # Load PDF
    for pdf_file in DIREKTORI_KNOWLEDGE_BASE.glob("*.pdf"):
        try:
            loader_pdf = PyMuPDFLoader(str(pdf_file))
            halaman = loader_pdf.load()
            dokumen.extend(halaman)
            print(f"[INFO] {pdf_file.name}: {len(halaman)} halaman")
        except Exception as e:
            print(f"[WARNING] Gagal baca {pdf_file.name}: {e}")

    return dokumen


def pecah_chunk(dokumen: list) -> list:
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=UKURAN_CHUNK,
        chunk_overlap=TUMPANG_TINDIH_CHUNK,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunk = splitter.split_documents(dokumen)
    print(f"[INFO] {len(chunk)} chunk dihasilkan.")
    return chunk


def bangun_faiss(chunk: list) -> None:
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS

    print(f"[INFO] Memuat model: {NAMA_MODEL_EMBEDDING}...")
    emb = HuggingFaceEmbeddings(
        model_name=NAMA_MODEL_EMBEDDING,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    print("[INFO] Membangun index FAISS...")
    index = FAISS.from_documents(chunk, emb)
    DIREKTORI_FAISS_INDEX.mkdir(parents=True, exist_ok=True)
    index.save_local(str(DIREKTORI_FAISS_INDEX))
    print(f"[SUKSES] FAISS index tersimpan di: {DIREKTORI_FAISS_INDEX}")


def main():
    print("=" * 60)
    print("VERBAMIND — INGESTION KNOWLEDGE BASE → FAISS")
    print("=" * 60)
    validasi_folder()
    dok = muat_semua_dokumen()
    if not dok:
        print("[ERROR] Tidak ada dokumen yang berhasil dimuat.")
        sys.exit(1)
    chunk = pecah_chunk(dok)
    bangun_faiss(chunk)


if __name__ == "__main__":
    main()
