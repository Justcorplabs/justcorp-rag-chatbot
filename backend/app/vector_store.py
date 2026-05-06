from typing import List, Dict, Any
from pathlib import Path

import chromadb

from app.config import settings


class VectorStore:
    """
    Handles local vector storage using ChromaDB.

    ChromaDB stores:
    - chunk text
    - embedding vectors
    - metadata such as filename and chunk number
    """

    def __init__(self):
        chroma_path = Path(settings.CHROMA_DB_PATH)
        chroma_path.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(path=str(chroma_path))

        self.collection = self.client.get_or_create_collection(
            name="justcorp_knowledge_base"
        )

    def add_document_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
    ) -> int:
        """
        Add document chunks and their embeddings to ChromaDB.
        """

        if not chunks:
            return 0

        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings.")

        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:
            chunk_id = f"{chunk['document_id']}_chunk_{chunk['chunk_number']}"

            ids.append(chunk_id)
            documents.append(chunk["text"])
            metadatas.append(
                {
                    "document_id": chunk["document_id"],
                    "filename": chunk["filename"],
                    "chunk_number": chunk["chunk_number"],
                }
            )

        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        return len(chunks)

    def search_similar_chunks(
        self,
        query_embedding: List[float],
        top_k: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        Search ChromaDB for chunks most similar to the user's question.
        """

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        matched_chunks = []

        for document_text, metadata, distance in zip(documents, metadatas, distances):
            matched_chunks.append(
                {
                    "document_id": metadata.get("document_id"),
                    "filename": metadata.get("filename"),
                    "chunk_number": metadata.get("chunk_number"),
                    "text": document_text,
                    "distance": distance,
                }
            )

        return matched_chunks

    def list_documents(self) -> List[Dict[str, Any]]:
        """
        Return a simple grouped list of uploaded documents from ChromaDB.
        """

        results = self.collection.get(include=["metadatas"])

        documents = {}

        for metadata in results.get("metadatas", []):
            if not metadata:
                continue

            document_id = metadata.get("document_id")
            filename = metadata.get("filename")

            if document_id not in documents:
                documents[document_id] = {
                    "document_id": document_id,
                    "filename": filename,
                    "chunks": 0,
                }

            documents[document_id]["chunks"] += 1

        return list(documents.values())

    def delete_document(self, document_id: str) -> int:
        """
        Delete all chunks linked to a specific document_id.
        """

        existing = self.collection.get(
            where={"document_id": document_id},
            include=["metadatas"],
        )

        ids = existing.get("ids", [])

        if not ids:
            return 0

        self.collection.delete(ids=ids)

        return len(ids)


vector_store = VectorStore()