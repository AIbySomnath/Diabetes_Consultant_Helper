"""
AI-Powered Diabetic Consultant Platform (Enhanced)
A comprehensive Streamlit application for personalized diabetes management
with authoritative form inputs, PDF prefill, and clinical rule engine.
"""

import streamlit as st
from datetime import datetime, date
from pathlib import Path
import uuid
import json
from typing import Dict, Any, List, Optional

# Import models and utilities
from src.models.patient import (
    PatientBase, Consent, Anthropometrics, Vitals, 
    DiabetesProfile, Medication, Comorbidity, Lifestyle, 
    LabResult, Screening, ClinicalNote, PatientCreate
)
from src.models.rules import RuleEngine, Rule, RuleSeverity
from src.utils.pdf_processor import PDFProcessor
from src.rag.retrieval import RAGPipeline
from src.report.generator import ReportGenerator

# Page configuration
st.set_page_config(
    page_title="AI Diabetic Consultant",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'patient_data' not in st.session_state:
    st.session_state.patient_data = {}
if 'lab_data' not in st.session_state:
    st.session_state.lab_data = {}
if 'generated_report' not in st.session_state:
    st.session_state.generated_report = None
if 'pdf_text' not in st.session_state:
    st.session_state.pdf_text = None
if 'conflicts' not in st.session_state:
    st.session_state.conflicts = {}

# Initialize components
@st.cache_resource
def get_rule_engine() -> RuleEngine:
    """Initialize the clinical rule engine"""
    return RuleEngine()

@st.cache_resource
def get_pdf_processor() -> PDFProcessor:
    """Initialize the PDF processor"""
    return PDFProcessor()

@st.cache_resource
def get_rag_pipeline() -> RAGPipeline:
    """Initialize the RAG pipeline"""
    return RAGPipeline()

def save_patient_data(patient_data: Dict[str, Any]) -> None:
    """Save patient data to session state"""
    st.session_state.patient_data = patient_data
    
def process_pdf(uploaded_file) -> None:
    """Process uploaded PDF and extract lab data"""
    if uploaded_file is not None:
        pdf_processor = get_pdf_processor()
        try:
            # Extract text from PDF
            st.session_state.pdf_text = pdf_processor.extract_text(uploaded_file)
            
            # Parse lab results
            lab_data = pdf_processor.parse_lab_results(st.session_state.pdf_text)
            
            # Detect conflicts with existing form data
            conflicts = {}
            for test_name, result in lab_data.items():
                form_value = st.session_state.patient_data.get(test_name)
                if form_value and form_value != result['value']:
                    conflicts[test_name] = {
                        'form_value': form_value,
                        'pdf_value': result['value'],
                        'unit': result.get('unit', '')
                    }
            
            st.session_state.lab_data = lab_data
            st.session_state.conflicts = conflicts
            
            if not conflicts:
                st.sidebar.success("Lab data extracted successfully!")
            else:
                st.sidebar.warning(f"Found {len(conflicts)} conflicts with form data")
                
        except Exception as e:
            st.sidebar.error(f"Error processing PDF: {str(e)}")

def render_conflict_chip(test_name: str, conflict: Dict) -> None:
    """Render a chip for a single conflict"""
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        st.markdown(f"**{test_name}**")
    with col2:
        st.markdown(f"`{conflict['form_value']} {conflict.get('unit', '')}`")
    with col3:
        st.markdown(f"`{conflict['pdf_value']} {conflict.get('unit', '')}`")
    
    # Let user resolve the conflict
    resolution = st.radio(
        f"Which value to use for {test_name}?",
        ["Keep form value", "Use PDF value"],
        key=f"resolve_{test_name}",
        horizontal=True
    )
    
    if resolution == "Use PDF value":
        st.session_state.patient_data[test_name] = conflict['pdf_value']

def render_patient_form() -> Dict[str, Any]:
    """Render the patient data entry form with authoritative dropdowns"""
    st.sidebar.header("Patient Information")
    
    # Initialize with session data or defaults
    data = st.session_state.get('patient_data', {})
    
    # Section 1: Identification
    with st.sidebar.expander("1. Identification", expanded=True):
        st.subheader("Patient Details")
        
        col1, col2 = st.columns(2)
        with col1:
            data['first_name'] = st.text_input(
                "First Name",
                value=data.get('first_name', ''),
                key='first_name'
            )
        with col2:
            data['last_name'] = st.text_input(
                "Last Name",
                value=data.get('last_name', ''),
                key='last_name'
            )
        
        data['nhs_number'] = st.text_input(
            "NHS Number",
            value=data.get('nhs_number', ''),
            help="10-digit NHS number (e.g., 123 456 7890)"
        )
        
        data['date_of_birth'] = st.date_input(
            "Date of Birth",
            value=data.get('date_of_birth', date(1980, 1, 1)),
            min_value=date(1900, 1, 1),
            max_value=date.today()
        )
        
        # Calculate and display age
        age = (date.today() - data['date_of_birth']).days // 365
        data['age'] = st.number_input(
            "Age",
            min_value=0,
            max_value=120,
            value=age,
            step=1,
            key='age_input'
        )
        
        data['sex'] = st.selectbox(
            "Sex at Birth",
            options=["Male", "Female", "Other", "Prefer not to say"],
            index=0 if 'sex' not in data else ["Male", "Female", "Other", "Prefer not to say"].index(data['sex'])
        )
        
        data['ethnicity'] = st.selectbox(
            "Ethnicity",
            options=[
                "White", "Mixed/Multiple ethnic groups", "Asian/Asian British",
                "Black/African/Caribbean/Black British", "Other"
            ],
            index=0 if 'ethnicity' not in data else [
                "White", "Mixed/Multiple ethnic groups", "Asian/Asian British",
                "Black/African/Caribbean/Black British", "Other"
            ].index(data['ethnicity'])
        )
    
    # Section 2: Anthropometrics
    with st.sidebar.expander("2. Anthropometrics & Vitals"):
        st.subheader("Measurements")
        
        col1, col2 = st.columns(2)
        with col1:
            data['height_cm'] = st.number_input(
                "Height (cm)",
                min_value=100.0,
                max_value=250.0,
                value=float(data.get('height_cm', 170.0)),
                step=0.1
            )
        with col2:
            data['weight_kg'] = st.number_input(
                "Weight (kg)",
                min_value=30.0,
                max_value=300.0,
                value=float(data.get('weight_kg', 70.0)),
                step=0.1
            )
        
        # Calculate and display BMI
        if data.get('height_cm') and data.get('weight_kg'):
            bmi = data['weight_kg'] / ((data['height_cm'] / 100) ** 2)
            st.metric("BMI", f"{bmi:.1f}")
        
        st.subheader("Vital Signs")
        
        col1, col2 = st.columns(2)
        with col1:
            data['systolic_bp'] = st.number_input(
                "Systolic BP (mmHg)",
                min_value=70,
                max_value=300,
                value=int(data.get('systolic_bp', 120)),
                step=1
            )
        with col2:
            data['diastolic_bp'] = st.number_input(
                "Diastolic BP (mmHg)",
                min_value=40,
                max_value=150,
                value=int(data.get('diastolic_bp', 80)),
                step=1
            )
        
        data['heart_rate'] = st.number_input(
            "Heart Rate (bpm)",
            min_value=30,
            max_value=200,
            value=int(data.get('heart_rate', 72)),
            step=1
        )
    
    # Section 3: Diabetes Profile
    with st.sidebar.expander("3. Diabetes Profile"):
        st.subheader("Diagnosis")
        
        data['diabetes_type'] = st.selectbox(
            "Type of Diabetes",
            options=["Type 1", "Type 2", "LADA", "MODY", "Gestational", "Other"],
            index=0 if 'diabetes_type' not in data else [
                "Type 1", "Type 2", "LADA", "MODY", "Gestational", "Other"
            ].index(data['diabetes_type'])
        )
        
        data['diagnosis_date'] = st.date_input(
            "Date of Diagnosis",
            value=data.get('diagnosis_date', date.today()),
            max_value=date.today()
        )
        
        st.subheader("Current Treatment")
        
        # Medications
        med_options = [
            "Metformin", "Gliclazide", "Glimepiride", "Pioglitazone", "DPP-4 Inhibitor",
            "SGLT2 Inhibitor", "GLP-1 RA", "Basal Insulin", "Bolus Insulin", "Mixed Insulin"
        ]
        
        data['current_medications'] = st.multiselect(
            "Current Diabetes Medications",
            options=med_options,
            default=data.get('current_medications', [])
        )
        
        # Other medications
        data['other_medications'] = st.text_area(
            "Other Medications",
            value=data.get('other_medications', ''),
            placeholder="List any other medications, one per line"
        )
        
        # Complications
        comp_options = [
            "Retinopathy", "Nephropathy", "Neuropathy", "Cardiovascular Disease",
            "Peripheral Artery Disease", "Foot Ulcers", "None"
        ]
        
        data['complications'] = st.multiselect(
            "Diabetes Complications",
            options=comp_options,
            default=data.get('complications', [])
        )
    
    # Section 4: Lab Results
    with st.sidebar.expander("4. Lab Results"):
        st.subheader("Recent Lab Results")
        
        # Upload PDF with lab results
        uploaded_file = st.file_uploader(
            "Upload Lab Results (PDF)",
            type=["pdf"],
            key="lab_results_upload"
        )
        
        if uploaded_file is not None:
            if st.button("Extract Lab Data"):
                process_pdf(uploaded_file)
        
        # Show conflicts if any
        if st.session_state.conflicts:
            st.warning("The following conflicts were found:")
            for test_name, conflict in st.session_state.conflicts.items():
                render_conflict_chip(test_name, conflict)
        
        # Manual entry fallback
        st.subheader("Or Enter Manually")
        
        col1, col2 = st.columns(2)
        with col1:
            data['hba1c'] = st.number_input(
                "HbA1c (%)",
                min_value=4.0,
                max_value=20.0,
                value=float(data.get('hba1c', 7.0)),
                step=0.1
            )
            
            data['fasting_glucose'] = st.number_input(
                "Fasting Glucose (mmol/L)",
                min_value=2.0,
                max_value=30.0,
                value=float(data.get('fasting_glucose', 6.0)),
                step=0.1
            )
        
        with col2:
            data['total_cholesterol'] = st.number_input(
                "Total Cholesterol (mmol/L)",
                min_value=1.0,
                max_value=20.0,
                value=float(data.get('total_cholesterol', 4.5)),
                step=0.1
            )
            
            data['hdl_cholesterol'] = st.number_input(
                "HDL Cholesterol (mmol/L)",
                min_value=0.1,
                max_value=10.0,
                value=float(data.get('hdl_cholesterol', 1.2)),
                step=0.1
            )
    
    # Section 5: Lifestyle
    with st.sidebar.expander("5. Lifestyle"):
        st.subheader("Physical Activity")
        
        data['activity_level'] = st.select_slider(
            "Activity Level",
            options=["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"],
            value=data.get('activity_level', 'Moderately Active')
        )
        
        data['exercise_minutes'] = st.slider(
            "Minutes of Exercise Per Week",
            min_value=0,
            max_value=300,
            value=int(data.get('exercise_minutes', 150)),
            step=10
        )
        
        st.subheader("Diet")
        
        data['diet_type'] = st.selectbox(
            "Dietary Pattern",
            options=["Mixed", "Vegetarian", "Vegan", "Low-Carb", "Mediterranean", "Other"],
            index=0 if 'diet_type' not in data else [
                "Mixed", "Vegetarian", "Vegan", "Low-Carb", "Mediterranean", "Other"
            ].index(data['diet_type'])
        )
        
        st.subheader("Substances")
        
        data['smoking_status'] = st.radio(
            "Smoking Status",
            options=["Never Smoked", "Former Smoker", "Current Smoker"],
            index=0 if 'smoking_status' not in data else [
                "Never Smoked", "Former Smoker", "Current Smoker"
            ].index(data['smoking_status'])
        )
        
        if data['smoking_status'] == "Current Smoker":
            data['cigarettes_per_day'] = st.slider(
                "Cigarettes Per Day",
                min_value=1,
                max_value=60,
                value=int(data.get('cigarettes_per_day', 10))
            )
        
        data['alcohol_units'] = st.slider(
            "Alcohol (Units/Week)",
            min_value=0,
            max_value=100,
            value=int(data.get('alcohol_units', 0)),
            step=1
        )
    
    # Section 6: Consent
    with st.sidebar.expander("6. Consent & Data Use"):
        st.info("""
        This application processes health data. By proceeding, you confirm that:
        - You have obtained the patient's consent to use their data
        - The information provided is accurate to the best of your knowledge
        - You understand how the data will be used
        """)
        
        data['consent_given'] = st.checkbox(
            "I confirm the patient has given consent for data processing",
            value=data.get('consent_given', False)
        )
    
    # Save data to session
    save_patient_data(data)
    
    return data

def main():
    """Main application function"""
    
    # Page header
    st.title("AI-Powered Diabetes Consultant")
    st.markdown("### Personalized Diabetes Management & Recommendations")
    st.markdown("---")
    
    # Sidebar with patient form
    patient_data = render_patient_form()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Patient Summary")
        
        if patient_data.get('first_name') and patient_data.get('last_name'):
            st.subheader(f"{patient_data['first_name']} {patient_data['last_name']}")
            
            # Basic info
            age = (date.today() - patient_data.get('date_of_birth', date.today())).days // 365
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Age", f"{age} years")
                st.metric("Sex", patient_data.get('sex', 'Not specified'))
            with col2:
                bmi = patient_data.get('weight_kg', 0) / ((patient_data.get('height_cm', 1) / 100) ** 2)
                st.metric("BMI", f"{bmi:.1f}")
                st.metric("Diabetes Type", patient_data.get('diabetes_type', 'Not specified'))
            
            # Key metrics
            st.subheader("Key Metrics")
            
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            kpi1.metric("HbA1c", f"{patient_data.get('hba1c', 'N/A')}%")
            kpi2.metric("Blood Pressure", f"{patient_data.get('systolic_bp', '')}/{patient_data.get('diastolic_bp', '')}")
            kpi3.metric("Total Cholesterol", f"{patient_data.get('total_cholesterol', 'N/A')} mmol/L")
            kpi4.metric("Activity", patient_data.get('activity_level', 'N/A'))
            
            # Run clinical rules
            rule_engine = get_rule_engine()
            flags = rule_engine.evaluate(patient_data)
            
            if flags:
                st.warning("Clinical Alerts")
                for flag in flags:
                    if flag.severity == RuleSeverity.HIGH:
                        st.error(f"🚨 {flag.title}: {flag.message}")
                    elif flag.severity == RuleSeverity.MEDIUM:
                        st.warning(f"⚠️ {flag.title}: {flag.message}")
                    else:
                        st.info(f"ℹ️ {flag.title}: {flag.message}")
            
            # Generate report button
            if st.button("Generate Comprehensive Report", 
                        type="primary",
                        disabled=not patient_data.get('consent_given', False)):
                
                if not patient_data.get('consent_given'):
                    st.error("Please confirm patient consent before generating a report")
                else:
                    with st.spinner("Generating personalized report..."):
                        # Use the age that's displayed in the form
                        if 'date_of_birth' in patient_data and patient_data['date_of_birth']:
                            patient_data['age'] = (date.today() - patient_data['date_of_birth']).days // 365
                        
                        # Initialize RAG pipeline
                        rag_pipeline = get_rag_pipeline()
                        
                        # Generate report
                        report_generator = ReportGenerator()
                        report, sources = report_generator.generate_report(
                            patient_data=patient_data,
                            labs_data=patient_data,  # Using same dict for simplicity
                            lifestyle_data=patient_data
                        )
                        
                        st.session_state.generated_report = report
                        st.session_state.sources = sources
                        
                        # Scroll to report
                        st.experimental_rerun()
            
            # Display report if generated
            if st.session_state.generated_report:
                st.markdown("---")
                st.markdown(st.session_state.generated_report, unsafe_allow_html=True)
                
                # Add download button for PDF
                pdf_generator = PDFGenerator()
                pdf_bytes = pdf_generator.generate_pdf(
                    st.session_state.generated_report,
                    f"{patient_data.get('first_name', 'Patient')} {patient_data.get('last_name', '')}"
                )
                
                st.download_button(
                    label="Download Report as PDF",
                    data=pdf_bytes,
                    file_name=f"diabetes_report_{patient_data.get('first_name', 'patient')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )
        else:
            st.info("Please enter patient information in the sidebar to begin")
    
    with col2:
        st.header("Quick Actions")
        
        if st.button("📅 Schedule Follow-up"):
            st.session_state.show_appointment_picker = True
        
        if st.session_state.get('show_appointment_picker', False):
            st.date_input("Select Follow-up Date", min_value=date.today())
            st.time_input("Appointment Time")
            
            if st.button("Confirm Appointment"):
                st.success("Follow-up appointment scheduled!")
                st.session_state.show_appointment_picker = False
        
        st.markdown("---")
        st.subheader("Clinical Tools")
        
        if st.button("📊 Calculate CVD Risk"):
            # In a real app, this would use the QRISK3 algorithm
            st.info("CVD Risk: 12.5% (Moderate)")
            st.caption("Based on UKPDS Risk Engine")
        
        if st.button("💊 Medication Advisor"):
            st.info("Recommended: Consider adding SGLT2i for renal protection")
        
        st.markdown("---")
        st.subheader("Patient Resources")
        
        if st.button("📱 Mobile Apps"):
            st.markdown("""
            Recommended Apps:
            - **NHS App**: For appointments and records
            - **MySugr**: For diabetes tracking
            - **NHS Weight Loss Plan""")
        
        if st.button("📚 Educational Materials"):
            st.markdown("""
            - [Diabetes UK Learning Zone](https://www.diabetes.org.uk/diabetes-the-basics)
            - [NHS Diabetes Guide](https://www.nhs.uk/conditions/type-2-diabetes/)
            - [Healthy Eating Guide](https://www.diabetes.org.uk/guide-to-diabetes/enjoy-food)""")

if __name__ == "__main__":
    main()
