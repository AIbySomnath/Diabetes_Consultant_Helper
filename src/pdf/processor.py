"""
PDF Processing Module for Diabetes Report Generator
Handles digital PDF text extraction and lab value parsing
"""

import re
import io
from typing import Dict, Any, Optional, List
from datetime import datetime, date
import PyPDF2
import pdfplumber
import streamlit as st

class PDFProcessor:
    """Process digital PDFs to extract lab values"""
    
    def __init__(self):
        """Initialize PDF processor with extraction patterns"""
        
        # UK lab value patterns
        self.patterns = {
            'hba1c': [
                r'HbA1c[:\s]+(\d+\.?\d*)\s*%',
                r'A1C[:\s]+(\d+\.?\d*)\s*%',
                r'Glycated\s+h[ae]moglobin[:\s]+(\d+\.?\d*)\s*%'
            ],
            'fpg': [
                r'FPG[:\s]+(\d+\.?\d*)\s*mmol/L',
                r'Fasting\s+plasma\s+glucose[:\s]+(\d+\.?\d*)\s*mmol/L',
                r'Fasting\s+glucose[:\s]+(\d+\.?\d*)\s*mmol/L'
            ],
            'ppg_2h': [
                r'2[\s-]?h(?:our)?\s+PPG[:\s]+(\d+\.?\d*)\s*mmol/L',
                r'Post[\s-]?prandial\s+glucose[:\s]+(\d+\.?\d*)\s*mmol/L',
                r'2[\s-]?hour\s+post[\s-]?meal[:\s]+(\d+\.?\d*)\s*mmol/L'
            ],
            'bp': [
                r'BP[:\s]+(\d+)/(\d+)',
                r'Blood\s+pressure[:\s]+(\d+)/(\d+)',
                r'Systolic[:\s]+(\d+).*Diastolic[:\s]+(\d+)'
            ],
            'cholesterol': [
                r'Total\s+cholesterol[:\s]+(\d+\.?\d*)\s*mmol/L',
                r'Cholesterol[:\s]+(\d+\.?\d*)\s*mmol/L'
            ],
            'ldl': [
                r'LDL[\s-]?cholesterol[:\s]+(\d+\.?\d*)\s*mmol/L',
                r'LDL[:\s]+(\d+\.?\d*)\s*mmol/L'
            ],
            'hdl': [
                r'HDL[\s-]?cholesterol[:\s]+(\d+\.?\d*)\s*mmol/L',
                r'HDL[:\s]+(\d+\.?\d*)\s*mmol/L'
            ],
            'triglycerides': [
                r'Triglycerides[:\s]+(\d+\.?\d*)\s*mmol/L',
                r'Trigs[:\s]+(\d+\.?\d*)\s*mmol/L'
            ],
            'egfr': [
                r'eGFR[:\s]+(\d+)',
                r'Estimated\s+GFR[:\s]+(\d+)',
                r'GFR[:\s]+(\d+)\s*mL/min'
            ],
            'uacr': [
                r'UACR[:\s]+(\d+\.?\d*)\s*mg/mmol',
                r'Albumin[\s/]creatinine\s+ratio[:\s]+(\d+\.?\d*)'
            ]
        }
        
        # Date patterns
        self.date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',
            r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{2,4})',
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})'
        ]
    
    def extract_lab_values(self, pdf_file) -> Dict[str, Any]:
        """
        Extract lab values from uploaded PDF file
        
        Args:
            pdf_file: Streamlit uploaded file object
            
        Returns:
            Dictionary of extracted values with provenance
        """
        
        try:
            # Check if PDF has text layer
            text, page_texts = self._extract_text(pdf_file)
            
            if not text or len(text.strip()) < 50:
                # No text layer detected
                return None
            
            # Extract values
            extracted = {}
            
            # Extract HbA1c
            hba1c_data = self._extract_value('hba1c', text, page_texts)
            if hba1c_data:
                extracted['HbA1c'] = hba1c_data
            
            # Extract FPG
            fpg_data = self._extract_value('fpg', text, page_texts)
            if fpg_data:
                extracted['FPG'] = fpg_data
            
            # Extract 2h-PPG
            ppg_data = self._extract_value('ppg_2h', text, page_texts)
            if ppg_data:
                extracted['2h-PPG'] = ppg_data
            
            # Extract Blood Pressure
            bp_data = self._extract_bp(text, page_texts)
            if bp_data:
                extracted.update(bp_data)
            
            # Extract Lipids
            chol_data = self._extract_value('cholesterol', text, page_texts)
            if chol_data:
                extracted['Total Cholesterol'] = chol_data
            
            ldl_data = self._extract_value('ldl', text, page_texts)
            if ldl_data:
                extracted['LDL'] = ldl_data
            
            hdl_data = self._extract_value('hdl', text, page_texts)
            if hdl_data:
                extracted['HDL'] = hdl_data
            
            trig_data = self._extract_value('triglycerides', text, page_texts)
            if trig_data:
                extracted['Triglycerides'] = trig_data
            
            # Extract Renal
            egfr_data = self._extract_value('egfr', text, page_texts)
            if egfr_data:
                extracted['eGFR'] = egfr_data
            
            uacr_data = self._extract_value('uacr', text, page_texts)
            if uacr_data:
                extracted['UACR'] = uacr_data
            
            # Extract dates
            self._add_dates_to_extracted(extracted, text)
            
            return extracted
            
        except Exception as e:
            st.error(f"PDF processing error: {str(e)}")
            return None
    
    def _extract_text(self, pdf_file) -> tuple[str, Dict[int, str]]:
        """Extract text from PDF using multiple methods"""
        
        full_text = ""
        page_texts = {}
        
        try:
            # Reset file pointer
            pdf_file.seek(0)
            
            # Try pdfplumber first (better for tables)
            with pdfplumber.open(pdf_file) as pdf:
                for i, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text() or ""
                    page_texts[i] = page_text
                    full_text += f"\n--- Page {i} ---\n{page_text}"
            
            # If pdfplumber fails, try PyPDF2
            if not full_text.strip():
                pdf_file.seek(0)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                for i, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    page_texts[i] = page_text
                    full_text += f"\n--- Page {i} ---\n{page_text}"
        
        except Exception as e:
            st.warning(f"Text extraction warning: {str(e)}")
        
        return full_text, page_texts
    
    def _extract_value(
        self, 
        value_type: str, 
        full_text: str, 
        page_texts: Dict[int, str]
    ) -> Optional[Dict[str, Any]]:
        """Extract a specific value type from text"""
        
        patterns = self.patterns.get(value_type, [])
        
        for pattern in patterns:
            matches = re.finditer(pattern, full_text, re.IGNORECASE)
            
            for match in matches:
                value = float(match.group(1))
                
                # Find page number
                page_num = self._find_page_number(match.start(), full_text)
                
                # Get nearby text
                start = max(0, match.start() - 50)
                end = min(len(full_text), match.end() + 50)
                nearby_text = full_text[start:end].strip()
                
                # Determine unit
                unit = self._get_unit_for_type(value_type)
                
                return {
                    'value': value,
                    'unit': unit,
                    'page': page_num,
                    'nearby_text': nearby_text,
                    'confidence': 'high'
                }
        
        return None
    
    def _extract_bp(self, full_text: str, page_texts: Dict[int, str]) -> Optional[Dict]:
        """Extract blood pressure values"""
        
        patterns = self.patterns.get('bp', [])
        
        for pattern in patterns:
            matches = re.finditer(pattern, full_text, re.IGNORECASE)
            
            for match in matches:
                systolic = int(match.group(1))
                diastolic = int(match.group(2))
                
                # Validate BP values
                if 70 <= systolic <= 250 and 40 <= diastolic <= 150:
                    page_num = self._find_page_number(match.start(), full_text)
                    
                    start = max(0, match.start() - 50)
                    end = min(len(full_text), match.end() + 50)
                    nearby_text = full_text[start:end].strip()
                    
                    return {
                        'Systolic BP': {
                            'value': systolic,
                            'unit': 'mmHg',
                            'page': page_num,
                            'nearby_text': nearby_text
                        },
                        'Diastolic BP': {
                            'value': diastolic,
                            'unit': 'mmHg',
                            'page': page_num,
                            'nearby_text': nearby_text
                        }
                    }
        
        return None
    
    def _find_page_number(self, position: int, full_text: str) -> int:
        """Find which page a text position belongs to"""
        
        pages = full_text.split('--- Page ')
        current_pos = 0
        
        for i, page in enumerate(pages[1:], 1):
            if current_pos <= position < current_pos + len(page):
                return i
            current_pos += len(page) + len('--- Page ')
        
        return 1
    
    def _get_unit_for_type(self, value_type: str) -> str:
        """Get the appropriate unit for a value type"""
        
        units = {
            'hba1c': '%',
            'fpg': 'mmol/L',
            'ppg_2h': 'mmol/L',
            'cholesterol': 'mmol/L',
            'ldl': 'mmol/L',
            'hdl': 'mmol/L',
            'triglycerides': 'mmol/L',
            'egfr': 'mL/min/1.73m²',
            'uacr': 'mg/mmol'
        }
        
        return units.get(value_type, '')
    
    def _add_dates_to_extracted(self, extracted: Dict, text: str) -> None:
        """Add date information to extracted values"""
        
        # Find all dates in text
        dates_found = []
        
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Parse date (simplified)
                    date_str = match.group(0)
                    dates_found.append(date_str)
                except:
                    continue
        
        # Add most recent date to all extracted values
        if dates_found and extracted:
            most_recent = dates_found[-1]  # Assume last date is most recent
            
            for key in extracted:
                if isinstance(extracted[key], dict):
                    extracted[key]['date'] = most_recent
    
    def validate_text_layer(self, pdf_file) -> bool:
        """Check if PDF has extractable text layer"""
        
        try:
            text, _ = self._extract_text(pdf_file)
            return len(text.strip()) > 50
        except:
            return False
