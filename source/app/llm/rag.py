"""RAG Knowledge Base System"""
import json
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger


class RAGKnowledgeBase:
    """Retrieval-Augmented Generation knowledge base"""

    def __init__(self):
        self.knowledge_data = []
        self.embeddings = {}
        self.vector_db_path = Path("data/chroma_db")
        self.vector_db = None

        # Initialize
        self._init_knowledge_base()

    def _init_knowledge_base(self):
        """Initialize knowledge base"""
        try:
            # TODO: Initialize Chroma vector database
            # import chromadb
            # self.vector_db = chromadb.PersistentClient(path=str(self.vector_db_path))

            logger.info("RAG knowledge base initialized successfully")
        except Exception as e:
            logger.warning(f"RAG knowledge base initialization failed: {str(e)}")

    async def add_knowledge(
        self,
        title: str,
        content: str,
        category: str,
        tags: List[str],
        source: str = ""
    ) -> Dict[str, Any]:
        """
        Add knowledge entry

        Args:
            title: Title
            content: Content
            category: Category
            tags: List of tags
            source: Source

        Returns:
            Addition result
        """
        try:
            # Generate embedding vector
            embedding = await self._generate_embedding(content)

            knowledge_item = {
                "title": title,
                "content": content,
                "category": category,
                "tags": tags,
                "source": source,
                "embedding": embedding
            }

            self.knowledge_data.append(knowledge_item)

            # TODO: Store in vector database

            logger.info(f"Added knowledge: {title}")
            return {"status": "success", "message": "Knowledge added successfully"}

        except Exception as e:
            logger.error(f"Failed to add knowledge: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def search_knowledge(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge base

        Args:
            query: Query text
            top_k: Number of results to return
            category: Category filter

        Returns:
            List of relevant knowledge entries
        """
        try:
            # Generate query vector
            query_embedding = await self._generate_embedding(query)

            # Calculate similarity
            results = []
            for item in self.knowledge_data:
                if category and item.get("category") != category:
                    continue

                similarity = self._cosine_similarity(
                    query_embedding,
                    item.get("embedding", [])
                )

                results.append({
                    **item,
                    "similarity": similarity
                })

            # Sort by similarity
            results.sort(key=lambda x: x["similarity"], reverse=True)

            return results[:top_k]

        except Exception as e:
            logger.error(f"Knowledge search failed: {str(e)}")
            return []

    async def get_context_for_detection(
        self,
        detection_content: str,
        detection_type: str
    ) -> str:
        """
        Get contextual knowledge for detection

        Args:
            detection_content: Detection content
            detection_type: Detection type

        Returns:
            Relevant knowledge context
        """
        try:
            # Search relevant knowledge based on detection type
            category_map = {
                "url": "prevention_guide",
                "sms": "fraud_case",
                "call": "fraud_case",
                "voice": "prevention_guide"
            }

            category = category_map.get(detection_type)
            results = await self.search_knowledge(
                query=detection_content,
                top_k=3,
                category=category
            )

            # Build context text
            context_parts = []
            for result in results:
                context_parts.append(f"[{result['title']}]\n{result['content']}")

            return "\n\n".join(context_parts)

        except Exception as e:
            logger.error(f"Failed to get detection context: {str(e)}")
            return ""

    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate text embedding vector

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        try:
            # TODO: Use actual embedding model
            # from sentence_transformers import SentenceTransformer
            # model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            # embedding = model.encode(text).tolist()

            # Simplified random vector (should use real embedding model in production)
            import numpy as np
            embedding = np.random.rand(384).tolist()
            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            return [0] * 384

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity"""
        if not vec1 or not vec2:
            return 0.0

        import numpy as np
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    async def load_from_database(self, knowledge_records: List[Dict[str, Any]]):
        """
        Load knowledge from database

        Args:
            knowledge_records: List of knowledge records
        """
        try:
            for record in knowledge_records:
                knowledge_item = {
                    "title": record.get("title"),
                    "content": record.get("content"),
                    "category": record.get("category"),
                    "tags": record.get("tags", []),
                    "source": record.get("source", ""),
                    "embedding": json.loads(record.get("embedding", "[]"))
                }
                self.knowledge_data.append(knowledge_item)

            logger.info(f"Loaded {len(knowledge_records)} knowledge entries from database")

        except Exception as e:
            logger.error(f"Failed to load knowledge from database: {str(e)}")


# Create global instance
rag_kb = RAGKnowledgeBase()
