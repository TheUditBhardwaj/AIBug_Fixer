"""
Retriever Service Module
Manages FAISS vector store for code retrieval
"""

import faiss
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import pickle
import os
from pathlib import Path


class RetrieverService:
    """
    Service for storing and retrieving code embeddings using FAISS.
    Enables semantic search over code chunks.
    """

    def __init__(self, embedding_dim: int = 384, index_path: Optional[str] = None):
        """
        Initialize the retriever service.

        Args:
            embedding_dim: Dimension of embeddings (must match model output)
            index_path: Path to load/save the FAISS index
        """
        self.embedding_dim = embedding_dim
        self.index_path = index_path or "./data/faiss_index"
        self.index = None
        self.documents = []  # Store original documents for retrieval
        self.metadata = []  # Store metadata alongside documents

        # Initialize FAISS index
        self._initialize_index()

    def _initialize_index(self):
        """Initialize or load FAISS index."""
        # Create a flat L2 index
        self.index = faiss.IndexFlatL2(self.embedding_dim)

        # Load existing index if available
        if os.path.exists(self.index_path):
            self._load_index()

    def add_documents(
        self,
        embeddings: List[np.ndarray],
        documents: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        Add documents with their embeddings to the index.

        Args:
            embeddings: List of embedding vectors
            documents: List of original document texts
            metadata: Optional list of metadata dictionaries
        """
        if len(embeddings) != len(documents):
            raise ValueError("Number of embeddings must match number of documents")

        # Convert embeddings to numpy array
        embeddings_array = np.array(embeddings).astype("float32")

        # Add to FAISS index
        self.index.add(embeddings_array)

        # Store documents and metadata
        self.documents.extend(documents)
        if metadata:
            self.metadata.extend(metadata)
        else:
            self.metadata.extend([{}] * len(documents))

    def add_code_chunks(
        self,
        chunk_embeddings: List[Tuple[np.ndarray, Dict[str, Any]]],
        chunks: List[Dict[str, Any]],
    ):
        """
        Add code chunks with embeddings.

        Args:
            chunk_embeddings: List of (embedding, metadata) tuples
            chunks: List of chunk dictionaries with content
        """
        embeddings = [e for e, _ in chunk_embeddings]
        documents = [c["content"] for c in chunks]
        metadata = [m for _, m in chunk_embeddings]

        self.add_documents(embeddings, documents, metadata)

    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents.

        Args:
            query_embedding: Query vector
            k: Number of results to return

        Returns:
            List of result dictionaries with 'content', 'score', 'metadata'
        """
        if self.index.ntotal == 0:
            return []

        # Ensure k doesn't exceed available documents
        k = min(k, self.index.ntotal)

        # Reshape query for FAISS (expects 2D array)
        query = query_embedding.reshape(1, -1).astype("float32")

        # Search
        distances, indices = self.index.search(query, k)

        # Format results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.documents):
                results.append(
                    {
                        "content": self.documents[idx],
                        "score": float(distances[0][i]),
                        "metadata": (
                            self.metadata[idx] if idx < len(self.metadata) else {}
                        ),
                    }
                )

        return results

    def get_context_for_query(
        self,
        query_embedding: np.ndarray,
        max_tokens: int = 2000,
        separator: str = "\n\n---\n\n",
    ) -> str:
        """
        Get concatenated context for a query within token budget.

        Args:
            query_embedding: Query embedding
            max_tokens: Approximate token limit for context
            separator: String to separate chunks

        Returns:
            Concatenated context string
        """
        results = self.search(query_embedding, k=10)  # Get more than needed

        context_parts = []
        current_length = 0

        for result in results:
            content = result["content"]
            # Rough token estimate (4 chars per token on average)
            estimated_tokens = len(content) // 4

            if current_length + estimated_tokens > max_tokens:
                break

            context_parts.append(content)
            current_length += estimated_tokens

        return separator.join(context_parts)

    def save_index(self):
        """Save the FAISS index and metadata to disk."""
        if self.index_path:
            # Create directory if needed
            Path(self.index_path).parent.mkdir(parents=True, exist_ok=True)

            # Save FAISS index
            faiss.write_index(self.index, f"{self.index_path}.faiss")

            # Save documents and metadata
            with open(f"{self.index_path}.meta", "wb") as f:
                pickle.dump({"documents": self.documents, "metadata": self.metadata}, f)

    def _load_index(self):
        """Load the FAISS index and metadata from disk."""
        try:
            faiss_path = f"{self.index_path}.faiss"
            meta_path = f"{self.index_path}.meta"

            if os.path.exists(faiss_path) and os.path.exists(meta_path):
                self.index = faiss.read_index(faiss_path)

                with open(meta_path, "rb") as f:
                    data = pickle.load(f)
                    self.documents = data.get("documents", [])
                    self.metadata = data.get("metadata", [])
        except Exception as e:
            print(f"Error loading index: {e}")
            # Reinitialize if load fails
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            self.documents = []
            self.metadata = []

    def clear(self):
        """Clear the index and all stored documents."""
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.documents = []
        self.metadata = []

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the index.

        Returns:
            Dictionary with index statistics
        """
        return {
            "total_documents": len(self.documents),
            "embedding_dimension": self.embedding_dim,
            "index_type": type(self.index).__name__,
        }
