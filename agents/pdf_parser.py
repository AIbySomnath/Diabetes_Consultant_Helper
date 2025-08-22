"""
PDF parser for diabetes lab reports using PyMuPDF + GPT-4o-mini
"""
import os
import fitz  # PyMuPDF
import json
from typing import Dict, List, Optional
from pathlib import Path
from openai import OpenAI
from rules.schemas.report import PDFExtraction

class PDFParser:
    """Parse diabetes lab reports from PDF files"""
    
    def __init__(self, api_key: str = None):
        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4o-mini"
        
    def extract_text(self, pdf_file) -> tuple[str, Dict]:
        """Extract text from PDF using PyMuPDF"""
        try:
            # Handle both file path and file-like object
            if hasattr(pdf_file, 'read'):
                pdf_bytes = pdf_file.read()
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            else:
                doc = fitz.open(pdf_file)
            
            text = ""
            page_count = 0
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()
                text += f"\n--- Page {page_num + 1} ---\n{page_text}"
                page_count += 1
                
                # Check if this looks like a scanned document
                if len(page_text.strip()) < 50 and page_count == 1:
                    return "", {"warning": "Document appears to be scanned - OCR not supported"}
            
            doc.close()
            
            metadata = {
                "page_count": page_count,
                "text_length": len(text),
                "filename": getattr(pdf_file, 'name', 'uploaded_file')
            }
            
            return text, metadata
            
        except Exception as e:
            return "", {"error": f"PDF extraction failed: {str(e)}"}
    
    def extract_structured_data(self, pdf_text: str) -> PDFExtraction:
        """Extract structured lab data using GPT-4o-mini"""
        if not pdf_text.strip():
            return PDFExtraction(
                confidence=0.0,
                warnings=["No text extracted from PDF"]
            )
        
        extraction_prompt = self._get_extraction_prompt()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": extraction_prompt},
                    {"role": "user", "content": f"PDF Text:\n{pdf_text}"}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                parsed_data = json.loads(result_text)
                
                # Calculate confidence based on how many fields were extracted
                total_possible = 15  # rough count of possible lab values
                extracted_count = self._count_extracted_fields(parsed_data)
                confidence = min(1.0, extracted_count / total_possible)
                
                return PDFExtraction(
                    labs=parsed_data.get('labs', {}),
                    vitals=parsed_data.get('vitals', {}),
                    screenings=parsed_data.get('screenings', {}),
                    confidence=confidence,
                    warnings=parsed_data.get('warnings', []),
                    provenance={
                        "extraction_model": self.model,
                        "extracted_fields": extracted_count
                    }
                )
                
            except json.JSONDecodeError as e:
                return PDFExtraction(
                    confidence=0.0,
                    warnings=[f"Failed to parse extraction JSON: {str(e)}"]
                )
                
        except Exception as e:
            return PDFExtraction(
                confidence=0.0,
                warnings=[f"LLM extraction failed: {str(e)}"]
            )
    
    def _get_extraction_prompt(self) -> str:
        """Get the extraction prompt for GPT-4o-mini"""
        return """You are a UK diabetes lab-extraction assistant.
INPUT: raw PDF text (UK lab style).
OUTPUT: a valid JSON dict with keys:
{
 "labs": {
   "hba1c_pct": float|null, "fpg_mmol": float|null, "ppg2h_mmol": float|null,
   "egfr": float|null, "creatinine_umol": float|null, "acr_mgmmol": float|null,
   "lipids": {"tc": float|null, "ldl": float|null, "hdl": float|null, "tg": float|null}
 },
 "vitals": {"bp_sys": float|null, "bp_dia": float|null, "hr": float|null},
 "screenings": {"retina_date": "YYYY-MM-DD"|null, "foot_date": "YYYY-MM-DD"|null, "renal_date": "YYYY-MM-DD"|null},
 "warnings": ["any extraction warnings"]
}

Rules: 
- Convert all glucose to mmol/L, round to 1 dp
- HbA1c to % if reported in mmol/mol (convert using: % = (mmol/mol + 10.93) / 10.93)
- Extract only clearly identifiable values
- Use null for missing/unclear values
- Add warnings for any ambiguous extractions
- Return valid JSON only, no other text"""
    
    def _count_extracted_fields(self, data: Dict) -> int:
        """Count how many fields were successfully extracted"""
        count = 0
        
        labs = data.get('labs', {})
        count += sum(1 for v in labs.values() if v is not None and v != "")
        
        if labs.get('lipids'):
            count += sum(1 for v in labs['lipids'].values() if v is not None and v != "")
        
        vitals = data.get('vitals', {})
        count += sum(1 for v in vitals.values() if v is not None and v != "")
        
        screenings = data.get('screenings', {})
        count += sum(1 for v in screenings.values() if v is not None and v != "")
        
        return count
    
    def parse_pdf(self, pdf_file) -> PDFExtraction:
        """Main method to parse PDF and extract structured data"""
        # Extract text
        pdf_text, metadata = self.extract_text(pdf_file)
        
        if not pdf_text:
            warnings = [metadata.get('warning', metadata.get('error', 'Unknown extraction error'))]
            return PDFExtraction(confidence=0.0, warnings=warnings)
        
        # Extract structured data
        extraction = self.extract_structured_data(pdf_text)
        extraction.provenance.update(metadata)
        
        return extraction

if __name__ == "__main__":
    # Test with a sample PDF
    parser = PDFParser()
    
    # Create a test text that looks like a lab report
    test_text = """
    DIABETES LABORATORY REPORT
    
    Patient: Test Patient
    Date: 2024-01-15
    
    GLUCOSE MANAGEMENT:
    HbA1c: 67 mmol/mol (8.3%)
    Fasting Glucose: 8.5 mmol/L
    
    LIPID PROFILE:
    Total Cholesterol: 5.2 mmol/L
    LDL Cholesterol: 3.2 mmol/L
    HDL Cholesterol: 1.1 mmol/L
    
    RENAL FUNCTION:
    eGFR: 82 mL/min/1.73m²
    Creatinine: 95 μmol/L
    ACR: 2.5 mg/mmol
    
    VITALS:
    Blood Pressure: 127/83 mmHg
    Heart Rate: 72 bpm
    """
    
    result = parser.extract_structured_data(test_text)
    print(f"Extraction confidence: {result.confidence:.2f}")
    print(f"Labs: {result.labs}")
    print(f"Vitals: {result.vitals}")
    if result.warnings:
        print(f"Warnings: {result.warnings}")
