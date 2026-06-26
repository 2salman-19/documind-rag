"""
Quick test: Verify hybrid search retrieval works.
"""

import sys
import os

os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'

sys.stdout.reconfigure(encoding='utf-8')

from app.rag_engine import RAGEngine

print('🔄 Initializing RAG Engine...')
e = RAGEngine()
print('✅ Engine initialized')

print('\n🔍 Testing Hybrid Search...')
query = "What is DocuMind?"
results = e.query(query, top_k=3)

print(f'\n📊 Retrieved {len(results)} chunks:')
for i, chunk in enumerate(results, 1):
    print(f'\n--- Chunk {i} ---')
    print(chunk[:200] + '...' if len(chunk) > 200 else chunk)

import gc
gc.collect()
print('\n✅ Retrieval test complete')