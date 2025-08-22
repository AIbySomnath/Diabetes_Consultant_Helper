"""
Session State Manager for Diabetes Report Generator
Handles data persistence across Streamlit reruns
"""

import streamlit as st
import json
from datetime import datetime, date
from typing import Dict, Any, List

class SessionManager:
    """Manages session state and data persistence"""
    
    def __init__(self):
        """Initialize session state variables if not present"""
        
        # Initialize default session state
        if 'patient_data' not in st.session_state:
            st.session_state.patient_data = {}
        
        if 'labs_data' not in st.session_state:
            st.session_state.labs_data = {}
        
        if 'lifestyle_data' not in st.session_state:
            st.session_state.lifestyle_data = {}
        
        if 'pdf_extracted_data' not in st.session_state:
            st.session_state.pdf_extracted_data = {}
        
        if 'generated_report' not in st.session_state:
            st.session_state.generated_report = None
        
        if 'sources' not in st.session_state:
            st.session_state.sources = {}
        
        if 'autosave_enabled' not in st.session_state:
            st.session_state.autosave_enabled = True
        
        if 'draft_saved' not in st.session_state:
            st.session_state.draft_saved = False
        
        if 'last_saved' not in st.session_state:
            st.session_state.last_saved = None
    
    def save_patient_data(self, data: Dict[str, Any]) -> None:
        """Save patient demographic data to session state"""
        st.session_state.patient_data = data
        self._update_last_saved()
    
    def save_labs_data(self, data: Dict[str, Any]) -> None:
        """Save laboratory data to session state"""
        st.session_state.labs_data = data
        self._update_last_saved()
    
    def save_lifestyle_data(self, data: Dict[str, Any]) -> None:
        """Save lifestyle data to session state"""
        st.session_state.lifestyle_data = data
        self._update_last_saved()
    
    def update_from_pdf(self, extracted_data: Dict[str, Any]) -> None:
        """Update session state with PDF extracted data"""
        
        # Map extracted fields to labs_data
        field_mapping = {
            'HbA1c': 'hba1c',
            'FPG': 'fpg',
            '2h-PPG': 'ppg_2h',
            'Systolic BP': 'bp_systolic',
            'Diastolic BP': 'bp_diastolic',
            'Total Cholesterol': 'total_cholesterol',
            'LDL': 'ldl_cholesterol',
            'HDL': 'hdl_cholesterol',
            'Triglycerides': 'triglycerides',
            'eGFR': 'egfr',
            'UACR': 'uacr'
        }
        
        # Update labs data with extracted values
        for pdf_field, session_field in field_mapping.items():
            if pdf_field in extracted_data:
                value = extracted_data[pdf_field].get('value')
                if value:
                    st.session_state.labs_data[session_field] = value
        
        # Store provenance information
        st.session_state.pdf_extracted_data = extracted_data
        self._update_last_saved()
    
    def get_all_data(self) -> Dict[str, Any]:
        """Get all session data as a dictionary"""
        return {
            'patient_data': st.session_state.patient_data,
            'labs_data': st.session_state.labs_data,
            'lifestyle_data': st.session_state.lifestyle_data,
            'pdf_extracted_data': st.session_state.pdf_extracted_data,
            'generated_report': st.session_state.generated_report,
            'sources': st.session_state.sources,
            'last_saved': st.session_state.last_saved
        }
    
    def clear_all_data(self) -> None:
        """Clear all session data"""
        st.session_state.patient_data = {}
        st.session_state.labs_data = {}
        st.session_state.lifestyle_data = {}
        st.session_state.pdf_extracted_data = {}
        st.session_state.generated_report = None
        st.session_state.sources = {}
        st.session_state.draft_saved = False
        st.session_state.last_saved = None
    
    def autosave(self) -> None:
        """Autosave current session data"""
        if st.session_state.autosave_enabled:
            try:
                # Save to browser local storage (simulation)
                # In production, this would save to a database
                data = self.get_all_data()
                
                # Convert dates to strings for JSON serialization
                data_json = json.dumps(data, default=str)
                
                # Mark as saved
                st.session_state.draft_saved = True
                self._update_last_saved()
                
            except Exception as e:
                st.error(f"Autosave failed: {str(e)}")
    
    def restore_draft(self) -> bool:
        """Restore draft data from storage"""
        try:
            # In production, this would load from database
            # For POC, we'll just return the current session state
            return st.session_state.draft_saved
        except Exception:
            return False
    
    def undo_last_change(self) -> None:
        """Undo the last change (simplified implementation)"""
        # In production, this would maintain a history stack
        st.info("Undo functionality will be available in the full version")
    
    def _update_last_saved(self) -> None:
        """Update the last saved timestamp"""
        st.session_state.last_saved = datetime.now().strftime("%H:%M:%S")
    
    def validate_required_fields(self) -> tuple[bool, List[str]]:
        """Validate that required fields are present"""
        
        missing_fields = []
        
        # Check patient data
        required_patient = ['name', 'dob', 'sex']
        for field in required_patient:
            if not st.session_state.patient_data.get(field):
                missing_fields.append(f"Patient: {field}")
        
        # Check labs data
        required_labs = ['hba1c', 'fpg']
        for field in required_labs:
            if not st.session_state.labs_data.get(field):
                missing_fields.append(f"Labs: {field}")
        
        # Check lifestyle data
        required_lifestyle = ['activity_level']
        for field in required_lifestyle:
            if not st.session_state.lifestyle_data.get(field):
                missing_fields.append(f"Lifestyle: {field}")
        
        is_valid = len(missing_fields) == 0
        return is_valid, missing_fields
    
    def export_session_data(self) -> str:
        """Export session data as JSON string"""
        data = self.get_all_data()
        return json.dumps(data, indent=2, default=str)
    
    def import_session_data(self, json_str: str) -> bool:
        """Import session data from JSON string"""
        try:
            data = json.loads(json_str)
            
            # Restore each component
            st.session_state.patient_data = data.get('patient_data', {})
            st.session_state.labs_data = data.get('labs_data', {})
            st.session_state.lifestyle_data = data.get('lifestyle_data', {})
            st.session_state.pdf_extracted_data = data.get('pdf_extracted_data', {})
            st.session_state.generated_report = data.get('generated_report')
            st.session_state.sources = data.get('sources', {})
            
            self._update_last_saved()
            return True
            
        except Exception as e:
            st.error(f"Failed to import data: {str(e)}")
            return False
