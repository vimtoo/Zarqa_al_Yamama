"""
Qdrant Vector Database Client
Handles embeddings for news and reports with cloud support
"""

import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, Range
import hashlib

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generates embeddings using sentence-transformers.
    Falls back to simple hashing if sentence-transformers is unavailable.
    """
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the embedding model"""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
        except ImportError:
            logger.warning("sentence-transformers not available, using fallback embeddings")
            self.model = None
        except Exception as e:
            logger.warning(f"Could not load embedding model: {str(e)}, using fallback")
            self.model = None
    
    def generate(self, text: str) -> List[float]:
        """
        Generate embedding for text
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats (embedding vector)
        """
        if self.model is not None:
            try:
                embedding = self.model.encode(text, convert_to_numpy=True)
                return embedding.tolist()
            except Exception as e:
                logger.warning(f"Embedding generation failed: {str(e)}")
                return self._fallback_embedding(text)
        else:
            return self._fallback_embedding(text)
    
    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if self.model is not None:
            try:
                embeddings = self.model.encode(texts, convert_to_numpy=True)
                return [emb.tolist() for emb in embeddings]
            except Exception as e:
                logger.warning(f"Batch embedding generation failed: {str(e)}")
                return [self._fallback_embedding(text) for text in texts]
        else:
            return [self._fallback_embedding(text) for text in texts]
    
    def _fallback_embedding(self, text: str) -> List[float]:
        """
        Generate a deterministic fallback embedding using hashing.
        This is NOT a semantic embedding but provides consistent vectors.
        """
        import hashlib
        import struct
        
        # Create a hash of the text
        hash_obj = hashlib.sha256(text.encode('utf-8'))
        hash_bytes = hash_obj.digest()
        
        # Extend hash to reach desired dimension
        embedding = []
        while len(embedding) < self.dimension:
            for i in range(0, len(hash_bytes), 4):
                if len(embedding) >= self.dimension:
                    break
                chunk = hash_bytes[i:i+4]
                if len(chunk) == 4:
                    value = struct.unpack('f', chunk)[0]
                    # Normalize to [-1, 1]
                    embedding.append(max(-1.0, min(1.0, value)))
            
            # Re-hash if we need more values
            if len(embedding) < self.dimension:
                hash_obj = hashlib.sha256(hash_bytes)
                hash_bytes = hash_obj.digest()
        
        return embedding[:self.dimension]


