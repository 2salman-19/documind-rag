# 🧠 DocuMind RAG

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Working%20Prototype-orange.svg)](.)

**AI-powered Document Q&A System with Hybrid Search, Re-ranking, and Real-Time Streaming**

DocuMind RAG is a working prototype of a Retrieval-Augmented Generation system that enables users to upload documents (PDF, DOCX, TXT), ask questions in natural language, and receive accurate answers with intelligent re-ranking and real-time streaming responses.

**GitHub:** [github.com/2salman-19/documind-rag](https://github.com/2salman-19/documind-rag)  
**Author:** Salman Siddique  
**Last Updated:** June 2026  
**Version:** 1.1.0

## ✨ Key Features

✅ **Multi-Format Document Upload** - PDF, DOCX, TXT with validation  
✅ **Semantic Chunking** - Meaning-based splitting for better context preservation  
✅ **Hybrid Search** - BM25 (keywords) + Vector (semantics) for superior accuracy  
✅ **Cross-Encoder Re-ranking** - 20-30% accuracy boost with semantic re-ranking  
✅ **Multi-Turn Conversations** - Chat history with intelligent context awareness  
✅ **Real-Time Streaming** - Word-by-word responses with Server-Sent Events  
✅ **Source Filtering** - Search within specific documents  
✅ **Deduplication** - Automatic removal of duplicate chunks  
✅ **LocalStorage Persistence** - Chat history survives page refreshes  
✅ **Clean AI Responses** - Professional answers without inline citations  
✅ **Error Handling** - Comprehensive validation and user-friendly feedback  

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.11+
Supabase Account (free tier)
Groq API Key (free tier)
```

### Installation (5 minutes)

```bash
# 1. Clone Repository
git clone https://github.com/2salman-19/documind-rag.git
cd documind-rag

# 2. Create Virtual Environment
python -m venv venv
venv\Scripts\activate  # Windows

# 3. Install Dependencies
pip install -r requirements.txt

# 4. Configure Environment
cp .env.example .env
# Edit .env with your credentials:
# GROQ_API_KEY=gsk_xxxxxxxxxxxxx
# SUPABASE_URL=https://xxx.supabase.co
# SUPABASE_SERVICE_KEY=eyJ...

# 5. Setup Database (One-time in Supabase SQL Editor)
# See DOCUMENTATION.md for SQL schema setup

# 6. Start Backend
python -m uvicorn app.main:app --reload --port 8000

# 7. Open Frontend
# Option A: Open index.html in browser (file://)
# Option B: Use VS Code Live Server extension
# Navigate to http://localhost:8000
```

## 📋 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | HTML5, CSS3, Vanilla JS | Clean, responsive UI |
| **Backend** | FastAPI (Python 3.11) | REST API & Streaming |
| **Database** | Supabase (PostgreSQL + pgvector) | Document storage & vector search |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 | 384-dim, 80MB, CPU-only |
| **LLM** | Groq (Llama-3.3-70B-Versatile) | Fast, high-quality responses |
| **Chunking** | LlamaIndex SemanticSplitterNodeParser | Semantic document splitting |
| **Re-ranker** | CrossEncoder (ms-marco-MiniLM-L-6-v2) | Query-aware relevance scoring |
| **Search** | Hybrid (BM25 30% + Vector 70%) | Keyword + semantic search |
| **Streaming** | Server-Sent Events (SSE) | Real-time token generation |

## 🏗️ Project Structure

```
documind-rag/
├── app/
│   ├── main.py                    # FastAPI application & endpoints
│   ├── rag_engine.py              # Core RAG pipeline with re-ranker
│   ├── supabase_client.py         # Database wrapper
│   ├── document_processor.py      # PDF/DOCX/TXT parser
│   ├── reranker.py                # Cross-encoder re-ranking module
│   └── __init__.py
├── config/
│   ├── settings.py                # Pydantic environment configuration
│   └── __init__.py
├── index.html                     # Frontend single-page app
├── requirements.txt               # Python dependencies
├── README.md                      # This file
├── DOCUMENTATION.md               # Technical deep dive
├── .env                           # Environment variables (git ignored)
├── .gitignore
├── testRag.py                     # Basic RAG test
├── test_retrieval.py              # Retrieval pipeline test
├── test_chat.py                   # Chat endpoint test
├── test_reranker.py               # Re-ranker functionality test
└── venv/                          # Virtual environment
```

## 📡 API Endpoints

### Health Check
```bash
GET /health
# Response: {"status": "healthy", "engine_initialized": true, ...}
```

### Chat (Non-streaming)
```bash
POST /chat
Content-Type: application/json
{
  "query": "What is machine learning?",
  "top_k": 3,
  "history": [...],
  "source_filter": null
}
# Response: {"answer": "...", "sources": [...]}
```

### Chat (Streaming Recommended)
```bash
POST /chat-stream
Content-Type: application/json
{
  "query": "What is machine learning?",
  "top_k": 3,
  "history": [...],
  "source_filter": "document_name.pdf"
}
# Response: Server-Sent Events stream with tokens
```

### List Documents
```bash
GET /documents
# Response: {
#   "success": true,
#   "documents": [
#     {"source": "Resume.pdf", "chunk_count": 47, "total_chars": 12345},
#     {"source": "Report.docx", "chunk_count": 89, "total_chars": 45678}
#   ],
#   "total_documents": 2
# }
```

### Upload File
```bash
POST /upload-file
Content-Type: multipart/form-data
File: document.pdf
# Response: {"success": true, "filename": "...", "file_size_mb": 2.5, ...}
```

### Upload Text
```bash
POST /upload
Content-Type: application/json
{
  "text_content": "Document text...",
  "source": "my_document"
}
# Response: {"success": true, "chunks_created": 1, ...}
```

## 🎯 How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    1. USER UPLOADS DOCUMENT                  │
│                    (PDF, DOCX, or TXT)                       │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│         2. SEMANTIC CHUNKING (Meaning-based split)           │
│            ↓ Dynamic chunk boundaries                        │
│            ↓ Preserves context within chunks                 │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│     3. EMBEDDING GENERATION (all-MiniLM-L6-v2)              │
│        384-dimensional vectors stored in Supabase            │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              4. USER ASKS A QUESTION                         │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│    5. HYBRID SEARCH (Retrieves 2x chunks if re-ranking)     │
│        ├─ BM25 Score (30% weight) - Keyword matching        │
│        └─ Vector Score (70% weight) - Semantic similarity   │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│    6. RE-RANKING (CrossEncoder) - NEW! +20-30% accuracy     │
│        ├─ Semantic relevance to query                        │
│        ├─ Deduplication (removes duplicates)                │
│        └─ Returns top-K most relevant chunks                │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│   7. LLM GENERATION (Groq - Llama-3.3-70B)                  │
│        ├─ Current query                                      │
│        ├─ Last 6 messages (conversation history)            │
│        └─ Retrieved chunks (as context)                     │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│      8. STREAMING RESPONSE (Server-Sent Events)              │
│        Token-by-token display in real-time                  │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│   9. SAVE TO CHAT HISTORY (localStorage)                    │
│      Persists across page refreshes                         │
└─────────────────────────────────────────────────────────────┘
```

## 🔑 Environment Variables

```bash
# Required: Groq API (free tier at console.groq.com)
GROQ_API_KEY=gsk_xxxxxxxxxxxxx

# Required: Supabase (free tier at supabase.com)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...

# Optional: Application Settings
ENVIRONMENT=development
DEBUG=False
```

## 📊 Performance Metrics

| Operation | Time | Notes |
|-----------|------|-------|
| PDF Upload (10 pages) | 3-5s | Parsing + embedding generation |
| Hybrid Search | 200-500ms | With pgvector indexing |
| Re-ranking (20→5 chunks) | 100-200ms | CrossEncoder inference |
| First Token (LLM) | 200-500ms | Groq latency (TTFT) |
| Full Response | 2-4s | Typical multi-turn answer |
| **Total Latency** | **3-5s** | End-to-end user experience |

*Note: All times are from development machine. Supabase response times may vary.*

## 🔐 Security Features

✅ File extension whitelist (PDF, DOCX, TXT only)  
✅ File size limits (10MB max per upload)  
✅ Service role key for backend (no anonymous access)  
✅ Temporary file cleanup after processing  
✅ Input validation via Pydantic models  
✅ CORS configured for localhost  
✅ Error handling with safe messages  
✅ No credential exposure in logs  

## 🛠️ Development

### Run Backend
```bash
python -m uvicorn app.main:app --reload --port 8000
```

### Run Tests
```bash
# Test basic RAG pipeline
python testRag.py

# Test retrieval quality
python test_retrieval.py

# Test chat endpoints
python test_chat.py

# Test re-ranker module
python test_reranker.py
```

### Code Quality
```bash
pip install pylint black
pylint app/
black app/
```

## 📚 Documentation

- **[DOCUMENTATION.md](DOCUMENTATION.md)** - Complete technical reference:
  - Architecture diagrams
  - API endpoint details
  - Database schema
  - Re-ranker explanation
  - Setup troubleshooting
  - Performance tuning

## 🎨 Frontend Features

- **Tabbed Interface** - Chat & Upload tabs
- **Real-Time Streaming** - Typing effect as response arrives
- **Chat History** - Persisted in localStorage
- **Source Filter Dropdown** - Search within specific documents
- **Document List** - View all uploaded documents with stats
- **New Chat Button** - Reset conversation with confirmation
- **Responsive Design** - Works on mobile & desktop
- **Error Handling** - User-friendly error messages
- **File Validation** - Size and format checks

## 📝 Example Usage

```
User: "What is in the document?"
Assistant: "The document contains information about..."

User: "Aur batao" (Hindi: Tell me more)
Assistant: "Based on the previous context, additionally..."

User: "Search in Resume.pdf"
(Select "Resume.pdf" from dropdown)
User: "What are the key skills?"
Assistant: (searches only in Resume.pdf)
```

## 🤝 Contributing

This is a working prototype. Areas for future enhancement:
- Document management UI (upload, delete, organize)
- User authentication and multi-user support
- Database-level conversation persistence
- Advanced analytics and usage tracking
- Additional embedding models
- Custom prompt templates
- Rate limiting
- Performance optimizations

## 📖 Learning Resources

- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [LlamaIndex Docs](https://docs.llamaindex.ai/)
- [Supabase Docs](https://supabase.com/docs)
- [Groq API Docs](https://console.groq.com/docs)
- [Sentence Transformers](https://www.sbert.net/)

## ❓ FAQ

**Q: Why does the re-ranker improve accuracy?**  
A: It uses a trained CrossEncoder that understands semantic relevance to your specific query, filtering out less relevant chunks that BM25 might have ranked high.

**Q: Can I use different embeddings?**  
A: Yes, update `HuggingFaceEmbedding` in `rag_engine.py`. Ensure dimensions match your Supabase vector column (currently 384).

**Q: How much does it cost?**  
A: $0 for hobby projects. Supabase free tier, Groq free tier. Scale-up costs depend on usage.

**Q: Does it work offline?**  
A: No, requires internet for Groq LLM API and Supabase database.

**Q: Can I filter searches by document?**  
A: Yes! Use the dropdown in the Chat tab to search within specific documents.

**Q: Why is the first token slow?**  
A: First token includes cold-start latency from Groq's infrastructure. Subsequent tokens stream much faster.

## 📄 License

MIT License - Feel free to use for personal & commercial projects. See [LICENSE](LICENSE) file.

## 👨‍💻 Author

**Salman Siddique**
- 📧 Email: salmansiddique0040@gmail.com
- � LinkedIn: [linkedin.com/in/siddiquesalman-ds-ks/](https://www.linkedin.com/in/siddiquesalman-ds-ks/)
- �🔗 GitHub: [github.com/2salman-19](https://github.com/2salman-19)
- 📍 Project: [github.com/2salman-19/documind-rag](https://github.com/2salman-19/documind-rag)

## 🙏 Acknowledgments

- FastAPI team for excellent async framework
- Groq for free, fast LLM access
- Supabase for PostgreSQL + pgvector
- LlamaIndex for semantic chunking
- Sentence Transformers for embeddings
- HuggingFace community for open models

---

**Made with ❤️ for document Q&A enthusiasts**  
**Star this repo if it helps you!** ⭐
