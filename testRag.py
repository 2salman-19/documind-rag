"""
Test script to verify RAG Engine document processing.
Run this in external CMD terminal, not VS Code.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from app.rag_engine import RAGEngine

print('🔄 Initializing RAG Engine...')
e = RAGEngine()
print('✅ Engine initialized')

print('🔄 Processing document...')
e.process_and_store(
    text_content='DocuMind is an advanced AI system that uses Retrieval-Augmented Generation. It helps users find answers from their private documents securely. The system uses Hybrid Search to combine keyword matching with semantic understanding.',
    source='test_doc_v1'
)
print('✅ Process complete')