import time
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from query_processing_service import get_query_processor
from retrieval_service import get_retrieval_service
from reranking_service import get_reranking_service
from models import SearchLog

logger = logging.getLogger(__name__)

class HybridSearchService:
    def __init__(self):
        self.embedding_service = None
        try:
            from embedding_service import get_embedding_service
            self.embedding_service = get_embedding_service()
        except Exception as e:
            logger.warning(f"Embedding search unavailable; falling back to keyword search. Reason: {e}")
        self.query_processor = get_query_processor()
        self.retrieval_service = get_retrieval_service()
        self.reranking_service = get_reranking_service()

    def _keyword_fallback(self, db: Session, query: str, limit: int):
        pattern = f"%{query.strip()}%"
        from models import Problem
        problems = db.query(Problem).filter(
            (Problem.title.ilike(pattern)) |
            (Problem.description.ilike(pattern)) |
            (Problem.suggested_tech.ilike(pattern))
        ).order_by(Problem.engineering_impact_score.desc(), Problem.scraped_at.desc()).limit(limit).all()
        for problem in problems:
            problem.search_scores = {
                "semantic": 0.0,
                "keyword": 1.0,
                "tag": 0.0,
                "final": round((problem.engineering_impact_score or 0) / 100, 3)
            }
        return problems

    def log_search(self, db: Session, query: str, results_count: int, latency_ms: float):
        """Log search query performance and results"""
        try:
            log_entry = SearchLog(
                query=query,
                results_returned=results_count,
                latency_ms=latency_ms
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to log search: {e}")

    def intent_aware_search(self, db: Session, query: str, limit: int = 10):
        """
        Google-style Two-Stage Intent-Aware Retrieval:
        1. Query Processing (Normalization + Expansion)
        2. Stage 1: Candidate Retrieval (Vector + Keyword)
        3. Stage 2: Intelligent Re-ranking (Weighted Hybrid + Intent Boosts)
        """
        start_time = time.perf_counter()
        
        # --- Stage 0: Query Understanding ---
        processed = self.query_processor.process_query(query)
        semantic_query = processed["semantic"]
        keyword_query = processed["keyword"]

        if self.embedding_service is None:
            final_results = self._keyword_fallback(db, keyword_query or query, limit)
            total_latency_ms = (time.perf_counter() - start_time) * 1000
            self.log_search(db, query, len(final_results), total_latency_ms)
            return final_results, {
                "latency_ms": round(total_latency_ms, 2),
                "stage1_candidates": len(final_results),
                "reranking": "keyword_fallback",
                "processed_query": processed
            }
        
        # --- Stage 1: Broad Candidate Retrieval ---
        # Get semantic embedding (with caching)
        query_embedding = self.embedding_service.generate_query_embedding(semantic_query)
        
        candidate_ids = self.retrieval_service.get_candidates(
            db, 
            query_embedding=query_embedding, 
            keyword_query=keyword_query, 
            limit=30
        )
        stage1_count = len(candidate_ids)

        # --- Stage 2: Intelligent Re-ranking ---
        final_results = self.reranking_service.rerank(
            db, 
            candidate_ids=candidate_ids, 
            semantic_query_embedding=query_embedding, 
            keyword_query=keyword_query
        )
        
        total_latency_ms = (time.perf_counter() - start_time) * 1000
        
        # Log the search
        self.log_search(db, query, len(final_results), total_latency_ms)
        
        metadata = {
            "latency_ms": round(total_latency_ms, 2),
            "stage1_candidates": stage1_count,
            "reranking": "hybrid_v2",
            "processed_query": processed
        }
        
        return final_results[:limit], metadata

    # Keep compatibility with old methods if needed, or remove them
    def search(self, db: Session, query_text: str = None, query_tags: list[str] = None, limit: int = 20):
        # Fallback to new search if query_text is provided
        if query_text:
            results, _ = self.intent_aware_search(db, query_text, limit)
            return results
        return []

    def search_semantic(self, db: Session, query: str, limit: int = 10, min_score: float = 0.0):
        # Reuse logic for semantic search if still needed
        # (Implementing a simplified version or just calling new flow)
        return self.intent_aware_search(db, query, limit)

# Singleton instance access
_search_service = None
def get_search_service():
    global _search_service
    if _search_service is None:
        _search_service = HybridSearchService()
    return _search_service
