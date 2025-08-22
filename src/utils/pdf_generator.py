"""Wrapper around PDFExporter to generate a PDF from patient data and report content."""
from typing import Dict, Any, Union
from io import BytesIO
from src.report.exporter import PDFExporter

class PDFGenerator:
    def __init__(self) -> None:
        self.exporter = PDFExporter()

    def generate_pdf_report(self, patient_data: Dict[str, Any], report_content: Union[str, Dict[str, Any]]) -> BytesIO:
        # Prepare patient/labs minimal dicts for exporter
        demo = patient_data.get('demographics', {})
        labs = {}
        bp = patient_data.get('vitals', {}).get('blood_pressure')
        if isinstance(bp, str) and '/' in bp:
            try:
                s, d = bp.split('/')
                labs['bp_systolic'] = float(s)
                labs['bp_diastolic'] = float(d)
            except Exception:
                pass
        labs['hba1c'] = patient_data.get('medical_history', {}).get('hba1c')
        labs['weight'] = demo.get('weight')
        labs['height'] = demo.get('height')

        patient = {
            'name': patient_data.get('name') or patient_data.get('patient_name') or 'Patient',
            'dob': None,
            'sex': demo.get('gender'),
            'ethnicity': None,
        }

        # If report content is dict, try to reconstruct markdown, else assume markdown str
        if isinstance(report_content, dict):
            md = report_content.get('full_markdown') or "\n\n".join([
                f"## Health Summary\n{report_content.get('health_summary','')}\n",
                f"## Lifestyle Recommendations\n{report_content.get('lifestyle_recommendations','')}\n",
                f"## Diet Plan\n{report_content.get('diet_plan','')}\n",
                f"## Monitoring & Follow-up\n{report_content.get('monitoring_followup','')}\n",
            ])
        else:
            md = str(report_content)

        sources = {}
        buf = self.exporter.export_report(md, patient, labs, sources)
        return buf
