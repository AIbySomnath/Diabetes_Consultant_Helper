"""Wrapper around RAGPipeline to provide a simple interface for the sidebar UI."""
from typing import List, Dict, Any
from src.rag.retrieval import RAGPipeline

class RAGSystem:
    def __init__(self) -> None:
        self.pipeline = RAGPipeline()

    def retrieve(self, query: str, patient_context: Dict[str, Any]) -> Dict[str, Any]:
        q = self.pipeline.build_query(patient_context)
        q += f" Additional question: {query}"
        chunks, sources_map = self.pipeline.retrieve(q)
        return {"chunks": chunks, "sources_map": sources_map}

    def answer(self, question: str, patient_context: Dict[str, Any]) -> str:
        # For POC, synthesize a brief answer using retrieval snippets
        res = self.retrieve(question, patient_context)
        snippets = [c['snippet'] for c in res.get('chunks', [])][:3]
        base = " ".join(snippets) if snippets else "Based on UK guidelines, please consult your clinician for personalised advice."
        return base[:800]
