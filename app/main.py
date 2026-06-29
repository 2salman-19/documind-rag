"""
FastAPI entry point for DocuMind RAG.

WHY: Provides HTTP interface for document upload and chat queries.
Keeps transport layer separate from core RAG logic.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional  # ✅ Added for Optional type hints
from contextlib import asynccontextmanager
from pathlib import Path
import tempfile
import os
import json
from app.rag_engine import RAGEngine
from app.document_processor import DocumentProcessor
from app.agent import get_agent, AgentBrain

# Global RAG engine instance (initialized once at startup)
rag_engine: RAGEngine = None
# Global Agent instance (initialized once at startup)
agent_brain: AgentBrain = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events.

    WHY: Initialize heavy resources (embedding model, DB client) once at startup,
    not on every request. Saves memory and improves response time.
    """
    global rag_engine, agent_brain
    print("🚀 Starting DocuMind RAG...")
    rag_engine = RAGEngine()
    print("✅ RAG Engine initialized")
    agent_brain = get_agent(rag_engine)
    print("✅ Agent Brain initialized")
    yield
    print("🛑 Shutting down DocuMind RAG...")


# Initialize FastAPI app
app = FastAPI(
    title="DocuMind RAG API",
    description="AI-powered document Q&A system with hybrid search",
    version="1.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatRequest(BaseModel):
    query: str
    top_k: int = 3
    history: list = []  # ✅ Changed from list[dict]
    source_filter: Optional[str] = None  # ✅ Changed to Optional[str]


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


class UploadRequest(BaseModel):
    text_content: str
    source: str = "manual_input"


class UploadResponse(BaseModel):
    success: bool
    chunks_created: int
    message: str


class FileUploadResponse(BaseModel):
    success: bool
    filename: str
    file_size_mb: float
    chunks_created: int
    message: str


class AgentChatRequest(BaseModel):
    query: str
    top_k: int = 3
    history: list = []  # ✅ Changed from list[dict]
    source_filter: Optional[str] = None  # ✅ Changed to Optional[str]


class AgentChatResponse(BaseModel):
    thoughts: list[dict]
    final_answer: str
    success: bool


# Endpoints
@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Status message and engine initialization state.
    """
    return {
        "status": "healthy",
        "engine_initialized": rag_engine is not None,
        "message": "DocuMind RAG is running"
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint: User query → Retrieve context → Generate answer.

    Args:
        request: ChatRequest with query, optional top_k, and conversation history

    Returns:
        ChatResponse with answer and source chunks
    """
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")

    try:
        result = rag_engine.generate_answer(
            user_query=request.query,
            top_k=request.top_k,
            history=request.history,
            source_filter=request.source_filter
        )
        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")


@app.post("/upload", response_model=UploadResponse)
async def upload_document(request: UploadRequest):
    """Legacy text upload endpoint."""
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")

    try:
        rag_engine.process_and_store(
            text_content=request.text_content,
            source=request.source
        )
        return UploadResponse(
            success=True,
            chunks_created=1,
            message="Document processed and stored successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@app.post("/upload-file", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and process PDF/DOCX/TXT files.

    WHY: Real-world use case - users upload actual documents, not paste text.
    Includes validation, extraction, chunking, and storage in one flow.
    """
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")

    temp_file_path = None

    try:
        # 1. Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        # 2. Validate file
        is_valid, error_msg = DocumentProcessor.validate_file(temp_file_path, file.filename)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # 3. Extract text
        text_content = DocumentProcessor.extract_text(temp_file_path, file.filename)

        # 4. Process and store
        rag_engine.process_and_store(
            text_content=text_content,
            source=file.filename
        )

        # 5. Calculate file size
        file_size_mb = len(content) / (1024 * 1024)

        return FileUploadResponse(
            success=True,
            filename=file.filename,
            file_size_mb=round(file_size_mb, 2),
            chunks_created=1,  # Placeholder - actual count from DB
            message=f"File '{file.filename}' processed successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

    finally:
        # 6. Cleanup temp file
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@app.post("/chat-stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint - returns Server-Sent Events (SSE).

    WHY: Provides real-time word-by-word response for better UX.
    """
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")

    async def generate():
        # Stream tokens from RAG engine
        for token in rag_engine.generate_answer_stream(
            user_query=request.query,
            top_k=request.top_k,
            history=request.history,
            source_filter=request.source_filter
        ):
            # Send as Server-Sent Event format
            yield f"data: {json.dumps({'token': token})}\n\n"

        # Send completion signal
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/documents")
async def list_documents():
    """
    List all uploaded documents with metadata.

    Returns:
        List of documents with source names, chunk counts, and character counts.
    """
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")

    try:
        # Query unique sources from documents table
        response = rag_engine.db_client.client.table('documents').select('metadata').execute()

        # Extract unique sources with stats
        sources = {}
        for row in response.data:
            metadata = row.get('metadata', {})
            source = metadata.get('source', 'Unknown')

            if source not in sources:
                sources[source] = {
                    'source': source,
                    'chunk_count': 0,
                    'total_chars': 0
                }

            sources[source]['chunk_count'] += 1
            sources[source]['total_chars'] += metadata.get('char_count', 0)

        return {
            "success": True,
            "documents": list(sources.values()),
            "total_documents": len(sources)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")


@app.post("/chat-agent", response_model=AgentChatResponse)
async def chat_agent(request: AgentChatRequest):
    """
    Agentic RAG endpoint: Agent decides which tool to use based on query.

    The agent can choose between:
    - RAG search (for private documents)
    - Web search (for real-time information)
    - Calculator (for mathematical calculations)

    Args:
        request: AgentChatRequest with query, optional top_k, and conversation history

    Returns:
        AgentChatResponse with thoughts (reasoning process) and final_answer
    """
    if not agent_brain:
        raise HTTPException(status_code=503, detail="Agent Brain not initialized")

    try:
        result = agent_brain.chat(
            query=request.query,
            history=request.history
        )
        return AgentChatResponse(
            thoughts=result['thoughts'],
            final_answer=result['final_answer'],
            success=result['success']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in agent chat: {str(e)}")


@app.post("/chat-agent-stream")
async def chat_agent_stream(request: AgentChatRequest):
    """
    Streaming agentic RAG endpoint - returns Server-Sent Events (SSE).

    Streams the agent's thought process and final answer in real-time.

    Args:
        request: AgentChatRequest with query and optional conversation history

    Returns:
        StreamingResponse with SSE events containing thoughts and answer tokens
    """
    if not agent_brain:
        raise HTTPException(status_code=503, detail="Agent Brain not initialized")

    async def generate():
        # Use run_in_executor to avoid blocking the event loop
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        executor = ThreadPoolExecutor(max_workers=1)

        def run_agent():
            results = []
            for chunk in agent_brain.chat_stream(
                query=request.query,
                history=request.history
            ):
                results.append(chunk)
            return results

        # Run agent in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(executor, run_agent)

        # Stream results as SSE
        for chunk in results:
            yield f"data: {json.dumps(chunk)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)