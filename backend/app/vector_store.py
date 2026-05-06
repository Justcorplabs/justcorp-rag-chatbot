import json
import math
from pathlib import Path
from typing import Any, Dict, List

from app.config import settings


class LightweightVectorStore:
    """
    Lightweight JSON-based vector store for free deployment.

    Why this replaces ChromaDB:
    - ChromaDB can be too heavy for Render Free
    - this stores document chunks and embeddings in a small JSON file
    - cosine similarity is computed directly in Python

    This is suitable for small/medium portfolio demo documents.
    For production with many documents, move back to ChromaDB, Qdrant,
    Pinecone, Supabase Vector, or another proper vector database.
    """

    def __init__(self):
        self.storage_dir = Path(getattr(settings, "VECTOR_STORE_DIR", "vector_store_data"))
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.storage_file = self.storage_dir / "documents.json"

        if not self.storage_file.exists():
            self._save_records([])

    def _load_records(self) -> List[Dict[str, Any]]:
        """
        Load all stored chunk records from disk.
        """

        try:
            with self.storage_file.open("r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return []

    def _save_records(self, records: List[Dict[str, Any]]) -> None:
        """
        Save all chunk records to disk.
        """

        with self.storage_file.open("w", encoding="utf-8") as file:
            json.dump(records, file, ensure_ascii=False, indent=2)

    def _cosine_similarity(
        self,
        vector_a: List[float],
        vector_b: List[float],
    ) -> float:
        """
        Compute cosine similarity between two vectors.
        """

        if not vector_a or not vector_b:
            return 0.0

        length = min(len(vector_a), len(vector_b))

        dot_product = 0.0
        norm_a = 0.0
        norm_b = 0.0

        for index in range(length):
            value_a = float(vector_a[index])
            value_b = float(vector_b[index])

            dot_product += value_a * value_b
            norm_a += value_a * value_a
            norm_b += value_b * value_b

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (math.sqrt(norm_a) * math.sqrt(norm_b))

    def add_document_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
    ) -> int:
        """
        Store document chunks and their embeddings.
        """

        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings.")

        records = self._load_records()

        for chunk, embedding in zip(chunks, embeddings):
            record = {
                "document_id": chunk.get("document_id"),
                "filename": chunk.get("filename"),
                "chunk_number": chunk.get("chunk_number"),
                "text": chunk.get("text"),
                "embedding": embedding,
            }

            records.append(record)

        self._save_records(records)

        return len(chunks)

    def search_similar(
        self,
        query_embedding: List[float],
        top_k: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        Search for the most similar document chunks.
        """

        records = self._load_records()

        scored_results = []

        for record in records:
            embedding = record.get("embedding", [])

            similarity = self._cosine_similarity(
                query_embedding,
                embedding,
            )

            distance = 1.0 - similarity

            scored_results.append(
                {
                    "document_id": record.get("document_id"),
                    "filename": record.get("filename"),
                    "chunk_number": record.get("chunk_number"),
                    "text": record.get("text"),
                    "distance": distance,
                    "similarity": similarity,
                }
            )

        scored_results.sort(key=lambda item: item["similarity"], reverse=True)

        return scored_results[:top_k]

    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List unique uploaded documents.
        """

        records = self._load_records()

        documents_by_id: Dict[str, Dict[str, Any]] = {}

        for record in records:
            document_id = record.get("document_id")

            if not document_id:
                continue

            if document_id not in documents_by_id:
                documents_by_id[document_id] = {
                    "document_id": document_id,
                    "filename": record.get("filename"),
                    "chunks_count": 0,
                }

            documents_by_id[document_id]["chunks_count"] += 1

        return list(documents_by_id.values())

    def delete_document(self, document_id: str) -> int:
        """
        Delete all chunks belonging to one document.
        """

        records = self._load_records()

        remaining_records = [
            record for record in records
            if record.get("document_id") != document_id
        ]

        chunks_deleted = len(records) - len(remaining_records)

        self._save_records(remaining_records)

        return chunks_deleted


vector_store = LightweightVectorStore()