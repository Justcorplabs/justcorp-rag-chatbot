from typing import List
from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class EmbeddingModel:
    """
    Handles local embedding generation using sentence-transformers.

    Version 1 uses all-MiniLM-L6-v2 because it is:
    - free
    - lightweight
    - fast enough for demos
    - good for semantic search
    """

    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME)

    def embed_text(self, text: str) -> List[float]:
        """
        Convert one text string into an embedding vector.
        """

        embedding = self.model.encode(text)
        return embedding.tolist()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Convert multiple text chunks into embedding vectors.
        """

        if not texts:
            return []

        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()


embedding_model = EmbeddingModel()