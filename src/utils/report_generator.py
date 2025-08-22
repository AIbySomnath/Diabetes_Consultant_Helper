"""Wrapper around ReportGenerator that returns structured dict for the sidebar UI."""
from typing import Dict, Any, Tuple
from src.report.generator import ReportGenerator as CoreReportGenerator

class ReportGenerator:
    def __init__(self, rag_system=None) -> None:
        # Core generator constructs its own RAGPipeline; no args expected
        self.core = CoreReportGenerator()

    def _extract_patient_data(self, patient_data: Dict[str, Any]) -> Tuple[Dict, Dict, Dict]:
        """Extract and format patient, labs, and lifestyle data from input."""
        # Handle different input formats
        demo = patient_data.get('demographics', {})
        
        # Extract patient info
        patient = {
            'name': patient_data.get('name') or patient_data.get('patient_name') or 'Patient',
            'age': patient_data.get('age') or demo.get('age'),
            'sex': demo.get('gender') or patient_data.get('sex'),
            'ethnicity': demo.get('ethnicity'),
            'dob': patient_data.get('dob') or demo.get('date_of_birth'),
            'nhs_number': patient_data.get('nhs_number') or demo.get('nhs_number'),
            'diabetes_type': patient_data.get('diabetes_type') or patient_data.get('medical_history', {}).get('diabetes_type'),
            'diagnosis_date': patient_data.get('diagnosis_date') or patient_data.get('medical_history', {}).get('diagnosis_year'),
            'hypos_90d': patient_data.get('hypos_90d', 0),
            'smoking_status': patient_data.get('smoking_status') or (demo.get('smoking') and 'Yes' if demo['smoking'] else 'No'),
            'activity_level': patient_data.get('activity_level') or demo.get('activity_level')
        }
        
        # Extract labs data
        labs = {
            'hba1c': patient_data.get('hba1c') or patient_data.get('medical_history', {}).get('hba1c'),
            'bp_systolic': None,
            'diastolic': None,  # Note: using 'diastolic' to match template expectations
            'weight': demo.get('weight'),
            'height': demo.get('height'),
            'ldl': patient_data.get('ldl') or patient_data.get('labs', {}).get('ldl'),
            'egfr': patient_data.get('egfr') or patient_data.get('labs', {}).get('egfr'),
            'acr': patient_data.get('acr') or patient_data.get('labs', {}).get('acr'),
            'fpg': patient_data.get('fpg') or patient_data.get('labs', {}).get('fpg'),
            'ppg': patient_data.get('ppg') or patient_data.get('labs', {}).get('ppg')
        }
        
        # Handle blood pressure from different formats
        bp = patient_data.get('blood_pressure') or patient_data.get('vitals', {}).get('blood_pressure')
        if isinstance(bp, str) and '/' in bp:
            try:
                s, d = bp.split('/')
                labs['bp_systolic'] = float(s.strip())
                labs['diastolic'] = float(d.strip())
            except (ValueError, AttributeError):
                pass
        
        # Extract lifestyle data
        lifestyle = {
            'activity_level': patient_data.get('activity_level') or demo.get('activity_level'),
            'dietary_pattern': patient_data.get('dietary_pattern') or demo.get('dietary_pattern'),
            'smoking_status': patient.get('smoking_status')
        }
        
        return patient, labs, lifestyle

    def generate_comprehensive_report(self, patient_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate a comprehensive diabetes management report."""
        try:
            # Extract and format data from input
            patient, labs, lifestyle = self._extract_patient_data(patient_data)
            
            # Generate the full markdown report
            report_md, _sources = self.core.generate_report(patient, labs, lifestyle)
            
            # For the UI, we'll return the full markdown and let the UI handle display
            # The enhanced generator creates a complete, well-formatted markdown document
            return {
                'full_markdown': report_md,
                'health_summary': report_md,  # Full report for now
                'lifestyle_recommendations': report_md,  # Full report for now
                'diet_plan': report_md,  # Full report for now
                'monitoring_followup': report_md  # Full report for now
            }
            
        except Exception as e:
            error_msg = f"Error generating report: {str(e)}"
            return {
                'error': error_msg,
                'full_markdown': f"# Error\n\n{error_msg}",
                'health_summary': error_msg,
                'lifestyle_recommendations': error_msg,
                'diet_plan': error_msg,
                'monitoring_followup': error_msg
            }
