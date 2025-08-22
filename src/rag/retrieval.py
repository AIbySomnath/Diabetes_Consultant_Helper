"""
RAG Retrieval Pipeline for Diabetes Report Generator
Implements hybrid retrieval with UK clinical guidelines
"""

import os
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import streamlit as st

class RAGPipeline:
    """Retrieval-Augmented Generation pipeline for UK diabetes guidelines"""
    
    def __init__(self):
        """Initialize RAG pipeline with mock knowledge base"""
        
        # In production, this would connect to ChromaDB with real embeddings
        # For POC, using mock data representing UK guidelines
        
        self.knowledge_base = self._load_mock_knowledge_base()
        self.sources_metadata = self._load_sources_metadata()
    
    def _load_mock_knowledge_base(self) -> List[Dict]:
        """Load mock UK diabetes guidelines knowledge base"""
        
        return [
            {
                "id": "nice_ng28_001",
                "content": "For adults with type 2 diabetes, agree an individualised HbA1c target. For adults on a drug associated with hypoglycaemia, support them to aim for an HbA1c level of 53 mmol/mol (7.0%).",
                "source": "NICE NG28",
                "title": "Type 2 diabetes in adults: management",
                "url": "https://www.nice.org.uk/guidance/ng28",
                "updated": "2022-03-31",
                "section": "Blood glucose management"
            },
            {
                "id": "nice_ng28_002",
                "content": "Advise adults with type 2 diabetes that lifestyle changes (losing weight if overweight, eating healthily, taking regular exercise) can improve blood glucose control and reduce cardiovascular risk.",
                "source": "NICE NG28",
                "title": "Type 2 diabetes in adults: management",
                "url": "https://www.nice.org.uk/guidance/ng28",
                "updated": "2022-03-31",
                "section": "Lifestyle management"
            },
            {
                "id": "nhs_diet_001",
                "content": "Follow the NHS Eatwell Guide. Aim to eat: plenty of fruit and vegetables - at least 5 portions a day; starchy foods like potatoes, bread, rice or pasta - choose wholegrain varieties; some dairy or dairy alternatives; beans, pulses, fish, eggs, meat and other proteins.",
                "source": "NHS",
                "title": "Healthy eating for type 2 diabetes",
                "url": "https://www.nhs.uk/conditions/type-2-diabetes/food-and-keeping-active/",
                "updated": "2023-06-15",
                "section": "Diet advice"
            },
            {
                "id": "nhs_activity_001",
                "content": "Adults should aim to do at least 150 minutes of moderate intensity activity a week or 75 minutes of vigorous intensity activity a week. Spread exercise evenly over 4 to 5 days a week, or every day.",
                "source": "NHS",
                "title": "Physical activity guidelines",
                "url": "https://www.nhs.uk/live-well/exercise/",
                "updated": "2023-04-20",
                "section": "Exercise recommendations"
            },
            {
                "id": "diabetes_uk_001",
                "content": "Self-monitoring of blood glucose is recommended for people with type 2 diabetes who are on insulin or medications that can cause hypoglycaemia. Test before meals and 2 hours after to see how food affects your levels.",
                "source": "Diabetes UK",
                "title": "Blood glucose monitoring",
                "url": "https://www.diabetes.org.uk/guide-to-diabetes/managing-your-diabetes/testing",
                "updated": "2023-07-10",
                "section": "Monitoring"
            },
            {
                "id": "bda_001",
                "content": "Use the plate method for portion control: fill half your plate with non-starchy vegetables, one quarter with lean protein, and one quarter with carbohydrate foods. Choose foods with a low glycaemic index where possible.",
                "source": "BDA",
                "title": "Food Fact Sheet - Diabetes",
                "url": "https://www.bda.uk.com/resource/diabetes.html",
                "updated": "2023-05-01",
                "section": "Portion control"
            },
            {
                "id": "nice_ng28_003",
                "content": "For adults with type 2 diabetes, if HbA1c levels are not adequately controlled by a single drug and rise to 58 mmol/mol (7.5%) or higher, reinforce advice about diet, lifestyle and adherence to drug treatment, and intensify drug treatment.",
                "source": "NICE NG28",
                "title": "Type 2 diabetes in adults: management",
                "url": "https://www.nice.org.uk/guidance/ng28",
                "updated": "2022-03-31",
                "section": "Treatment escalation"
            },
            {
                "id": "nhs_sick_day_001",
                "content": "During illness: continue taking diabetes medications, check blood glucose more frequently (every 2-4 hours), drink plenty of fluids, try to eat normally. Seek urgent medical advice if blood glucose stays high (over 15 mmol/L) or you have ketones.",
                "source": "NHS",
                "title": "Sick day rules for diabetes",
                "url": "https://www.nhs.uk/conditions/type-2-diabetes/",
                "updated": "2023-06-01",
                "section": "Sick day management"
            }
        ]
    
    def _load_sources_metadata(self) -> Dict:
        """Load metadata for all knowledge sources"""
        
        return {
            "NICE NG28": {
                "full_name": "NICE Guideline NG28 - Type 2 diabetes in adults: management",
                "authority": "National Institute for Health and Care Excellence",
                "last_updated": "March 2022",
                "scope": "Adults with type 2 diabetes"
            },
            "NHS": {
                "full_name": "NHS Diabetes Guidance",
                "authority": "National Health Service",
                "last_updated": "2023",
                "scope": "General population and diabetes patients"
            },
            "Diabetes UK": {
                "full_name": "Diabetes UK Clinical Guidance",
                "authority": "Diabetes UK Charity",
                "last_updated": "2023",
                "scope": "People living with diabetes"
            },
            "BDA": {
                "full_name": "British Dietetic Association Food Facts",
                "authority": "British Dietetic Association",
                "last_updated": "2023",
                "scope": "Dietary management for diabetes"
            }
        }
    
    def build_retrieval_query(
        self,
        patient_data: Dict,
        labs_data: Dict,
        lifestyle_data: Dict
    ) -> str:
        """Build optimized retrieval query from patient context"""
        
        query_parts = []
        
        # Add condition-specific terms
        query_parts.append("type 2 diabetes management UK adults")
        
        # Add glycaemic control context
        hba1c = labs_data.get('hba1c')
        if hba1c:
            if hba1c >= 10:
                query_parts.append("very poor glycaemic control urgent intervention")
            elif hba1c >= 8:
                query_parts.append("suboptimal glycaemic control intensification")
            elif hba1c >= 7:
                query_parts.append("target HbA1c lifestyle modification")
            else:
                query_parts.append("good glycaemic control maintenance")
        
        # Add BP context
        bp_sys = labs_data.get('bp_systolic')
        if bp_sys and bp_sys >= 140:
            query_parts.append("hypertension blood pressure management")
        
        # Add lifestyle context
        activity = lifestyle_data.get('activity_level')
        if activity == 'Sedentary':
            query_parts.append("physical activity sedentary starting exercise")
        
        diet = lifestyle_data.get('dietary_pattern')
        if diet:
            query_parts.append(f"diet {diet} portion control plate method")
        
        # Add medication context if on insulin
        meds = patient_data.get('medications', [])
        if 'Insulin' in meds:
            query_parts.append("insulin monitoring hypoglycaemia sick day rules")
        
        # Add goals
        goal = lifestyle_data.get('primary_goal')
        if goal:
            query_parts.append(goal.lower())
        
        # Add standard UK terms
        query_parts.extend([
            "NICE guidelines",
            "NHS recommendations",
            "150 minutes exercise weekly",
            "Eatwell plate",
            "self-monitoring blood glucose",
            "annual review foot eye kidney"
        ])
        
        return " ".join(query_parts)
    
    def retrieve_sources(
        self,
        query: str,
        patient_context: Dict,
        top_k: int = 6
    ) -> tuple[List[Dict], Dict[str, Dict]]:
        """
        Retrieve relevant sources using hybrid search
        
        Returns:
            - List of retrieved chunks with content
            - Dictionary mapping S# to source metadata
        """
        
        # In production, this would use:
        # 1. Dense retrieval with embeddings
        # 2. BM25 sparse retrieval
        # 3. Cross-encoder reranking
        # 4. MMR diversity filtering
        
        # For POC, using simple keyword matching and scoring
        scored_chunks = []
        
        query_terms = query.lower().split()
        
        for chunk in self.knowledge_base:
            score = 0
            content_lower = chunk['content'].lower()
            
            # Score based on query term matches
            for term in query_terms:
                if term in content_lower:
                    score += 1
            
            # Boost recent sources
            if chunk['updated'] > '2022-01-01':
                score += 0.5
            
            # Boost NICE guidelines
            if chunk['source'] == 'NICE NG28':
                score += 1
            
            # Context-specific boosting
            hba1c = patient_context.get('labs_data', {}).get('hba1c')
            if hba1c and hba1c >= 8 and 'intensif' in content_lower:
                score += 2
            
            if score > 0:
                scored_chunks.append((score, chunk))
        
        # Sort by score and take top K
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [chunk for _, chunk in scored_chunks[:top_k]]
        
        # Create source mapping
        sources_map = {}
        for i, chunk in enumerate(top_chunks, 1):
            source_id = f"S{i}"
            sources_map[source_id] = {
                'title': chunk['title'],
                'url': chunk['url'],
                'updated': chunk['updated'],
                'source': chunk['source'],
                'section': chunk['section'],
                'snippet': chunk['content'][:200] + '...' if len(chunk['content']) > 200 else chunk['content']
            }
        
        return top_chunks, sources_map
    
    def format_sources_for_prompt(self, chunks: List[Dict]) -> str:
        """Format retrieved chunks for inclusion in prompt"""
        
        formatted = "## Retrieved Sources\n\n"
        
        for i, chunk in enumerate(chunks, 1):
            formatted += f"[S{i}] {chunk['title']} - {chunk['source']} ({chunk['updated']})\n"
            formatted += f"URL: {chunk['url']}\n"
            formatted += f"Content: {chunk['content']}\n\n"
        
        return formatted
    
    def validate_retrieval_quality(self, chunks: List[Dict]) -> bool:
        """Validate that retrieval has sufficient quality sources"""
        
        if len(chunks) < 3:
            return False
        
        # Check for diversity of sources
        sources = set(chunk['source'] for chunk in chunks)
        if len(sources) < 2:
            return False
        
        # Check for recent content
        recent = sum(1 for chunk in chunks if chunk['updated'] > '2021-01-01')
        if recent < len(chunks) / 2:
            return False
        
        return True
    
    def get_fallback_sources(self) -> tuple[List[Dict], Dict[str, Dict]]:
        """Get fallback sources if retrieval fails"""
        
        # Return core NICE and NHS guidelines
        fallback = [
            chunk for chunk in self.knowledge_base
            if chunk['source'] in ['NICE NG28', 'NHS']
        ][:4]
        
        sources_map = {}
        for i, chunk in enumerate(fallback, 1):
            source_id = f"S{i}"
            sources_map[source_id] = {
                'title': chunk['title'],
                'url': chunk['url'],
                'updated': chunk['updated'],
                'source': chunk['source'],
                'snippet': chunk['content'][:200]
            }
        
        return fallback, sources_map