class QdrantVectorDB:
    """Client for Qdrant vector database with cloud support"""
    
    def __init__(self):
        # Initialize cloud client with API key
        self.client = self._create_client()
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.vector_size = settings.EMBEDDING_DIMENSION
        self.embedding_generator = EmbeddingGenerator()
        
        self._initialize_collection()
    
    def _create_client(self) -> QdrantClient:
        """Create Qdrant client with proper authentication"""
        url = settings.QDRANT_URL
        api_key = settings.QDRANT_API_KEY
        
        if api_key:
            logger.info(f"Connecting to Qdrant cloud at: {url}")
            return QdrantClient(
                url=url,
                api_key=api_key,
                timeout=30.0
            )
        else:
            logger.info(f"Connecting to Qdrant without auth at: {url}")
            return QdrantClient(url=url, timeout=30.0)
    
    def _initialize_collection(self):
        """Initialize or verify collection exists"""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating Qdrant collection: {self.collection_name}")
                
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Collection {self.collection_name} created successfully")
            else:
                logger.info(f"Collection {self.collection_name} already exists")
                
        except Exception as e:
            logger.error(f"Error initializing Qdrant collection: {str(e)}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using the embedding generator
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        return self.embedding_generator.generate(text)
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        return self.embedding_generator.generate_batch(texts)
    
    def add_news_embedding(
        self,
        news_id: str,
        text: str,
        metadata: Dict[str, Any],
        embedding: List[float] = None
    ) -> bool:
        """
        Add news article embedding to vector database
        
        Args:
            news_id: Unique identifier for the news item
            text: Text content to embed (if embedding not provided)
            metadata: Associated metadata (title, source, sentiment, etc.)
            embedding: Pre-computed embedding (optional)
            
        Returns:
            True if successful
        """
        try:
            # Generate embedding if not provided
            if embedding is None:
                embedding = self.generate_embedding(text)
            
            # Generate integer ID from string
            point_id = int(hashlib.md5(news_id.encode()).hexdigest()[:8], 16)
            
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "news_id": news_id,
                    **metadata
                }
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.info(f"Added news embedding: {news_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding news embedding: {str(e)}")
            return False
    
    def add_news_batch(
        self,
        news_items: List[Dict[str, Any]]
    ) -> int:
        """
        Add multiple news items in batch
        
        Args:
            news_items: List of dicts with 'id', 'text', and 'metadata' keys
            
        Returns:
            Number of items added successfully
        """
        try:
            texts = [item['text'] for item in news_items]
            embeddings = self.generate_embeddings_batch(texts)
            
            points = []
            for i, item in enumerate(news_items):
                point_id = int(hashlib.md5(item['id'].encode()).hexdigest()[:8], 16)
                points.append(PointStruct(
                    id=point_id,
                    vector=embeddings[i],
                    payload={
                        "news_id": item['id'],
                        **item.get('metadata', {})
                    }
                ))
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Added {len(points)} news embeddings in batch")
            return len(points)
            
        except Exception as e:
            logger.error(f"Error adding news batch: {str(e)}")
            return 0
    
    def search_similar_news(
        self,
        query_text: str,
        limit: int = 10,
        score_threshold: float = 0.5,
        query_embedding: List[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar news articles
        
        Args:
            query_text: Query text to search for
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            query_embedding: Pre-computed query embedding (optional)
            
        Returns:
            List of similar news items with scores
        """
        try:
            # Generate query embedding if not provided
            if query_embedding is None:
                query_embedding = self.generate_embedding(query_text)
            
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold
            )
            
            similar_news = []
            for result in results:
                similar_news.append({
                    'id': result.id,
                    'score': result.score,
                    'metadata': result.payload
                })
            
            return similar_news
            
        except Exception as e:
            logger.error(f"Error searching similar news: {str(e)}")
            return []
    
    def search_by_theme(
        self,
        theme: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search news by theme
        
        Args:
            theme: Theme to search for
            limit: Maximum number of results
            
        Returns:
            List of news items matching theme
        """
        try:
            results = self.client.scroll(
                collection_name=self.collection_name,
                limit=limit,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="themes",
                            match=MatchValue(value=theme)
                        )
                    ]
                )
            )
            
            news_items = []
            for point in results[0]:
                news_items.append({
                    'id': point.id,
                    'metadata': point.payload
                })
            
            return news_items
            
        except Exception as e:
            logger.error(f"Error searching by theme: {str(e)}")
            return []
    
    def get_news_by_sentiment(
        self,
        sentiment_min: float = -1.0,
        sentiment_max: float = 1.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get news items within sentiment range
        
        Args:
            sentiment_min: Minimum sentiment score
            sentiment_max: Maximum sentiment score
            limit: Maximum number of results
            
        Returns:
            List of news items with sentiment in range
        """
        try:
            results = self.client.scroll(
                collection_name=self.collection_name,
                limit=limit,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="sentiment_score",
                            range=Range(
                                gte=sentiment_min,
                                lte=sentiment_max
                            )
                        )
                    ]
                )
            )
            
            news_items = []
            for point in results[0]:
                news_items.append({
                    'id': point.id,
                    'metadata': point.payload
                })
            
            return news_items
            
        except Exception as e:
            logger.error(f"Error getting news by sentiment: {str(e)}")
            return []
    
    def delete_old_embeddings(self, days: int = 30) -> bool:
        """
        Delete embeddings older than specified days
        
        Args:
            days: Number of days to keep
            
        Returns:
            True if successful
        """
        try:
            from datetime import datetime, timedelta
            
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="timestamp",
                            range=Range(lt=cutoff_date)
                        )
                    ]
                )
            )
            
            logger.info(f"Deleted embeddings older than {days} days")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting old embeddings: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            
            return {
                'name': self.collection_name,
                'points_count': collection_info.points_count,
                'vectors_count': collection_info.vectors_count,
                'indexed_vectors_count': getattr(collection_info, 'indexed_vectors_count', 0),
                'status': collection_info.status.value if hasattr(collection_info.status, 'value') else str(collection_info.status)
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {}
    
    def health_check(self) -> bool:
        """Check if Qdrant connection is healthy"""
        try:
            collections = self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {str(e)}")
            return False


# Singleton instance
qdrant_db = None

def get_qdrant_db() -> QdrantVectorDB:
    """Get or create Qdrant database instance"""
    global qdrant_db
    if qdrant_db is None:
        qdrant_db = QdrantVectorDB()
    return qdrant_db
