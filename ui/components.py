"""
UI components for diabetes report system - conflict resolver, tiles, download buttons
"""
import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

def create_conflict_resolver(form_data: Dict, pdf_data: Dict, confidence_scores: Dict) -> Dict:
    """
    Create conflict resolution interface for form vs PDF data
    
    Args:
        form_data: Data from form inputs
        pdf_data: Data extracted from PDF
        confidence_scores: PDF extraction confidence per field
    
    Returns:
        Dict of resolved conflicts {field: 'form'|'pdf'}
    """
    st.subheader("🔄 Resolve Data Conflicts")
    st.info("Some values differ between your form entries and the uploaded PDF. Please choose which to use.")
    
    conflicts = {}
    conflict_data = []
    
    # Find conflicts between form and PDF data
    for field, pdf_value in pdf_data.items():
        if field.startswith('_'):  # Skip metadata fields
            continue
            
        form_value = form_data.get(field)
        
        # Check if values differ significantly
        if form_value is not None and pdf_value is not None:
            if _values_differ(form_value, pdf_value):
                conflict_data.append({
                    'Field': _format_field_name(field),
                    'Form Value': _format_value(form_value),
                    'PDF Value': _format_value(pdf_value),
                    'PDF Confidence': f"{confidence_scores.get(field, 0):.1%}",
                    'field_key': field
                })
    
    if not conflict_data:
        st.success("✅ No conflicts found between form and PDF data")
        return {}
    
    # Display conflicts table
    df = pd.DataFrame(conflict_data)
    st.dataframe(df[['Field', 'Form Value', 'PDF Value', 'PDF Confidence']], use_container_width=True)
    
    st.markdown("**Choose data source for each conflict:**")
    
    # Create resolution controls
    for _, row in df.iterrows():
        field_key = row['field_key']
        field_name = row['Field']
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(f"**{field_name}**")
            st.write(f"Form: {row['Form Value']}")
            st.write(f"PDF: {row['PDF Value']} (confidence: {row['PDF Confidence']})")
        
        with col2:
            if st.button(f"✓ Use Form", key=f"form_{field_key}", type="secondary"):
                conflicts[field_key] = 'form'
                st.rerun()
        
        with col3:
            if st.button(f"📄 Use PDF", key=f"pdf_{field_key}", type="secondary"):
                conflicts[field_key] = 'pdf'
                st.rerun()
    
    return conflicts

def _values_differ(val1: Any, val2: Any, tolerance: float = 0.1) -> bool:
    """Check if two values differ significantly"""
    if val1 is None or val2 is None:
        return False
    
    # For numeric values
    if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
        return abs(val1 - val2) > tolerance
    
    # For string values
    return str(val1).lower().strip() != str(val2).lower().strip()

def _format_field_name(field: str) -> str:
    """Format field name for display"""
    field_names = {
        'hba1c_pct': 'HbA1c (%)',
        'fpg_mmol': 'Fasting Glucose (mmol/L)',
        'ppg2h_mmol': '2h Post-meal Glucose (mmol/L)',
        'bp_sys': 'Systolic BP (mmHg)',
        'bp_dia': 'Diastolic BP (mmHg)',
        'egfr': 'eGFR (mL/min/1.73m²)',
        'creatinine_umol': 'Creatinine (μmol/L)',
        'acr_mgmmol': 'ACR (mg/mmol)',
        'tc': 'Total Cholesterol (mmol/L)',
        'ldl': 'LDL Cholesterol (mmol/L)',
        'hdl': 'HDL Cholesterol (mmol/L)',
        'tg': 'Triglycerides (mmol/L)'
    }
    return field_names.get(field, field.replace('_', ' ').title())

def _format_value(value: Any) -> str:
    """Format value for display"""
    if value is None:
        return "Not provided"
    elif isinstance(value, float):
        return f"{value:.1f}"
    else:
        return str(value)

