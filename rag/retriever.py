"""
RAG retriever for diabetes guidelines
"""
import os
import json
import numpy as np
import faiss
from typing import List, Dict
from pathlib import Path
import openai
from openai import OpenAI

class RAGRetriever:
    """Retrieve relevant guidelines from FAISS index"""
    
    def __init__(self, index_path: str = "data/rag", api_key: str = None):
        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        self.embedding_model = "text-embedding-ada-002"
        self.index_path = Path(index_path)
        
        # Load index and metadata
        self.index = None
        self.metadata = []
        self._load_index()
    
    def _load_index(self):
        """Load FAISS index and metadata"""
        index_file = self.index_path / "index.faiss"
        metadata_file = self.index_path / "metadata.json"
        
        if not index_file.exists() or not metadata_file.exists():
            print("Index not found. Please run index_builder.py first.")
            return
            
        self.index = faiss.read_index(str(index_file))
        
        with open(metadata_file, 'r') as f:
            self.metadata = json.load(f)
            
        print(f"Loaded index with {len(self.metadata)} chunks")
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for a single text"""
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=[text]
            )
            # Convert to numpy array and ensure float32
            embedding = np.array([response.data[0].embedding], dtype='float32')
            return embedding
        except Exception as e:
            print(f"Error getting embedding: {str(e)}")
            raise
    
    def retrieve(self, query: str, k: int = 4) -> List[Dict]:
        """
        Retrieve top-k relevant guidelines
        
        Returns: List of {id, source, section, text}
        """
        if not self.index:
            return []
            
        try:
            # Get query embedding
            query_embedding = self.get_embedding(query)
            
            # Ensure query_embedding is 2D and float32
            if len(query_embedding.shape) == 1:
                query_embedding = query_embedding.reshape(1, -1)
            
            # Normalize for cosine similarity
            faiss.normalize_L2(query_embedding)
            
            # Ensure k doesn't exceed number of vectors in index
            k = min(k, self.index.ntotal) if self.index.ntotal > 0 else 0
            if k == 0:
                return []
            
            # Search index
            scores, indices = self.index.search(query_embedding, k)
            
            # Format results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.metadata):
                    result = self.metadata[idx].copy()
                    result['relevance_score'] = float(score)
                    results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Error in retrieve: {str(e)}")
            return []
    
    def build_retrieval_query(self, patient_data: Dict) -> str:
        """Build retrieval query from patient context"""
        query_parts = []
        
        # Add diabetes type
        if patient_data.get('diabetes_type'):
            query_parts.append(f"{patient_data['diabetes_type']} diabetes")
        
        # Add key clinical areas based on data
        labs = patient_data.get('labs', {})
        if labs.get('hba1c_pct'):
            query_parts.append("HbA1c blood glucose control")
        
        if patient_data.get('bp_sys'):
            query_parts.append("blood pressure hypertension")
            
        if labs.get('lipids'):
            query_parts.append("cholesterol lipids cardiovascular risk")
        
        if patient_data.get('hypos_90d', 0) > 0:
            query_parts.append("hypoglycaemia management")
            
        # Add medications context
        meds = patient_data.get('meds', [])
        if any('insulin' in med.get('name', '').lower() for med in meds):
            query_parts.append("insulin therapy")
        
        # Add screening needs
        query_parts.append("screening retinopathy kidney foot")
        
        query = ' '.join(query_parts)
        return query or "diabetes management guidelines"

if __name__ == "__main__":
    retriever = RAGRetriever()
    
    # Test retrieval
    test_query = "T1DM HbA1c targets hypoglycaemia"
    results = retriever.retrieve(test_query, k=3)
    
    print(f"Query: {test_query}")
    print(f"Found {len(results)} results:")
    for result in results:
        print(f"- {result['source']}: {result['section']} (score: {result['relevance_score']:.3f})")
        print(f"  {result['text'][:100]}...")
        print()
