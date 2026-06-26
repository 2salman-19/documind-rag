"""
Re-ranker module for improving retrieval accuracy.

WHY: Hybrid search returns top K chunks, but not all are equally relevant.
Re-ranker uses cross-encoder to score each chunk against query,
then selects top N most relevant chunks.

Performance: Accuracy boost of 20-30% in RAG systems.
"""

from sentence_transformers import CrossEncoder
from typing import List, Tuple


class Reranker:
    """Cross-encoder based re-ranker for chunk relevance scoring."""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize re-ranker with cross-encoder model.
        
        Args:
            model_name: Pre-trained cross-encoder model
                - "cross-encoder/ms-marco-MiniLM-L-6-v2" (fast, good quality)
                - "cross-encoder/ms-marco-electra-base" (slower, better quality)
        """
        print(f"🔄 Loading re-ranker model: {model_name}")
        self.model = CrossEncoder(model_name)
        print("✅ Re-ranker model loaded")
    
    def rerank(
        self, 
        query: str, 
        chunks: List[str], 
        top_k: int = 3
    ) -> List[Tuple[str, float]]:
        """
        Re-rank chunks based on relevance to query.
        
        Args:
            query: User's question
            chunks: List of text chunks from retrieval
            top_k: Number of top chunks to return
            
        Returns:
            List of tuples: (chunk_text, relevance_score)
        """
        if not chunks:
            return []
        
        # Create query-chunk pairs for scoring
        pairs = [(query, chunk) for chunk in chunks]
        
        # Get relevance scores from cross-encoder
        scores = self.model.predict(pairs)
        
        # Combine chunks with scores
        chunk_scores = list(zip(chunks, scores))
        
        # Sort by score (descending) and take top K
        chunk_scores.sort(key=lambda x: x[1], reverse=True)
        top_chunks = chunk_scores[:top_k]
        
        return top_chunks


# Global re-ranker instance (initialized once)
reranker_instance = None


def get_reranker() -> Reranker:
    """Get or create global re-ranker instance."""
    global reranker_instance
    if reranker_instance is None:
        reranker_instance = Reranker()
    return reranker_instance