def create_clinical_snapshot_cards(patient_data: Dict, rules: Dict):
    """Create clinical snapshot cards with traffic light indicators"""
    from utils.formatters import create_clinical_snapshot
    
    snapshot = create_clinical_snapshot(patient_data, rules)
    
    if not snapshot:
        return
    
    st.subheader("📊 Clinical Snapshot")
    
    # Create cards in columns
    cols = st.columns(min(4, len(snapshot)))
    
    card_order = ['hba1c', 'bp', 'bmi', 'ldl']
    
    for i, key in enumerate(card_order):
        if key in snapshot and i < len(cols):
            with cols[i]:
                info = snapshot[key]
                
                # Card styling with traffic light color
                traffic_color = {
                    'green': '#28a745',
                    'amber': '#ffc107', 
                    'red': '#dc3545'
                }.get(info['traffic']['status'], '#6c757d')
                
                metric_name = {
                    'hba1c': 'HbA1c',
                    'bp': 'Blood Pressure',
                    'bmi': 'BMI', 
                    'ldl': 'LDL Cholesterol'
                }.get(key, key.upper())
                
                st.markdown(f"""
                <div style="
                    padding: 1rem;
                    border-left: 4px solid {traffic_color};
                    background-color: #f8f9fa;
                    border-radius: 0.25rem;
                    margin-bottom: 1rem;
                ">
                    <h4 style="margin: 0 0 0.5rem 0; color: #343a40;">{metric_name}</h4>
                    <p style="margin: 0; font-size: 1.2em; font-weight: bold; color: {traffic_color};">
                        {info['value']}
                    </p>
                    <p style="margin: 0.25rem 0 0 0; font-size: 0.9em; color: #6c757d;">
                        Target: {info['target']}
                    </p>
                    <p style="margin: 0.25rem 0 0 0; font-size: 0.9em;">
                        {info['traffic']['display']}
                    </p>
                </div>
                """, unsafe_allow_html=True)

def create_download_button(pdf_content: bytes, filename: str, label: str = "📄 Download PDF Report") -> bool:
    """Create a styled download button for PDF reports"""
    
    return st.download_button(
        label=label,
        data=pdf_content,
        file_name=filename,
        mime="application/pdf",
        type="primary",
        use_container_width=True
    )

def create_urgent_banner(red_flags: List[str]):
    """Create urgent clinical banner for red flag conditions"""
    if not red_flags:
        return
    
    # Create urgent warning banner
    st.error("🚨 **URGENT CLINICAL ATTENTION REQUIRED**")
    
    with st.expander("⚠️ Critical Values Detected - Click to view", expanded=True):
        for flag in red_flags:
            st.warning(f"• {flag}")
        
        st.markdown("""
        **Immediate Actions Required:**
        - Review medication regimen
        - Consider specialist referral
        - Arrange urgent follow-up
        - Patient education on warning signs
        """)

