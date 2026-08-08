"""RAG (Retrieval-Augmented Generation) module for VerbaMind.

Integrates with the Verbamind_RAG pipeline for clinical knowledge retrieval.
All operations run locally (on-premise) for patient data confidentiality.

Components:
- verbatim_parser: Parse verbatim.json transcripts into narrative text
- retriever: FAISS-based semantic search of clinical knowledge base
- knowledge_ingest: Build FAISS index from .txt/.pdf knowledge base files
"""
