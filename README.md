# 🧠 DocuMind RAG

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg)](.)

**AI-powered Document Q&A System with Hybrid Search and Real-Time Streaming**

DocuMind RAG is a production-ready Retrieval-Augmented Generation system that enables users to upload documents (PDF, DOCX, TXT), ask questions in natural language, and receive accurate answers with streaming responses and multi-turn conversation support.

## ✨ Key Features

✅ **Multi-Format Document Upload** - PDF, DOCX, TXT with validation  
✅ **Semantic Chunking** - Meaning-based splitting for better context preservation  
✅ **Hybrid Search** - BM25 (keywords) + Vector (semantics) for superior accuracy  
✅ **Multi-Turn Conversations** - Chat history with intelligent context awareness  
✅ **Real-Time Streaming** - Word-by-word responses with Server-Sent Events  
✅ **Clean AI Responses** - Professional answers without inline citations  
✅ **LocalStorage Persistence** - Chat history survives page refreshes  
✅ **Production Ready** - Error handling, CORS, validation, security measures  

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.11+
Supabase Account (free tier)
Groq API Key (free tier)
```

### Installation (5 minutes)

```bash
# 1. Clone & Setup
git clone <repo-url>
cd documind-rag
python -m venv venv
venv\Scripts\activate  # Windows

# 2. Install Dependencies
pip install -r requirements.txt

# 3. Configure Environment
cp .env.example .env
# Edit .env with your Groq API Key and Supabase credentials

# 4. Setup Database (Supabase)
# Run SQL from DOCUMENTATION.md in Supabase SQL Editor
# Create documents table with pgvector extension

# 5. Start Backend
python -m uvicorn app.main:app --reload --port 8000

# 6. Open Frontend
# Open index.html in browser or use VS Code Live Server
# Navigate to http://localhost:8000
```

## 📋 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | HTML5, CSS3, Vanilla JS | Clean, responsive UI |
| **Backend** | FastAPI (Python 3.11) | REST API & Streaming |
| **Database** | Supabase (PostgreSQL + pgvector) | Document storage & vector search |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 | 384-dim, 80MB, CPU-compatible |
| **LLM** | Groq (Llama-3.3-70B) | Fast, high-quality responses |
| **Chunking** | LlamaIndex SemanticSplitterNodeParser | Semantic document splitting |
| **Search** | Hybrid (BM25 30% + Vector 70%) | Keyword + semantic search |
| **Streaming** | Server-Sent Events (SSE) | Real-time token generation |

## 🏗️ Project Structure

```
documind-rag/
├── app/
│   ├── main.py                    # FastAPI app & endpoints
│   ├── rag_engine.py              # Core RAG logic
│   ├── supabase_client.py         # Database wrapper
│   └── document_processor.py      # PDF/DOCX/TXT parser
├── config/
│   └── settings.py                # Environment config
├── index.html                     # Frontend UI
├── requirements.txt               # Python dependencies
├── README.md                      # This file
├── DOCUMENTATION.md               # Technical documentation
├── .env                           # Environment variables (git ignored)
├── .gitignore
└── venv/                          # Virtual environment
```

## 📡 API Endpoints

### Health Check
```bash
GET /health
```

### Chat (Streaming Recommended)
```bash
POST /chat-stream
Content-Type: application/json
{
  "query": "What is machine learning?",
  "top_k": 3,
  "history": [...]  # Optional conversation history
}
```
Response: Server-Sent Events stream with tokens

### File Upload
```bash
POST /upload-file
Content-Type: multipart/form-data
File: document.pdf
```

### Text Upload
```bash
POST /upload
Content-Type: application/json
{
  "text_content": "Document text here...",
  "source": "my_document"
}
```

## 🎯 How It Works

```
1. User uploads document
   ↓
2. Semantic chunking splits into meaningful pieces
   ↓
3. Embeddings generated for each chunk (384 dims)
   ↓
4. Chunks stored in Supabase with pgvector
   ↓
5. User asks question
   ↓
6. Hybrid search retrieves relevant chunks (BM25 + Vector)
   ↓
7. Chunks + history sent to Groq LLM
   ↓
