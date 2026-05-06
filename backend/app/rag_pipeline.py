from typing import Any, Dict, List

from app.embeddings import embedding_model
from app.vector_store import vector_store


class RAGPipeline:
    """
    Retrieval pipeline for the JustCorp Labs AI Knowledge Base Chatbot.

    Flow:
    - receive a user question
    - create a lightweight embedding for the question
    - search stored document chunks using cosine similarity
    - return relevant chunks for the LLM answer generator
    """

    def retrieve_context(
        self,
        question: str,
        top_k: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the most relevant chunks for a question.
        """

        if not question or not question.strip():
            return []

        query_embedding = embedding_model.embed_query(question.strip())

        results = vector_store.search_similar(
            query_embedding=query_embedding,
            top_k=top_k,
        )

        cleaned_results = []

        for result in results:
            text = result.get("text")

            if not text:
                continue

            cleaned_results.append(
                {
                    "document_id": result.get("document_id"),
                    "filename": result.get("filename"),
                    "chunk_number": result.get("chunk_number"),
                    "text": text,
                    "distance": result.get("distance", 1.0),
                }
            )

        return cleaned_results


rag_pipeline = RAGPipeline()