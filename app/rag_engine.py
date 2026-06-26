"""
Core RAG orchestration engine for DocuMind.

WHY: Centralizes the logic for chunking, embedding, and retrieval.
Keeps the FastAPI layer clean and allows easy swapping of models or 
retrieval strategies (e.g., adding Re-rankers later).
"""

from llama_index.core import Document
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from app.supabase_client import SupabaseClient
from config.settings import get_settings


class RAGEngine:
    """Handles document processing and hybrid search retrieval."""

    def __init__(self):
        # Initialize Embedding Model (Local, Free, 384 dims)
        # 80MB model, 384 dimensions, stable on low RAM
        self.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # Initialize Semantic Splitter
        self.splitter = SemanticSplitterNodeParser(
            buffer_size=1, 
            breakpoint_percentile_threshold=95,
            embed_model=self.embed_model
        )
        
        # Initialize Database Client
        self.db_client = SupabaseClient()

    def process_and_store(self, text_content: str, source: str = "manual_input"):
        """
        Takes raw text, chunks it semantically, embeds it, and stores in Supabase.
        
        Args:
            text_content: The raw text from a PDF or user input.
            source: Metadata tag for the document source.
        """
        print("🔄 Starting Semantic Chunking...")
        
        # 1. Create LlamaIndex Document object
        doc = Document(text=text_content, metadata={"source": source})
        
        # 2. Semantic Chunking (Dynamic splitting based on meaning)
        nodes = self.splitter.get_nodes_from_documents([doc])
        print(f"✅ Created {len(nodes)} semantic chunks.")

        # 3. Prepare data for Supabase
        documents_to_insert = []
        for node in nodes:
            # Generate embedding for each chunk
            embedding = self.embed_model.get_text_embedding(node.text)
            
            documents_to_insert.append({
                "content": node.text,
                "embedding": embedding,
                "metadata": {"source": source, "char_count": len(node.text)}
            })

        # 4. Batch Insert into Supabase
        if documents_to_insert:
            success, data = self.db_client.insert_documents(documents_to_insert)
            if success:
                print(f"💾 Successfully stored {len(documents_to_insert)} chunks in Supabase.")
            else:
                print(f"❌ Failed to store chunks in Supabase.")
        else:
            print("⚠️ No chunks generated to store.")

    def query(self, user_query: str, top_k: int = 5) -> list[str]:
        """
        Retrieves relevant context using Hybrid Search.
        
        Args:
            user_query: The question asked by the user.
            top_k: Number of relevant chunks to retrieve.
            
        Returns:
            List of relevant text chunks.
        """
        print(f"🔍 Searching for: '{user_query}'")
        
        # 1. Embed the user's query
        query_embedding = self.embed_model.get_text_embedding(user_query)
        
        # 2. Perform Hybrid Search via Supabase RPC
        results = self.db_client.hybrid_search(
            query_text=user_query,
            query_embedding=query_embedding,
            top_k=top_k
        )
        
        # 3. Extract only the content text
        retrieved_contexts = [item['content'] for item in results]
        
        if retrieved_contexts:
            print(f"✅ Found {len(retrieved_contexts)} relevant chunks.")
        else:
            print("❌ No relevant documents found.")
            
        return retrieved_contexts

    def generate_answer(self, user_query: str, top_k: int = 3, history: list[dict] = None) -> dict:
        """
        Complete RAG pipeline with conversation history support.
        
        Args:
            user_query: User's current question
            top_k: Number of chunks to retrieve
            history: List of previous messages [{"role": "user/assistant", "content": "..."}]
            
        Returns:
            Dict with 'answer' and 'sources'
        """
        from llama_index.llms.groq import Groq
        from config.settings import get_settings
        
        print(f"\n🧠 Generating answer for: '{user_query}'")
        
        # 1. Retrieve relevant chunks (only for current query, not history)
        chunks = self.query(user_query, top_k=top_k)
        
        if not chunks:
            return {
                "answer": "Sorry, I couldn't find relevant information in the documents.",
                "sources": []
            }
        
        # 2. Format context for LLM
        context = "\n\n---\n\n".join(chunks)
        
        # 3. Build conversation history string
        history_text = ""
        if history and len(history) > 0:
            history_parts = []
            for msg in history[-6:]:  # Last 6 messages (3 turns)
                role = "User" if msg["role"] == "user" else "Assistant"
                history_parts.append(f"{role}: {msg['content']}")
            history_text = "\n".join(history_parts)
        
        # 4. Create prompt with history context
        if history_text:
            prompt = f"""You are DocuMind, an AI assistant that answers questions based on provided documents.
You are in a conversation with the user. Use the conversation history to understand context and follow-up questions.

Knowledge Base Context:
{context}

Previous Conversation:
{history_text}

Current Question: {user_query}

Instructions:
- Answer based on the Knowledge Base Context
- Use conversation history to understand follow-up questions (e.g., "aur batao", "is ka matlab")
- If the answer is not in the context, say "I don't have enough information to answer this"
- Be concise, accurate, and professional
- DO NOT quote, cite, or mention the source text in your answer
- Provide a direct, natural response

Answer:"""
        else:
            prompt = f"""You are DocuMind, an AI assistant that answers questions based on provided documents.

Knowledge Base Context:
{context}

Question: {user_query}

Instructions:
- Answer based ONLY on the provided context
- If the answer is not in the context, say "I don't have enough information to answer this"
- Be concise, accurate, and professional
- DO NOT quote, cite, or mention the source text in your answer
- Provide a direct, natural response

Answer:"""
        
        # 5. Call Groq LLM
        try:
            settings = get_settings()
            llm = Groq(model="llama-3.3-70b-versatile", api_key=settings.GROQ_API_KEY)
            response = llm.complete(prompt)
            
            return {
                "answer": str(response),
                "sources": chunks[:3]
            }
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            return {
                "answer": "Sorry, I encountered an error generating the answer.",
                "sources": chunks
            }

    def generate_answer_stream(self, user_query: str, top_k: int = 3, history: list[dict] = None):
        """
        Streaming version of generate_answer - returns generator for word-by-word output.
        
        Args:
            user_query: User's current question
            top_k: Number of chunks to retrieve
            history: Conversation history
            
        Yields:
            Individual words/tokens as they are generated
        """
        from llama_index.llms.groq import Groq
        from config.settings import get_settings
        
        print(f"\n🧠 Streaming answer for: '{user_query}'")
        
        # 1. Retrieve relevant chunks
        chunks = self.query(user_query, top_k=top_k)
        
        if not chunks:
            yield "Sorry, I couldn't find relevant information in the documents."
            return
        
        # 2. Format context
        context = "\n\n---\n\n".join(chunks)
        
        # 3. Build history
        history_text = ""
        if history and len(history) > 0:
            history_parts = []
            for msg in history[-6:]:
                role = "User" if msg["role"] == "user" else "Assistant"
                history_parts.append(f"{role}: {msg['content']}")
            history_text = "\n".join(history_parts)
        
        # 4. Create prompt
        if history_text:
            prompt = f"""You are DocuMind, an AI assistant that answers questions based on provided documents.
You are in a conversation with the user. Use the conversation history to understand context.

Knowledge Base Context:
{context}

Previous Conversation:
{history_text}

Current Question: {user_query}

Instructions:
- Answer based on the Knowledge Base Context
- Use conversation history to understand follow-up questions
- Be concise, accurate, and professional
- DO NOT quote or cite sources
- Provide a direct, natural response

Answer:"""
        else:
            prompt = f"""You are DocuMind, an AI assistant that answers questions based on provided documents.

Knowledge Base Context:
{context}

Question: {user_query}

Instructions:
- Answer based ONLY on the provided context
- Be concise, accurate, and professional
- DO NOT quote or cite sources
- Provide a direct, natural response

Answer:"""
        
        # 5. Stream response from Groq
        try:
            settings = get_settings()
            llm = Groq(model="llama-3.3-70b-versatile", api_key=settings.GROQ_API_KEY)
            
            # Stream tokens
            response = llm.stream_complete(prompt)
            for chunk in response:
                if chunk.delta:
                    yield chunk.delta
        
        except Exception as e:
            print(f"❌ LLM Streaming Error: {e}")
            yield "Sorry, I encountered an error generating the answer."