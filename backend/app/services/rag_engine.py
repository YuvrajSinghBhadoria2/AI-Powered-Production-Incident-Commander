import os
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
import json


class RAGEngine:
    """
    Pinecone-based RAG engine for retrieving:
    - Historical incident patterns
    - Runbook recommendations
    - Similar past resolutions
    """
    
    def __init__(self):
        self.api_key = os.getenv('PINECONE_API_KEY')
        self.environment = os.getenv('PINECONE_ENVIRONMENT', 'us-east-1')
        self.index_name = os.getenv('PINECONE_INDEX_NAME', 'incident-commander')
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=self.api_key)
        
        # Initialize embedding model (384 dimensions)
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.embedding_dim = 384
        
        self.index = None
    
    async def initialize(self):
        """Initialize or connect to Pinecone index"""
        try:
            # Check if index exists
            existing_indexes = self.pc.list_indexes()
            index_names = [idx['name'] for idx in existing_indexes]
            
            if self.index_name not in index_names:
                # Create new index with serverless spec
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.embedding_dim,
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region=self.environment
                    )
                )
                print(f"Created new Pinecone index: {self.index_name}")
            
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            print(f"Connected to Pinecone index: {self.index_name}")
            
        except Exception as e:
            print(f"Error initializing Pinecone: {e}")
            raise
    
    def _create_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        embedding = self.embedding_model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
    
    async def upsert_incident(self, incident_id: str, incident_data: Dict[str, Any]):
        """
        Store incident in vector database.
        
        Args:
            incident_id: Unique incident identifier
            incident_data: Dict with keys: title, description, root_cause, resolution, service
        """
        if not self.index:
            await self.initialize()
        
        # Create searchable text
        searchable_text = f"""
        Title: {incident_data.get('title', '')}
        Service: {incident_data.get('service', '')}
        Description: {incident_data.get('description', '')}
        Root Cause: {incident_data.get('root_cause', '')}
        Resolution: {incident_data.get('resolution', '')}
        """.strip()
        
        # Generate embedding
        embedding = self._create_embedding(searchable_text)
        
        # Prepare metadata (Pinecone has size limits, keep it concise)
        metadata = {
            'incident_id': incident_id,
            'title': incident_data.get('title', '')[:200],
            'service': incident_data.get('service', ''),
            'severity': incident_data.get('severity', 'medium'),
            'root_cause': incident_data.get('root_cause', '')[:500],
            'resolution': incident_data.get('resolution', '')[:500],
        }
        
        # Upsert to Pinecone
        self.index.upsert(vectors=[(incident_id, embedding, metadata)])
    
    async def upsert_runbook(self, runbook_id: str, runbook_data: Dict[str, Any]):
        """
        Store runbook in vector database.
        
        Args:
            runbook_id: Unique runbook identifier
            runbook_data: Dict with keys: title, problem, solution, service
        """
        if not self.index:
            await self.initialize()
        
        # Create searchable text
        searchable_text = f"""
        Title: {runbook_data.get('title', '')}
        Service: {runbook_data.get('service', '')}
        Problem: {runbook_data.get('problem', '')}
        Solution: {runbook_data.get('solution', '')}
        """.strip()
        
        # Generate embedding
        embedding = self._create_embedding(searchable_text)
        
        # Prepare metadata
        metadata = {
            'runbook_id': runbook_id,
            'type': 'runbook',
            'title': runbook_data.get('title', '')[:200],
            'service': runbook_data.get('service', ''),
            'problem': runbook_data.get('problem', '')[:500],
            'solution': runbook_data.get('solution', '')[:500],
        }
        
        # Upsert to Pinecone
        self.index.upsert(vectors=[(runbook_id, embedding, metadata)])
    
    async def search_similar_incidents(
        self, 
        query: str, 
        service: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar incidents using semantic search.
        
        Args:
            query: Search query (incident description)
            service: Optional service filter
            top_k: Number of results to return
        
        Returns:
            List of similar incidents with metadata and similarity scores
        """
        if not self.index:
            await self.initialize()
        
        # Generate query embedding
        query_embedding = self._create_embedding(query)
        
        # Build filter
        filter_dict = {}
        if service:
            filter_dict['service'] = service
        
        # Search
        try:
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict if filter_dict else None
            )
            
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
