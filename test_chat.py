"""
Test complete RAG pipeline with Groq LLM.
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

print('\n💬 Testing Chat...')
query = "What is DocuMind and how does it work?"
result = e.generate_answer(query)

print(f'\n📝 Answer:\n{result["answer"]}')
print(f'\n📚 Sources ({len(result["sources"])} chunks):')
for i, source in enumerate(result["sources"], 1):
    print(f'\n--- Source {i} ---')
    print(source[:150] + '...' if len(source) > 150 else source)

import gc
gc.collect()
print('\n✅ Chat test complete')