8. LLM generates answer (streamed to frontend)
   ↓
9. Answer appears word-by-word in chat
```

## 🔑 Environment Variables

```bash
# Groq API (get free key from console.groq.com)
GROQ_API_KEY=gsk_xxxxxxxxxxxxx

# Supabase (create account at supabase.com)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...

# App Settings
ENVIRONMENT=development
DEBUG=False
```

## 📊 Performance

| Operation | Time | Notes |
|-----------|------|-------|
| PDF Upload (10 pages) | 3-5s | Includes parsing + embedding |
| Document Retrieval | 200-500ms | Hybrid search with indexing |
| First Token (streaming) | 200-500ms | TTFT from Groq |
| Full Response | 2-4s | Typical chat response |
| **Total Latency** | **3-5s** | End-to-end user perspective |

## 🔐 Security Features

✅ File extension whitelist (PDF, DOCX, TXT only)  
✅ File size limits (10MB max)  
✅ Service role key (backend only, no anon key)  
✅ Temporary file cleanup  
✅ Input validation (Pydantic models)  
✅ CORS configured  
✅ Error handling with safe messages  

## 📚 Documentation

- **[DOCUMENTATION.md](DOCUMENTATION.md)** - Complete technical guide with:
  - Architecture diagrams (ASCII)
  - API reference
  - Database schema
  - Setup troubleshooting
  - Future enhancements

## 🛠️ Development

### Run Backend
```bash
python -m uvicorn app.main:app --reload --port 8000
```

### Run Tests
```bash
python test_retrieval.py
python test_chat.py
```

### Code Quality
```bash
pip install pylint black
pylint app/
black app/
```

## 📝 Example Usage

```python
# Start conversation
User: "What is in the document?"
Assistant: "The document contains information about..."

# Follow-up (uses history)
User: "Aur batao" (Hindi: Tell me more)
Assistant: "Based on the previous context, additionally..."

# Another follow-up
User: "Is ka matlab?"  (Hindi: What does this mean?)
Assistant: "That refers to..."
```

## 🎨 Frontend Features

- **Tabbed Interface** - Chat & Upload tabs
- **Real-Time Streaming** - Typing effect as response arrives
- **Chat History** - Persisted in localStorage
- **New Chat Button** - Reset conversation with confirmation
- **Responsive Design** - Works on mobile & desktop
- **Error Handling** - User-friendly error messages
- **File Upload** - Drag-drop ready

## 🚀 Deployment

### Quick Deploy (Railway/Render)
1. Push to GitHub
2. Connect to Railway/Render
3. Set environment variables
4. Deploy!

### Docker
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

## 🤝 Contributing

Contributions welcome! Areas for enhancement:
- Re-ranker implementation
- Document management UI
- User authentication
- Database conversation persistence
- Rate limiting

## 📖 Learning Resources

- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [LlamaIndex Docs](https://docs.llamaindex.ai/)
- [Supabase Docs](https://supabase.com/docs)
- [Groq API Docs](https://console.groq.com/docs)

## ❓ FAQ

**Q: Why does streaming make responses faster?**  
A: Streaming shows first token in ~200ms instead of waiting for full response (2-4s).

**Q: Can I use different embeddings?**  
A: Yes, update `HuggingFaceEmbedding` in `rag_engine.py` (keep 384 dims for Supabase).

**Q: How much does it cost?**  
A: Supabase (free tier), Groq (free tier), total = $0 for hobby projects.

**Q: Does it work offline?**  
A: No, requires internet for Groq API and Supabase.

## 📄 License

MIT License - feel free to use for personal & commercial projects.

## 👨‍💻 Author

**Salman Siddique**
- 📧 Email: salmansiddique0040@gmail.com
- 🔗 LinkedIn: [linkedin.com/in/salman](https://linkedin.com/in/salman)
- 🐙 GitHub: [github.com/Salman](https://github.com/Salman)

## 🙏 Acknowledgments

- FastAPI team for excellent framework
- Groq for free LLM access
- Supabase for PostgreSQL + pgvector
- LlamaIndex community

---

**⭐ If this helps you, please give it a star!**

**Made with ❤️ for document Q&A lovers**
