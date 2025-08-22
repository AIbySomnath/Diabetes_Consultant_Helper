"""
PDF processing utilities for extracting structured data from lab reports.
"""
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import PyPDF2
import io
from ..models.patient import PatientBase, LabResult

class PDFProcessor:
    """Processes PDF lab reports to extract structured data."""
    
    def __init__(self):
        # Common patterns for extracting lab values
        self.patterns = {
            'hba1c': [
                r'HbA1c.*?([\d\.]+)\s*%',
                r'HbA1c.*?([\d\.]+)\s*%\(',
                r'HbA1c.*?(\d+)\s*mmol/mol',
            ],
            'glucose': [
                r'Glucose.*?([\d\.]+)\s*mmol/L',
                r'Glucose.*?([\d\.]+)\s*mg/dL',
                r'Glucose.*?([\d\.]+)\s*\(',
            ],
            'creatinine': [
                r'Creatinine.*?([\d\.]+)\s*umol/L',
                r'Creatinine.*?([\d\.]+)\s*mg/dL',
            ],
            'egfr': [
                r'eGFR.*?(\d+)\s*ml/min',
                r'eGFR.*?(\d+)\s*mL/min',
                r'eGFR.*?(\d+)\s*',
            ],
            'acr': [
                r'Albumin:Creatinine Ratio.*?([\d\.]+)\s*mg/mmol',
                r'ACR.*?([\d\.]+)\s*mg/mmol',
            ],
            'ldl': [
                r'LDL.*?([\d\.]+)\s*mmol/L',
                r'LDL.*?([\d\.]+)\s*mg/dL',
            ],
            'hdl': [
                r'HDL.*?([\d\.]+)\s*mmol/L',
                r'HDL.*?([\d\.]+)\s*mg/dL',
            ],
            'total_cholesterol': [
                r'Total Cholesterol.*?([\d\.]+)\s*mmol/L',
                r'Chol.*?([\d\.]+)\s*mmol/L',
            ],
            'triglycerides': [
                r'Triglycerides.*?([\d\.]+)\s*mmol/L',
                r'TG.*?([\d\.]+)\s*mmol/L',
            ],
            'tsh': [
                r'TSH.*?([\d\.]+)\s*mIU/L',
                r'Thyroid Stimulating Hormone.*?([\d\.]+)\s*mIU/L',
            ],
            't4': [
                r'Free T4.*?([\d\.]+)\s*pmol/L',
                r'Free Thyroxine.*?([\d\.]+)\s*pmol/L',
            ],
            'b12': [
                r'Vitamin B12.*?(\d+)\s*ng/L',
                r'B12.*?(\d+)\s*ng/L',
            ],
            'folate': [
                r'Folate.*?([\d\.]+)\s*ug/L',
                r'Folic Acid.*?([\d\.]+)\s*ug/L',
            ],
            'ferritin': [
                r'Ferritin.*?(\d+)\s*ug/L',
                r'Ferritin.*?(\d+)\s*ng/mL',
            ],
            'vitamin_d': [
                r'Vitamin D.*?(\d+)\s*nmol/L',
                r'25-OH Vitamin D.*?(\d+)\s*nmol/L',
            ],
            'alt': [
                r'ALT.*?(\d+)\s*U/L',
                r'Alanine Aminotransferase.*?(\d+)\s*U/L',
            ],
            'ast': [
                r'AST.*?(\d+)\s*U/L',
                r'Aspartate Aminotransferase.*?(\d+)\s*U/L',
            ],
            'alp': [
                r'Alkaline Phosphatase.*?(\d+)\s*U/L',
                r'ALP.*?(\d+)\s*U/L',
            ],
            'bilirubin': [
                r'Bilirubin.*?([\d\.]+)\s*umol/L',
                r'Bilirubin.*?([\d\.]+)\s*mg/dL',
            ],
            'albumin': [
                r'Albumin.*?([\d\.]+)\s*g/L',
                r'Albumin.*?([\d\.]+)\s*g/dL',
            ],
            'sodium': [
                r'Sodium.*?(\d+)\s*mmol/L',
                r'Na\+.*?(\d+)\s*mmol/L',
            ],
            'potassium': [
                r'Potassium.*?([\d\.]+)\s*mmol/L',
                r'K\+.*?([\d\.]+)\s*mmol/L',
            ],
            'chloride': [
                r'Chloride.*?(\d+)\s*mmol/L',
                r'Cl-.*?(\d+)\s*mmol/L',
            ],
            'bicarbonate': [
                r'Bicarbonate.*?(\d+)\s*mmol/L',
                r'HCO3.*?(\d+)\s*mmol/L',
            ],
            'urea': [
                r'Urea.*?([\d\.]+)\s*mmol/L',
                r'BUN.*?([\d\.]+)\s*mg/dL',
            ],
            'haemoglobin': [
                r'Haemoglobin.*?([\d\.]+)\s*g/L',
                r'Hb.*?([\d\.]+)\s*g/dL',
            ],
            'wcc': [
                r'White Cell Count.*?([\d\.]+)\s*10\^9/L',
                r'WCC.*?([\d\.]+)\s*10\^9/L',
            ],
            'platelets': [
                r'Platelet Count.*?(\d+)\s*10\^9/L',
                r'Platelets.*?(\d+)\s*10\^9/L',
            ],
        }
        
        # Reference ranges for validation
        self.reference_ranges = {
            'hba1c': (4.0, 15.0, '%'),
            'glucose_fasting': (3.5, 5.5, 'mmol/L'),
            'glucose_random': (0.0, 11.1, 'mmol/L'),
            'creatinine': (50, 120, 'umol/L'),  # Varies by age/sex
            'egfr': (60, 120, 'mL/min/1.73m²'),
            'acr': (0, 3, 'mg/mmol'),
            'ldl': (0, 3.0, 'mmol/L'),  # Target depends on risk
            'hdl': (1.0, None, 'mmol/L'),  # Higher is better
            'total_cholesterol': (0, 5.0, 'mmol/L'),
            'triglycerides': (0, 1.7, 'mmol/L'),
            'tsh': (0.4, 4.0, 'mIU/L'),
            't4': (12, 22, 'pmol/L'),
            'b12': (200, 1000, 'ng/L'),
            'folate': (3.0, 20.0, 'ug/L'),
            'ferritin': (30, 300, 'ug/L'),  # Male
            'ferritin_female': (15, 150, 'ug/L'),
            'vitamin_d': (50, 150, 'nmol/L'),
            'alt': (10, 40, 'U/L'),  # Male
            'alt_female': (7, 35, 'U/L'),
            'ast': (15, 40, 'U/L'),
            'alp': (30, 130, 'U/L'),  # Varies by age
            'bilirubin': (3, 21, 'umol/L'),
            'albumin': (35, 50, 'g/L'),
            'sodium': (135, 145, 'mmol/L'),
            'potassium': (3.5, 5.0, 'mmol/L'),
            'chloride': (95, 105, 'mmol/L'),
            'bicarbonate': (22, 30, 'mmol/L'),
            'urea': (2.5, 7.8, 'mmol/L'),
            'haemoglobin': (130, 180, 'g/L'),  # Male
            'haemoglobin_female': (115, 165, 'g/L'),
            'wcc': (4.0, 11.0, '10^9/L'),
            'platelets': (150, 400, '10^9/L'),
        }
    
    def extract_text_from_pdf(self, pdf_file) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_file: File-like object or path to PDF file
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        metadata = {
            'source': 'uploaded_file',
            'filename': getattr(pdf_file, 'name', 'unknown.pdf'),
            'extraction_date': datetime.now().isoformat(),
            'pages': 0,
            'success': False,
            'error': None
        }
        
        try:
            # Handle file path or file-like object
            if hasattr(pdf_file, 'read'):
                # File-like object (e.g., from Streamlit file_uploader)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
            else:
                # Assume it's a file path
                with open(pdf_file, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
            
            # Extract text from all pages
            text_parts = []
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text_parts.append(page.extract_text() or '')
            
            metadata.update({
                'pages': len(pdf_reader.pages),
                'success': True
            })
            
            return '\n\n'.join(text_parts), metadata
            
        except Exception as e:
            metadata.update({
                'success': False,
                'error': str(e)
            })
            return '', metadata
    
    def extract_labs(self, text: str) -> Dict[str, Any]:
        """
        Extract lab values from text using regex patterns.
        
        Args:
            text: Text to search for lab values
            
        Returns:
            Dictionary of extracted lab values with metadata
        """
        results = {}
        
        for test_name, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        value = float(match.group(1))
                        # Convert units if needed
                        if 'mg/dL' in pattern and test_name == 'glucose':
                            value = value / 18  # Convert mg/dL to mmol/L for glucose
                        elif 'mg/dL' in pattern and test_name == 'creatinine':
                            value = value * 88.4  # Convert mg/dL to umol/L for creatinine
                        
                        # Get reference range
                        ref_range = self.reference_ranges.get(test_name, (None, None, ''))
                        
                        results[test_name] = {
                            'value': value,
                            'unit': ref_range[2] if len(ref_range) > 2 else '',
                            'reference_range': f"{ref_range[0]}-{ref_range[1]}" if ref_range[0] is not None and ref_range[1] is not None else '',
                            'is_abnormal': (
                                (ref_range[0] is not None and value < ref_range[0]) or 
                                (ref_range[1] is not None and value > ref_range[1])
                            ) if ref_range[0] is not None or ref_range[1] is not None else None,
                            'source': 'extracted_from_pdf',
                            'extraction_date': datetime.now().isoformat(),
                        }
                        break  # Stop after first match
                    except (ValueError, IndexError):
                        continue
        
        return results
    
    def process_pdf_lab_report(self, pdf_file) -> Dict[str, Any]:
        """
        Process a PDF lab report and extract structured data.
        
        Args:
            pdf_file: File-like object or path to PDF file
            
        Returns:
            Dictionary with extracted data and metadata
        """
        # Extract text from PDF
        text, metadata = self.extract_text_from_pdf(pdf_file)
        
        if not metadata['success']:
            return {
                'success': False,
                'error': metadata.get('error', 'Failed to extract text from PDF'),
                'metadata': metadata
            }
        
        # Extract lab values
        lab_results = self.extract_labs(text)
        
        # Extract report date if available
        report_date = None
        date_patterns = [
            r'Report Date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'Date Collected[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # Fallback to any date
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    date_str = match.group(1)
                    # Try different date formats
                    for fmt in ('%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y'):
                        try:
                            report_date = datetime.strptime(date_str, fmt).date().isoformat()
                            break
                        except ValueError:
                            continue
                    if report_date:
                        break
                except (IndexError, AttributeError):
                    continue
        
        # Prepare results
        results = {
            'success': True,
            'metadata': {
                **metadata,
                'report_date': report_date,
                'extraction_date': datetime.now().isoformat(),
            },
            'lab_results': lab_results,
            'text_snippet': text[:1000] + ('...' if len(text) > 1000 else ''),  # Include first 1000 chars for reference
        }
        
        return results
    
    def update_patient_from_labs(self, patient: PatientBase, lab_data: Dict[str, Any]) -> Tuple[PatientBase, Dict[str, Any]]:
        """
        Update patient data with lab results, handling conflicts.
        
        Args:
            patient: The patient data to update
            lab_data: Extracted lab data from process_pdf_lab_report
            
        Returns:
            Tuple of (updated_patient, conflicts)
        """
        if not lab_data.get('success') or not lab_data.get('lab_results'):
            return patient, {}
        
        conflicts = {}
        updated_data = patient.dict()
        
        # Map lab result keys to patient model fields
        field_mapping = {
            'hba1c': 'hba1c_percent',
            'egfr': 'egfr',
            'acr': 'acr',
            'ldl': 'ldl_mmol',
            'hdl': 'hdl_mmol',
            'total_cholesterol': 'total_cholesterol',
            'triglycerides': 'triglycerides',
        }
        
        # Check for conflicts and update patient data
        for lab_key, patient_field in field_mapping.items():
            if lab_key in lab_data['lab_results']:
                lab_value = lab_data['lab_results'][lab_key]['value']
                current_value = getattr(patient, patient_field, None)
                
                # If there's a conflict (both values exist and differ by more than 5%)
                if current_value is not None and abs(lab_value - current_value) > (0.05 * current_value):
                    conflicts[patient_field] = {
                        'current_value': current_value,
                        'lab_value': lab_value,
                        'unit': lab_data['lab_results'][lab_key].get('unit', ''),
                        'is_abnormal': lab_data['lab_results'][lab_key].get('is_abnormal', False),
                    }
                
                # Update the patient data with the lab value
                updated_data[patient_field] = lab_value
        
        # Update the patient object if there are no conflicts or if we're forcing an update
        if conflicts:
            # Return the original patient and conflicts for resolution
            return patient, conflicts
        else:
            # No conflicts, update the patient
            updated_patient = patient.copy(update=updated_data)
            return updated_patient, {}

# Example usage:
# processor = PDFProcessor()
# with open('lab_report.pdf', 'rb') as f:
#     lab_data = processor.process_pdf_lab_report(f)
#     patient, conflicts = processor.update_patient_from_labs(patient, lab_data)
