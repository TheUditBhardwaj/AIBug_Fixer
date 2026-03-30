"""
Embedding Service Module
Generates embeddings for code chunks using Sentence Transformers
"""

from sentence_transformers import SentenceTransformer
from typing import List, Optional, Tuple
import numpy as np


class EmbeddingService:
    """
    Service for generating code embeddings using Sentence Transformers.
    Uses a code-specialized model for better semantic understanding.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding service.

        Args:
            model_name: Name of the sentence-transformers model to use
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Numpy array embedding
        """
        return self.model.encode(text, convert_to_numpy=True)

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            Numpy array of embeddings (batch_size x embedding_dim)
        """
        return self.model.encode(texts, convert_to_numpy=True)

    def embed_code_chunks(
        self, chunks: List[dict], include_metadata: bool = True
    ) -> List[Tuple[np.ndarray, dict]]:
        """
        Embed code chunks with metadata.

        Args:
            chunks: List of chunk dictionaries with 'content' and 'metadata'
            include_metadata: Whether to include metadata in embedding

        Returns:
            List of (embedding, metadata) tuples
        """
        texts_to_embed = []
        for chunk in chunks:
            if include_metadata and "metadata" in chunk:
                # Include file path and chunk type for better context
                metadata = chunk.get("metadata", {})
                text = f"{metadata.get('filepath', '')}\n{metadata.get('type', 'code')}\n{chunk['content']}"
            else:
                text = chunk["content"]
            texts_to_embed.append(text)

        embeddings = self.embed_batch(texts_to_embed)

        return [
            (embeddings[i], chunks[i].get("metadata", {})) for i in range(len(chunks))
        ]

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embeddings.

        Returns:
            Embedding dimension
        """
        return self.model.get_sentence_embedding_dimension()

    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Similarity score between -1 and 1
        """
        return np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )
