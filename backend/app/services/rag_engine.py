import asyncio
import os
from typing import List, Dict, Any, Optional
import json

# Pinecone will be imported inside methods to handle import errors gracefully
PINECONE_AVAILABLE = None  # Will be set when first import attempt is made
Pinecone = None
ServerlessSpec = None


def _import_pinecone():
    """Import Pinecone only when needed"""
    global PINECONE_AVAILABLE, Pinecone, ServerlessSpec
    if PINECONE_AVAILABLE is not None:  # Already attempted import
        return PINECONE_AVAILABLE
    
    try:
        # Handle the Pinecone package rename issue
        try:
            from pinecone import Pinecone as PineconeClient, ServerlessSpec as ServerlessSpecClient
        except Exception:
            # This handles the Pinecone package rename error
            PINECONE_AVAILABLE = False
            print("Warning: Pinecone not available. RAG functionality will be disabled.")
            return False
        
        Pinecone = PineconeClient
        ServerlessSpec = ServerlessSpecClient
        PINECONE_AVAILABLE = True
        return True
    except ImportError:
        PINECONE_AVAILABLE = False
        print("Warning: Pinecone not available. RAG functionality will be disabled.")
        return False


class RAGEngine:
    """
    Pinecone-based RAG engine for retrieving:
    - Historical incident patterns
    - Runbook recommendations
    - Similar past resolutions
    
    Uses Pinecone's inference API for embeddings (no need for separate model)
    """
    
    def __init__(self):
        self.api_key = os.getenv('PINECONE_API_KEY')
        self.environment = os.getenv('PINECONE_ENVIRONMENT', 'us-east-1')
        self.index_name = os.getenv('PINECONE_INDEX_NAME', 'incident-commander')
        
        # Initialize Pinecone
        self.pc = None
        self.index = None
        
        # Using Pinecone's multilingual-e5-large model (1024 dimensions)
        self.embedding_model = "multilingual-e5-large"
        self.embedding_dim = 1024
        
        if not PINECONE_AVAILABLE:
            print("RAG Engine initialized in fallback mode - no vector search available")
    
    async def initialize(self):
        """Initialize or connect to Pinecone index"""
        if not _import_pinecone():
            print("Pinecone not available, skipping initialization")
            return
        
        try:
            # Initialize Pinecone client
            self.pc = Pinecone(api_key=self.api_key)
            
            # Check if index exists
            def list_indexes():
                return self.pc.list_indexes()
            
            existing_indexes = await asyncio.to_thread(list_indexes)
            index_names = [idx.name for idx in existing_indexes]
            
            if self.index_name not in index_names:
                # Create new index with serverless spec and inference embeddings
                def create_index():
                    self.pc.create_index(
                        name=self.index_name,
                        dimension=self.embedding_dim,
                        metric='cosine',
                        spec=ServerlessSpec(
                            cloud='aws',
                            region=self.environment
                        )
                    )
                await asyncio.to_thread(create_index)
                print(f"Created new Pinecone index: {self.index_name}")
            
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            print(f"Connected to Pinecone index: {self.index_name}")
            
        except Exception as e:
            print(f"Error initializing Pinecone: {e}")
            raise
    
    def _create_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using Pinecone's inference API.
        Falls back to a simple hash-based embedding if inference fails.
        """
        if not _import_pinecone():
            # If Pinecone is not available, use fallback directly
            import hashlib
            hash_obj = hashlib.sha256(text.encode())
            hash_bytes = hash_obj.digest()
            embedding = []
            for i in range(0, len(hash_bytes) * 8, 8):
                byte_idx = i // 8
                if byte_idx < len(hash_bytes):
                    embedding.append(float(hash_bytes[byte_idx]) / 255.0)
            while len(embedding) < self.embedding_dim:
                embedding.append(0.0)
            return embedding[:self.embedding_dim]
        
        try:
            # Use Pinecone's inference API
            embeddings = self.pc.inference.embed(
                model=self.embedding_model,
                inputs=[text],
                parameters={"input_type": "passage"}
            )
            return embeddings[0]['values']
        except Exception as e:
            print(f"Warning: Pinecone inference failed, using fallback: {e}")
            # Fallback
            import hashlib
            hash_obj = hashlib.sha256(text.encode())
            hash_bytes = hash_obj.digest()
            embedding = []
            for i in range(0, len(hash_bytes) * 8, 8):
                byte_idx = i // 8
                if byte_idx < len(hash_bytes):
                    embedding.append(float(hash_bytes[byte_idx]) / 255.0)
            while len(embedding) < self.embedding_dim:
                embedding.append(0.0)
            return embedding[:self.embedding_dim]
    
    async def upsert_incident(self, incident_id: str, incident_data: Dict[str, Any]):
        """
        Store incident in vector database.
        """
        if not _import_pinecone():
            # Skip upsert if Pinecone is not available
            return
        
        if not self.index:
            await self.initialize()
        
        # Create searchable text
        searchable_text = f"Title: {incident_data.get('title', '')}\nService: {incident_data.get('service', '')}\nDescription: {incident_data.get('description', '')}\nRoot Cause: {incident_data.get('root_cause', '')}\nResolution: {incident_data.get('resolution', '')}"
        
        # Generate embedding (this hit the inference API which is also sync)
        embedding = await asyncio.to_thread(self._create_embedding, searchable_text)
        
        # Prepare metadata
        metadata = {
            'incident_id': incident_id,
            'title': incident_data.get('title', '')[:200],
            'service': incident_data.get('service', ''),
            'severity': incident_data.get('severity', 'medium'),
            'root_cause': incident_data.get('root_cause', '')[:500],
            'resolution': incident_data.get('resolution', '')[:500],
        }
        
        # Upsert to Pinecone
        def do_upsert():
            self.index.upsert(vectors=[(incident_id, embedding, metadata)])
            
        await asyncio.to_thread(do_upsert)
    
    async def upsert_runbook(self, runbook_id: str, runbook_data: Dict[str, Any]):
        """
        Store runbook in vector database.
        """
        if not _import_pinecone():
            # Skip upsert if Pinecone is not available
            return
        
        if not self.index:
            await self.initialize()
        
        searchable_text = f"Title: {runbook_data.get('title', '')}\nService: {runbook_data.get('service', '')}\nProblem: {runbook_data.get('problem', '')}\nSolution: {runbook_data.get('solution', '')}"
        
        embedding = await asyncio.to_thread(self._create_embedding, searchable_text)
        
        metadata = {
            'runbook_id': runbook_id,
            'type': 'runbook',
            'title': runbook_data.get('title', '')[:200],
            'service': runbook_data.get('service', ''),
            'problem': runbook_data.get('problem', '')[:500],
            'solution': runbook_data.get('solution', '')[:500],
        }
        
        def do_upsert():
            self.index.upsert(vectors=[(runbook_id, embedding, metadata)])
            
        await asyncio.to_thread(do_upsert)
    
    async def search_similar_incidents(
        self, 
        query: str, 
        service: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar incidents using semantic search.
        """
        if not _import_pinecone():
            # Return empty results if Pinecone is not available
            return []
        
        if not self.index:
            await self.initialize()
        
        # Generate query embedding
        query_embedding = await asyncio.to_thread(self._create_embedding, query)
        
        # Build filter
        filter_dict = {}
        if service:
            filter_dict['service'] = service
        
        # Search
        try:
            def do_query():
                return self.index.query(
                    vector=query_embedding,
                    top_k=top_k,
                    include_metadata=True,
                    filter=filter_dict if filter_dict else None
                )
            
            results = await asyncio.to_thread(do_query)
            
            # Format results
            similar_incidents = []
            for match in results.get('matches', []):
                similar_incidents.append({
                    'id': match['id'],
                    'score': match['score'],
                    'metadata': match.get('metadata', {})
                })
            
            return similar_incidents
        
        except Exception as e:
            print(f"Error searching Pinecone: {e}")
            return []
    
    async def get_relevant_context(
        self, 
        compressed_context: Dict[str, Any],
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Get relevant historical incidents and runbooks based on compressed context.
        
        Args:
            compressed_context: Output from ContextCompressor
            top_k: Number of results per category
        
        Returns:
            Dict with similar_incidents and relevant_runbooks
        """
        # Build query from compressed context
        query_parts = []
        
        # Add error clusters
        if compressed_context.get('error_clusters'):
            top_errors = compressed_context['error_clusters'][:3]
            for cluster in top_errors:
                query_parts.append(f"{cluster['service']}: {cluster['error_pattern']}")
        
        # Add anomalous metrics
        if compressed_context.get('anomalous_metrics'):
            top_anomalies = compressed_context['anomalous_metrics'][:2]
            for anomaly in top_anomalies:
                query_parts.append(f"{anomaly['metric_name']} {anomaly['anomaly_type']}")
        
        query = " ".join(query_parts)
        
        # Get affected services
        services = compressed_context.get('affected_services', [])
        primary_service = services[0] if services else None
        
        # Search for similar incidents
        similar_incidents = await self.search_similar_incidents(
            query=query,
            service=primary_service,
            top_k=top_k
        )
        
        return {
            'similar_incidents': similar_incidents,
            'query_used': query
        }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        if not _import_pinecone():
            return {'total_vectors': 0, 'dimension': 0, 'index_fullness': 0, 'status': 'disabled'}
        
        if not self.index:
            await self.initialize()
        
        try:
            stats = self.index.describe_index_stats()
            return {
                'total_vectors': stats.get('total_vector_count', 0),
                'dimension': stats.get('dimension', 0),
                'index_fullness': stats.get('index_fullness', 0)
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}


# Global instance
rag_engine = RAGEngine()
