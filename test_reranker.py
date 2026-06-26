"""
Test re-ranker integration.
"""

import sys
import os

os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'

sys.stdout.reconfigure(encoding='utf-8')

from app.rag_engine import RAGEngine

print('🔄 Initializing RAG Engine with Re-ranker...')
e = RAGEngine()
print('✅ Engine initialized')

print('\n🔍 Testing Query with Re-ranker...')
query = "Salman ki education kya hai?"
results = e.query(query, top_k=3, use_reranker=True)

print(f'\n📊 Retrieved {len(results)} chunks (re-ranked):')
for i, chunk in enumerate(results, 1):
    print(f'\n--- Chunk {i} ---')
    print(chunk[:200] + '...' if len(chunk) > 200 else chunk)

import gc
gc.collect()
print('\n✅ Re-ranker test complete')