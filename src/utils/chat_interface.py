"""Simple chat interface using the RAGSystem wrapper."""
from typing import Dict, Any
from src.utils.rag_system import RAGSystem

class ChatInterface:
    def __init__(self, rag_system: RAGSystem) -> None:
        self.rag = rag_system

    def get_response(self, prompt: str, patient_context: Dict[str, Any]) -> str:
        # For POC, return retrieval-based answer
        return self.rag.answer(prompt, patient_context or {})
