"""
Supabase client wrapper for DocuMind RAG.

WHY: Isolates storage layer logic from business logic (rag_engine).
Makes it easy to swap databases later or mock this class for testing.
Uses async patterns to support concurrent I/O in FastAPI without blocking.
"""

from supabase import create_client, Client
from config.settings import get_settings


class SupabaseClient:
    """Wrapper for Supabase client with pgvector hybrid search support."""
    
    def __init__(self):
        settings = get_settings()
        self.client: Client = create_client(
            settings.SUPABASE_URL, 
            settings.SUPABASE_SERVICE_KEY
        )
        self.table_name = "documents"

    def insert_documents(self, documents: list[dict]) -> tuple[bool, list[dict]]:
        """
        Inserts processed document chunks into Supabase.
        
        Returns:
            Tuple of (success: bool, data: list[dict])
        """
        try:
            response = self.client.table(self.table_name).insert(documents).execute()
            return True, response.data
        except Exception as e:
            print(f"❌ Error inserting documents: {e}")
            return False, []

    def hybrid_search(
        self, 
        query_text: str, 
        query_embedding: list[float], 
        top_k: int = 5,
        source_filter: str = None
    ) -> list[dict]:
        """
        Hybrid search with optional source filtering.
        
        Args:
            query_text: User's question
            query_embedding: Query vector
            top_k: Number of results
            source_filter: Optional source name to filter (e.g., "Salman_Siddique_resume.pdf")
            
        Returns:
            List of relevant document chunks.
        """
        try:
            response = self.client.rpc(
                'match_documents',
                {
                    'query_embedding': query_embedding,
                    'query_text': query_text,
                    'match_count': top_k,
                    'source_filter': source_filter
                }
            ).execute()
            
            return response.data if response.data else []
        except Exception as e:
            print(f"❌ Hybrid search error: {e}")
            return []