def create_report_tabs(report_data: Dict, patient_data: Dict, rules: Dict):
    """Create tabbed interface for different report views"""
    
    tab1, tab2, tab3, tab4 = st.tabs(["👨‍⚕️ Consultant View", "👤 Patient Summary", "📝 EMR Note", "📚 Citations"])
    
    with tab1:
        st.subheader("Consultant Clinical Report")
        
        # Show clinical snapshot cards
        create_clinical_snapshot_cards(patient_data, rules)
        
        # Executive summary
        if 'executive_summary' in report_data:
            st.markdown("### Executive Summary")
            st.info(report_data['executive_summary'])
        
        # Clinical interpretation
        if 'interpretation' in report_data:
            st.markdown("### Clinical Assessment")
            for i, interp in enumerate(report_data['interpretation'], 1):
                with st.expander(f"Issue {i}: {interp.get('problem', 'Clinical Issue')}"):
                    st.markdown(f"**Assessment:** {interp.get('assessment', '')}")
                    st.markdown(f"**Plan:** {interp.get('plan', '')}")
                    if interp.get('citation_ids'):
                        st.markdown(f"**Evidence:** Citations {', '.join(interp['citation_ids'])}")
        
        # Labs table
        if 'labs_table' in report_data:
            st.markdown("### Laboratory Results")
            df_labs = pd.DataFrame(report_data['labs_table'])
            if not df_labs.empty:
                st.dataframe(df_labs, use_container_width=True)
    
    with tab2:
        # For the enhanced report, we expect a 'full_markdown' field with the complete report
        if 'full_markdown' in report_data and report_data['full_markdown']:
            # Display the full HTML report
            st.components.v1.html(
                report_data['full_markdown'],
                height=800,
                scrolling=True
            )
        else:
            # Fallback to the old format if needed
            st.subheader("Patient Summary Report")
            
            if 'lifestyle_plan' in report_data and report_data['lifestyle_plan']:
                st.markdown("### Your Lifestyle Recommendations")
                for i, rec in enumerate(report_data['lifestyle_plan'], 1):
                    # Handle both dictionary and object access
                    text = rec.get('text') if isinstance(rec, dict) else getattr(rec, 'text', str(rec))
                    st.markdown(f"{i}. {text}")
            
            if 'diet_plan' in report_data and report_data['diet_plan']:
                st.markdown("### Your Diet Plan")
                diet = report_data['diet_plan']
                if isinstance(diet, dict):
                    if 'principles' in diet:
                        st.markdown(diet['principles'])
                elif hasattr(diet, 'principles'):
                    st.markdown(diet.principles)
            
            if 'monitoring_plan' in report_data and report_data['monitoring_plan']:
                st.markdown("### Monitoring Your Diabetes")
                monitoring = report_data['monitoring_plan']
                if isinstance(monitoring, dict):
                    for key, value in monitoring.items():
                        if key != 'citation_ids':
                            st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")
                elif hasattr(monitoring, 'items'):
                    for key, value in monitoring.items():
                        if key != 'citation_ids':
                            st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")
                elif isinstance(monitoring, (list, tuple)):
                    for item in monitoring:
                        st.markdown(f"- {item}")
    
    with tab3:
        st.subheader("EMR Clinical Note")
        
        if 'emr_note' in report_data:
            st.code(report_data['emr_note'], language=None)
        else:
            st.info("EMR note not available")
        
        # Copy button
        if 'emr_note' in report_data:
            if st.button("📋 Copy to Clipboard"):
                st.success("EMR note copied! (Feature requires browser support)")
    
    with tab4:
        st.subheader("Evidence & Citations")
        
        if 'citations' in report_data:
            for citation in report_data['citations']:
                with st.expander(f"[{citation['id']}] {citation['source']}"):
                    st.markdown(f"**Section:** {citation['section']}")
                    if 'text' in citation:
                        st.markdown(citation['text'])
        else:
            st.info("No citations available")

def create_progress_tracker(current_step: str, total_steps: int = 4):
    """Create progress tracker for report generation"""
    steps = [
        "Collecting Data",
        "Processing PDF", 
        "Generating Report",
        "Finalizing"
    ]
    
    current_index = steps.index(current_step) if current_step in steps else 0
    
    # Create progress bar
    progress = (current_index + 1) / len(steps)
    st.progress(progress)
    
    # Create step indicators
    cols = st.columns(len(steps))
    for i, (step, col) in enumerate(zip(steps, cols)):
        with col:
            if i <= current_index:
                st.success(f"✓ {step}")
            else:
                st.info(f"○ {step}")

def create_validation_feedback(patient_data: Dict) -> List[str]:
    """Create validation feedback for patient data completeness"""
    warnings = []
    
    # Check required fields
    required_fields = {
        'name': 'Patient name',
        'dob': 'Date of birth',
        'sex': 'Sex',
        'diabetes_type': 'Diabetes type',
        'height_cm': 'Height',
        'weight_kg': 'Weight'
    }
    
    for field, display_name in required_fields.items():
        if not patient_data.get(field):
            warnings.append(f"Missing {display_name}")
    
    # Check lab data
    labs = patient_data.get('labs', {})
    if not labs.get('hba1c_pct'):
        warnings.append("Missing HbA1c - critical for diabetes management")
    
    # Check recent screening
    screenings = patient_data.get('screenings', {})
    if not any(screenings.values()):
        warnings.append("No recent screening dates recorded")
    
    return warnings

def display_validation_warnings(warnings: List[str]):
    """Display validation warnings to user"""
    if warnings:
        st.warning("⚠️ **Data Completeness Issues**")
        for warning in warnings:
            st.write(f"• {warning}")
        st.info("Reports will be generated with available data, but may be incomplete.")

if __name__ == "__main__":
    # Test components
    st.title("UI Components Test")
    
    # Test snapshot cards
    sample_data = {
        "weight_kg": 78.5,
        "height_cm": 175.0,
        "bp_sys": 127,
        "bp_dia": 83,
        "labs": {
            "hba1c_pct": 8.3,
            "lipids": {"ldl": 3.2}
        }
    }
    
    from rules import load_rules
    rules = load_rules()
    
    create_clinical_snapshot_cards(sample_data, rules)
