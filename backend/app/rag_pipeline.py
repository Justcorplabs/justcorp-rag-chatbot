from typing import List, Dict, Any

from app.embeddings import embedding_model
from app.vector_store import vector_store


class RAGPipeline:
    """
    Retrieval pipeline for the JustCorp Labs AI Knowledge Base.

    Step 6 only performs retrieval:
    - embed the user's question
    - search ChromaDB
    - return the most relevant chunks

    LLM answer generation comes in Step 7.
    """

    def retrieve_context(
        self,
        question: str,
        top_k: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the most relevant chunks for a user question.
        """

        if not question or not question.strip():
            return []

        query_embedding = embedding_model.embed_text(question.strip())

        matched_chunks = vector_store.search_similar_chunks(
            query_embedding=query_embedding,
            top_k=top_k,
        )

        return matched_chunks


rag_pipeline = RAGPipeline()