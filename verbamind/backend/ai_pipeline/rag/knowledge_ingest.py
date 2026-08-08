"""Knowledge ingest — builds FAISS vector store from clinical knowledge base.

Adapted from Verbamind_RAG's ingest_knowledge.py.
Reads .txt files, chunks, embeds, and saves FAISS index.

Provides the top-level `ingest_knowledge_base()` function.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Must match the embedding model used by RAGRetriever
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Chunking configuration
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

# Lazy import — declared at module level so tests can mock them.
# All are None until _check_dependencies() confirms they're available.
TextLoader = None  # type: ignore[assignment]
FAISS = None  # type: ignore[assignment]
HuggingFaceEmbeddings = None  # type: ignore[assignment]
RecursiveCharacterTextSplitter = None  # type: ignore[assignment]


def _check_dependencies():
    """Verify and set up langchain dependencies.

    Sets module-level globals: TextLoader, FAISS, HuggingFaceEmbeddings,
    RecursiveCharacterTextSplitter.

    Raises:
        ImportError: If required packages are missing.
    """
    global TextLoader, FAISS, HuggingFaceEmbeddings, RecursiveCharacterTextSplitter
    try:
        from langchain_community.document_loaders import TextLoader as TL
        from langchain_community.vectorstores import FAISS as FS
        from langchain_huggingface import HuggingFaceEmbeddings as HFE
        from langchain_text_splitters import RecursiveCharacterTextSplitter as RCTS

        TextLoader = TL
        FAISS = FS
        HuggingFaceEmbeddings = HFE
        RecursiveCharacterTextSplitter = RCTS
    except ImportError as e:
        raise ImportError(
            f"RAG dependencies not installed: {e}. "
            f"Install with: pip install langchain langchain-community "
            f"langchain-huggingface langchain-text-splitters faiss-cpu sentence-transformers"
        ) from e


def _validate_knowledge_base(kb_dir: Path) -> list[Path]:
    """Validate knowledge base directory and return .txt files.

    Args:
        kb_dir: Path to the knowledge base directory.

    Returns:
        List of .txt file paths.

    Raises:
        FileNotFoundError: If directory doesn't exist.
        ValueError: If no .txt files found.
    """
    if not kb_dir.exists():
        raise FileNotFoundError(
            f"Folder knowledge base tidak ditemukan: {kb_dir}"
        )

    txt_files = [f for f in kb_dir.glob("*.txt")]
    if not txt_files:
        raise ValueError(
            f"Tidak ditemukan file .txt di dalam {kb_dir}. "
            f"Tambahkan minimal satu file .txt berisi materi kode etik/teori psikologi."
        )

    return txt_files


def ingest_knowledge_base(
    knowledge_base_path: str = "data/knowledge_base",
    index_output_path: str = "faiss_index",
    embedding_model: str = EMBEDDING_MODEL_NAME,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> int:
    """Build FAISS index from knowledge base .txt files.

    Reads all .txt files from the knowledge base directory, splits into
    overlapping chunks, generates embeddings, and saves a FAISS index.

    Args:
        knowledge_base_path: Directory containing .txt knowledge files.
        index_output_path: Directory where FAISS index is saved.
        embedding_model: HuggingFace model name for embeddings.
        chunk_size: Maximum characters per text chunk.
        chunk_overlap: Overlap between adjacent chunks.

    Returns:
        Number of chunks created in the FAISS index.

    Raises:
        FileNotFoundError: If knowledge_base_path doesn't exist.
        ValueError: If no .txt files found in the directory.
        ImportError: If langchain dependencies are not installed.
    """
    kb_dir = Path(knowledge_base_path)
    faiss_dir = Path(index_output_path)

    # Validate FIRST (before importing heavy langchain deps)
    txt_files = _validate_knowledge_base(kb_dir)

    # Check deps and import langchain (inside function for lazy loading)
    _check_dependencies()

    # Using module-level globals set by _check_dependencies()

    # Load documents
    documents = []
    for filepath in txt_files:
        loader = TextLoader(str(filepath), encoding="utf-8")
        documents.extend(loader.load())

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)

    if not chunks:
        logger.warning("No chunks generated from documents")
        return 0

    # Build embeddings and FAISS index
    model = HuggingFaceEmbeddings(
        model_name=embedding_model,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    index = FAISS.from_documents(documents=chunks, embedding=model)

    # Save
    faiss_dir.mkdir(parents=True, exist_ok=True)
    index.save_local(str(faiss_dir))
    logger.info(f"FAISS index saved to {faiss_dir} with {len(chunks)} chunks")

    return len(chunks)
