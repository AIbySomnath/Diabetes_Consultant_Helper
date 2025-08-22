"""Wrapper around PDFProcessor to extract structured data from PDFs for the sidebar UI."""
from typing import Any, Dict, Optional
from src.pdf.processor import PDFProcessor

class DataProcessor:
    def __init__(self) -> None:
        self._pdf = PDFProcessor()

    def extract_pdf_data(self, uploaded_file) -> Optional[Dict[str, Any]]:
        try:
            extracted = self._pdf.extract_lab_values(uploaded_file)
            # Return as simple dict keyed by test with value and provenance
            if not extracted:
                return None
            # Normalize into dict of lists by test
            out: Dict[str, Any] = { 'extracted_values': extracted }
            return out
        except Exception:
            return None
