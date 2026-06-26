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

    def hybrid_search(self, query_text: str, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        """
        Performs hybrid search using BM25 (keyword) + Vector similarity via RPC.
        
        Args:
            query_text: Raw user query for keyword matching.
            query_embedding: Vector representation of the query.
            top_k: Number of results to return.
            
        Returns:
            List of relevant document chunks.
        """
        try:
            # Calls the 'match_documents' SQL function we will create next
            response = self.client.rpc(
                'match_documents', 
                {
                    'query_text': query_text,
                    'query_embedding': query_embedding,
                    'match_count': top_k
                }
            ).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"❌ Error during hybrid search: {e}")
            return []