"""
RAG index builder for NICE/BDA guidelines
"""
import os
import json
import numpy as np
import faiss
from typing import List, Dict
from pathlib import Path
import openai
from openai import OpenAI

class RAGIndexBuilder:
    """Build and manage FAISS index for diabetes guidelines"""
    
    def __init__(self, api_key: str = None):
        try:
            # Get API key from parameter or environment variable
            self.api_key = api_key or os.getenv('OPENAI_API_KEY')
            if not self.api_key:
                raise ValueError("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")
            
            # Verify the API key format (starts with 'sk-' or 'sk-proj-')
            if not (self.api_key.startswith('sk-') or self.api_key.startswith('sk-proj-')):
                raise ValueError("Invalid API key format. It should start with 'sk-' or 'sk-proj-'")
            
            # Initialize OpenAI client
            self.client = OpenAI(api_key=self.api_key)
            
            # Test the API key with a simple request
            try:
                models = self.client.models.list()
                if not models.data:
                    raise ValueError("API key is invalid or has no access to models")
            except Exception as e:
                if "Incorrect API key" in str(e):
                    raise ValueError("The provided API key is invalid or revoked.")
                elif "Rate limit" in str(e):
                    raise ValueError("API rate limit exceeded. Please try again later.")
                else:
                    raise ValueError(f"Failed to verify API key: {str(e)}")
            
            # Set embedding model
            self.embedding_model = os.getenv('EMBEDDING_MODEL', 'text-embedding-ada-002')
            self.chunk_size = 1000
            self.overlap = 200
            
            # Log successful initialization (without exposing the key)
            print("✅ Successfully initialized OpenAI client")
            
        except Exception as e:
            error_msg = str(e)
            # Don't expose API key in error messages
            if self.api_key and len(self.api_key) > 8:
                error_msg = error_msg.replace(self.api_key, f"{self.api_key[:4]}...{self.api_key[-4:]}")
            raise ValueError(f"Failed to initialize RAGIndexBuilder: {error_msg}")
        
    def load_guidelines(self) -> List[Dict]:
        """Load curated NICE/BDA text snippets"""
        guidelines = [
            {
                "id": "nice_ng17_hba1c",
                "source": "NICE NG17",
                "section": "Blood glucose management",
                "text": """Adults with type 1 diabetes should aim for HbA1c level of 48 mmol/mol (6.5%) or lower to minimise the risk of long-term vascular complications. However, this target should be individualised based on factors including hypoglycaemia awareness, occupational considerations, and presence of complications. For adults at higher risk of severe hypoglycaemia or with limited life expectancy, less stringent targets of 53 mmol/mol (7.0%) may be appropriate."""
            },
            {
                "id": "nice_ng28_bp",
                "source": "NICE NG28", 
                "section": "Blood pressure management",
                "text": """For adults with type 2 diabetes, offer antihypertensive drug treatment if blood pressure is consistently above 140/90 mmHg. The target blood pressure should be below 140/90 mmHg (below 130/80 mmHg if kidney, eye or cerebrovascular damage is present). ACE inhibitors or ARBs are first-line treatment for adults with diabetes and hypertension."""
            },
            {
                "id": "nice_ng28_lipids",
                "source": "NICE NG28",
                "section": "Lipid management", 
                "text": """Offer atorvastatin 20mg to adults with type 2 diabetes who have a 10-year cardiovascular risk of 10% or more. For primary prevention, aim for more than 40% reduction in non-HDL cholesterol. For secondary prevention, the target LDL cholesterol is less than 2.0 mmol/L. Consider higher intensity statin if targets not achieved."""
            },
            {
                "id": "bda_carb_counting",
                "source": "BDA Guidelines",
                "section": "Carbohydrate counting",
                "text": """Carbohydrate counting enables flexible meal planning and improved glycaemic control in people with type 1 diabetes using intensive insulin regimens. One carbohydrate portion typically contains 10-15g of carbohydrate. Insulin-to-carbohydrate ratios typically range from 1:8 to 1:15 but must be individualised. Regular review and adjustment is essential."""
            },
            {
                "id": "nice_ng17_hypo",
                "source": "NICE NG17",
                "section": "Hypoglycaemia management",
                "text": """Severe hypoglycaemia should be avoided as it increases cardiovascular risk and impairs quality of life. Adults experiencing frequent non-severe hypoglycaemia or any severe hypoglycaemia should have their treatment regimen reviewed. Consider structured education, glucose monitoring technology, and insulin regimen optimisation. Emergency glucagon should be prescribed for those at risk of severe hypoglycaemia."""
            },
            {
                "id": "nice_screening",
                "source": "NICE Diabetes Screening",
                "section": "Annual screening",
                "text": """Annual screening should include: diabetic retinopathy (digital photography), diabetic kidney disease (eGFR and ACR), foot assessment (neuropathy and vascular status), blood pressure monitoring, and lipid profile. Influenza vaccination should be offered annually, with pneumococcal vaccination every 5 years for adults with diabetes."""
            }
        ]
        return guidelines
        
    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size - self.overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunks.append(' '.join(chunk_words))
            
        return chunks
    
    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for text chunks"""
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=texts
        )
        return np.array([emb.embedding for emb in response.data])
    
    def build_index(self, save_path: str = "data/rag"):
        """Build FAISS index from guidelines with proper vector normalization"""
        try:
            # Load guidelines
            guidelines = self.load_guidelines()
            if not guidelines:
                raise ValueError("No guidelines found to index")
            
            # Prepare chunks and metadata
            all_chunks = []
            metadata = []
            
            print("📚 Processing guidelines...")
            for guideline in guidelines:
                chunks = self.chunk_text(guideline['text'])
                for i, chunk in enumerate(chunks):
                    all_chunks.append(chunk)
                    metadata.append({
                        "id": f"{guideline['id']}_chunk_{i}",
                        "source": guideline['source'],
                        "section": guideline['section']
                    })
            
            if not all_chunks:
                raise ValueError("No text chunks were generated from guidelines")
            
            # Generate embeddings
            print(f"🔄 Generating embeddings for {len(all_chunks)} text chunks...")
            embeddings = self.get_embeddings(all_chunks)
            
            # Convert to numpy array and ensure float32
            import numpy as np
            embeddings = np.array(embeddings).astype('float32')
            
            # Normalize vectors to unit length (L2 norm)
            print("📏 Normalizing vectors...")
            faiss.normalize_L2(embeddings)
            
            # Get vector dimension
            dimension = embeddings.shape[1]
            print(f"🔢 Vector dimension: {dimension}")
            
            # Create FAISS index with inner product (cosine) similarity
            print("🏗️ Creating FAISS index...")
            index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            
            # Add vectors to index
            print("📥 Adding vectors to index...")
            index.add(embeddings)
            
            # Verify index
            if index.ntotal == 0:
                raise ValueError("Failed to add vectors to index")
            
            # Create output directory if it doesn't exist
            os.makedirs(save_path, exist_ok=True)
            
            # Save index
            faiss.write_index(index, f"{save_path}/index.faiss")
            
            # Save metadata
            with open(f"{save_path}/metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Index built with {index.ntotal} vectors and saved to {save_path}")
            return index, metadata
            
        except Exception as e:
            print(f"❌ Error building index: {str(e)}")
            raise

if __name__ == "__main__":
    builder = RAGIndexBuilder()
    builder.build_index()
