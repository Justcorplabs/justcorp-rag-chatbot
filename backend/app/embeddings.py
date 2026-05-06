import hashlib
import math
import re
from typing import List


class LightweightEmbeddingModel:
    """
    Lightweight deterministic embedding model for free deployment.

    Why this exists:
    - sentence-transformers + torch are too heavy for Render Free
    - this model uses simple hashing-based bag-of-words embeddings
    - it is not as semantically powerful as MiniLM, but it is fast,
      free, deterministic, and deployable on small memory instances

    Good enough for:
    - portfolio demos
    - FAQ documents
    - service guides
    - onboarding documents
    - business knowledge base prototypes
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def _tokenize(self, text: str) -> List[str]:
        """
        Convert text into normalized tokens.
        """

        if not text:
            return []

        text = text.lower()

        tokens = re.findall(r"[a-z0-9]+", text)

        return tokens

    def _hash_token(self, token: str) -> int:
        """
        Convert token into a stable integer index.
        """

        digest = hashlib.md5(token.encode("utf-8")).hexdigest()
        return int(digest, 16) % self.dimension

    def _embed_single_text(self, text: str) -> List[float]:
        """
        Create a normalized hashing-based vector for one text.
        """

        vector = [0.0] * self.dimension
        tokens = self._tokenize(text)

        if not tokens:
            return vector

        for token in tokens:
            index = self._hash_token(token)
            vector[index] += 1.0

        norm = math.sqrt(sum(value * value for value in vector))

        if norm == 0:
            return vector

        return [value / norm for value in vector]

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple texts.
        """

        return [self._embed_single_text(text) for text in texts]

    def embed_query(self, query: str) -> List[float]:
        """
        Embed a user question/search query.
        """

        return self._embed_single_text(query)


embedding_model = LightweightEmbeddingModel()