"""
Report orchestrator for single-pass LLM report generation
"""
import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from openai import OpenAI

from rules.schemas.report import PatientIntake, ReportOut
from rag.retriever import RAGRetriever
from rules import load_rules
from llm.prompts import get_report_generation_prompt
from utils.formatters import normalize_patient_data

class ReportOrchestrator:
    """Orchestrate single-pass report generation with RAG"""
    
    def __init__(self, api_key: str = None):
        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4o-mini"
        self.rag_retriever = RAGRetriever()
        self.rules = load_rules()
        
    def merge_data_sources(self, form_data: Dict, pdf_data: Dict, conflicts: Dict) -> PatientIntake:
        """
        Merge form and PDF data, applying conflict resolutions
        
        Args:
            form_data: Data from UI forms
            pdf_data: Extracted PDF data
            conflicts: User-resolved conflicts {field: 'form'|'pdf'}
        """
        merged_data = form_data.copy()
        
        # Apply PDF data where no conflicts or PDF chosen
        for field, pdf_value in pdf_data.items():
            if field not in conflicts:
                # No conflict, use PDF if confidence is high
                if pdf_data.get('_confidence', {}).get(field, 0) > 0.7:
                    merged_data[field] = pdf_value
            elif conflicts[field] == 'pdf':
                merged_data[field] = pdf_value
            # If conflicts[field] == 'form', keep form data (already in merged_data)
        
        # Normalize and validate
        normalized_data = normalize_patient_data(merged_data, self.rules)
        
        return PatientIntake(**normalized_data)
    
    def generate_report(self, patient_data: PatientIntake, max_retries: int = 1) -> Tuple[Optional[ReportOut], List[str]]:
        """
        Generate complete report using single LLM call
        
        Returns:
            - ReportOut object if successful, None if failed
            - List of error messages
        """
        errors = []
        
        try:
            # Build retrieval query and get relevant snippets
            query = self.rag_retriever.build_retrieval_query(patient_data.dict())
            snippets = self.rag_retriever.retrieve(query, k=6)
            
            # Prepare context for LLM
            context = {
                "patient_intake": patient_data.dict(),
                "rules": self.rules,
                "retrieved_snippets": snippets
            }
            
            # Generate report with retry logic
            for attempt in range(max_retries + 1):
                try:
                    report_json = self._call_llm_for_report(context)
                    
                    # Validate and parse
                    report = ReportOut(**report_json)
                    
                    # Validate citations
                    if not self._validate_citations(report, snippets):
                        errors.append("Some citations are invalid")
                    
                    return report, errors
                    
                except Exception as e:
                    error_msg = f"Attempt {attempt + 1} failed: {str(e)}"
                    errors.append(error_msg)
                    
                    if attempt == max_retries:
                        return None, errors
                    
                    # Add error context for retry
                    context["previous_error"] = str(e)
            
        except Exception as e:
            errors.append(f"Report generation failed: {str(e)}")
            return None, errors
        
        return None, errors
    
    def _call_llm_for_report(self, context: Dict) -> Dict:
        """Call LLM with structured prompt for report generation"""
        
        prompt = get_report_generation_prompt()
        
        # Format context as structured input
        context_str = f"""
PATIENT DATA:
{json.dumps(context['patient_intake'], indent=2)}

CLINICAL RULES:
{json.dumps(context['rules'], indent=2)}

RETRIEVED EVIDENCE:
{json.dumps(context['retrieved_snippets'], indent=2)}
"""
        
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": context_str}
        ]
        
        # Add previous error context if retrying
        if context.get('previous_error'):
            messages.append({
                "role": "user", 
                "content": f"Previous attempt failed with error: {context['previous_error']}. Please fix and return valid JSON."
            })
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            max_tokens=4000
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Clean and parse JSON
        if result_text.startswith('```json'):
            result_text = result_text[7:]
        if result_text.endswith('```'):
            result_text = result_text[:-3]
        
        return json.loads(result_text)
    
    def _validate_citations(self, report: ReportOut, snippets: List[Dict]) -> bool:
        """Validate that all citation_ids exist in retrieved snippets"""
        snippet_ids = {snippet['id'] for snippet in snippets}
        
        # Check all citation_ids in the report
        all_citation_ids = set()
        
        # From lifestyle_plan
        for rec in report.lifestyle_plan:
            all_citation_ids.update(rec.citation_ids)
        
        # From medication_plan
        for rec in report.medication_plan:
            all_citation_ids.update(rec.citation_ids)
        
        # From interpretation
        for interp in report.interpretation:
            all_citation_ids.update(interp.get('citation_ids', []))
        
        # From citations list
        citation_ids_in_list = {cite['id'] for cite in report.citations}
        all_citation_ids.update(citation_ids_in_list)
        
        # Check if all citations are valid
        invalid_citations = all_citation_ids - snippet_ids
        
        if invalid_citations:
            print(f"Warning: Invalid citation IDs found: {invalid_citations}")
            return False
        
        return True
    
    def save_report(self, patient_uuid: str, report: ReportOut, patient_data: PatientIntake) -> str:
        """Save report to patient directory"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        patient_dir = Path(f"data/patients/{patient_uuid}/{date_str}")
        patient_dir.mkdir(parents=True, exist_ok=True)
        
        # Save report JSON
        report_file = patient_dir / "report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report.dict(), f, indent=2, ensure_ascii=False)
        
        # Save patient data
        patient_file = patient_dir / "patient_data.json"
        with open(patient_file, 'w', encoding='utf-8') as f:
            json.dump(patient_data.dict(), f, indent=2, ensure_ascii=False)
        
        return str(patient_dir)

if __name__ == "__main__":
    # Test orchestrator
    orchestrator = ReportOrchestrator()
    
    # Sample patient data
    sample_data = {
        "uuid": "test-uuid-123",
        "name": "Sai Mohan",
        "dob": "1980-05-15",
        "sex": "Male",
        "diabetes_type": "T1DM",
        "height_cm": 175.0,
        "weight_kg": 78.5,
        "bp_sys": 127.0,
        "bp_dia": 83.0,
        "labs": {
            "hba1c_pct": 8.3,
            "fpg_mmol": 8.5,
            "lipids": {
                "ldl": 3.2,
                "tc": 5.2
            }
        },
        "meds": [
            {"name": "Insulin aspart", "dose": "1:10 ratio", "schedule": "with meals"}
        ]
    }
    
    try:
        patient = PatientIntake(**sample_data)
        report, errors = orchestrator.generate_report(patient)
        
        if report:
            print("Report generated successfully!")
            print(f"Executive summary: {report.executive_summary}")
            print(f"Citations: {len(report.citations)}")
        else:
            print(f"Failed to generate report: {errors}")
            
    except Exception as e:
        print(f"Test failed: {e}")
