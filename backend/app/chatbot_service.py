from typing import Any, Dict, List

from app.rag_pipeline import rag_pipeline
from app.llm_client import llm_client


def build_sources(retrieved_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert retrieved chunks into clean source objects.

    This mirrors the source-building logic used by the main /ask endpoint,
    but keeps it reusable for WhatsApp and future channels.
    """

    sources = []

    for chunk in retrieved_chunks:
        sources.append(
            {
                "document_id": chunk["document_id"],
                "filename": chunk["filename"],
                "chunk_number": chunk["chunk_number"],
                "distance": chunk["distance"],
            }
        )

    return sources


def get_chatbot_answer(question: str, top_k: int = 4) -> Dict[str, Any]:
    """
    Get an answer from the JustCorp Labs RAG knowledge base.

    Flow:
    - clean the question
    - retrieve relevant document chunks from ChromaDB
    - generate an answer using Groq based only on the retrieved chunks
    - return the answer and source references
    """

    if not question or not question.strip():
        return {
            "question": "",
            "answer": "Please send a question so I can help you.",
            "sources": [],
        }

    cleaned_question = question.strip()

    try:
        retrieved_chunks = rag_pipeline.retrieve_context(
            question=cleaned_question,
            top_k=top_k,
        )

        if not retrieved_chunks:
            return {
                "question": cleaned_question,
                "answer": "The uploaded documents do not contain enough information to answer that question.",
                "sources": [],
            }

        answer = llm_client.generate_answer(
            question=cleaned_question,
            retrieved_chunks=retrieved_chunks,
        )

        sources = build_sources(retrieved_chunks)

        return {
            "question": cleaned_question,
            "answer": answer,
            "sources": sources,
        }

    except Exception as error:
        print("Chatbot service error:", str(error))

        return {
            "question": cleaned_question,
            "answer": (
                "Sorry, I had trouble searching the knowledge base right now. "
                "Please try again in a moment."
            ),
            "sources": [],
        }