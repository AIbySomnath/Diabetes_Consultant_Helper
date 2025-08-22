"""
AI-Powered Diabetic Consultant Platform (Sidebar UI)
A comprehensive Streamlit application for personalized diabetes management
"""

import streamlit as st
from datetime import datetime, timedelta, date
import uuid
from pathlib import Path
import pandas as pd

# Import custom modules (wrappers around existing core modules)
from src.utils.data_processor import DataProcessor
from src.utils.rag_system import RAGSystem
from src.utils.report_generator import ReportGenerator
from src.utils.pdf_generator import PDFGenerator
from src.utils.chat_interface import ChatInterface
from src.utils.validators import validate_red_flags
from src.ui.components import create_urgent_banner, create_at_glance_bar

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
if 'generated_report' not in st.session_state:
    st.session_state.generated_report = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Initialize components
@st.cache_resource
def initialize_rag_system():
    """Initialize the RAG system with medical knowledge base"""
    return RAGSystem()

@st.cache_resource
def initialize_data_processor():
    """Initialize the data processing utilities"""
    return DataProcessor()


def main():
    """Main application interface"""

    # Header
    st.title("🩺 AI-Powered Diabetic Consultant")
    st.markdown("### Personalized Diabetes Management & Health Recommendations")
    st.markdown("---")

    # Initialize systems
    rag_system = initialize_rag_system()
    data_processor = initialize_data_processor()

    # Sidebar for patient data input
    with st.sidebar:
        st.header("📋 Patient Information")

        # Patient Name
        st.subheader("Patient Details")
        patient_name = st.text_input("Name of Patient", value="", placeholder="Enter patient name")

        # Phase 1: Core Demographics
        st.subheader("Demographics")
        age = st.number_input("Age", min_value=1, max_value=120, value=45)
        gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"], index=0)
        weight = st.number_input("Weight (kg)", min_value=30.0, max_value=300.0, value=72.1, step=0.1)
        height = st.number_input("Height (cm)", min_value=100, max_value=250, value=168)

        # Medical Information
        st.subheader("Medical History")
        diabetes_type = st.selectbox("Diabetes Type", ["Type 1", "Type 2", "Pre-diabetes", "Gestational", "Other"])
        diagnosis_year = st.number_input("Year of Diagnosis", min_value=1950, max_value=2100, value=2020)
        hba1c = st.number_input("Latest HbA1c (%)", min_value=4.0, max_value=15.0, value=7.0, step=0.1)

        # Current Treatment
        st.subheader("Current Treatment")
        medications = st.multiselect(
            "Current Medications",
            ["Metformin", "Insulin", "Gliclazide", "Pioglitazone", "Empagliflozin", "Liraglutide", "Other"]
        )
        medication_other = st.text_input("Other medications (if selected)")

        # Lifestyle
        st.subheader("Lifestyle Factors")
        activity_level = st.selectbox("Physical Activity Level", ["Sedentary", "Light", "Moderate", "Active", "Very Active"])
        smoking = st.selectbox("Smoking Status", ["Never", "Former", "Current"])
        alcohol = st.selectbox("Alcohol Consumption", ["None", "Occasional", "Moderate", "Heavy"])

        # Recent Readings
        st.subheader("Recent Readings")
        col1, col2 = st.columns(2)
        with col1:
            blood_pressure_sys = st.number_input("Systolic BP (mmHg)", min_value=80, max_value=250, value=120)
            blood_pressure_dia = st.number_input("Diastolic BP (mmHg)", min_value=40, max_value=150, value=80)
            cholesterol = st.number_input("Total Cholesterol (mmol/L)", min_value=2.0, max_value=15.0, value=5.0, step=0.1)
        
        with col2:
            fpg = st.number_input("FPG (mmol/L)", min_value=2.0, max_value=30.0, value=5.5, step=0.1, 
                                help="Fasting Plasma Glucose")
            ppg_2h = st.number_input("2h-PPG (mmol/L)", min_value=2.0, max_value=40.0, value=7.8, step=0.1,
                                   help="2-hour Post-Prandial Glucose")
            lab_date = st.date_input("Last Lab Date", value=date.today())

    # Build interim patient/lab dicts for validation and at-a-glance
    interim_patient = {
        'name': patient_name,
        'sex': gender,
        'dob': None,
    }
    interim_labs = {
        'hba1c': hba1c,
        'bp_systolic': blood_pressure_sys,
        'bp_diastolic': blood_pressure_dia,
        'weight': weight,
        'height': height,
        'bmi': (weight / ((height/100) ** 2)) if height else None,
    }

    # Red flags banner
    red_flags = validate_red_flags(interim_patient, interim_labs)
    if red_flags:
        create_urgent_banner(red_flags)

    # At-a-glance sticky bar if labs available
    if interim_labs.get('hba1c') or interim_labs.get('bp_systolic'):
        create_at_glance_bar(interim_labs)

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("📄 Health Report Upload")
        uploaded_file = st.file_uploader(
            "Upload recent medical reports (PDF)",
            type=['pdf'],
            help="Upload recent blood tests, doctor reports, or medical summaries"
        )

        if uploaded_file is not None:
            st.success(f"File uploaded: {uploaded_file.name}")

            # Process uploaded file
            with st.spinner("Processing uploaded document..."):
                extracted_data = data_processor.extract_pdf_data(uploaded_file)
                if extracted_data:
                    st.info("✅ Medical data extracted from uploaded report")
                    with st.expander("View extracted information"):
                        st.json(extracted_data)

    with col2:
        st.header("⚙️ Report Settings")

        report_language = st.selectbox("Report Language", ["English (UK)", "English (US)"])
        report_detail = st.selectbox("Detail Level", ["Summary", "Detailed", "Comprehensive"])
        include_diet_plan = st.checkbox("Include Personalized Diet Plan", value=True)
        include_exercise = st.checkbox("Include Exercise Recommendations", value=True)
        include_monitoring = st.checkbox("Include Monitoring Schedule", value=True)

    # Generate Report Button
    st.markdown("---")
    c1, c2, c3 = st.columns([1, 2, 1])

    with c2:
        if st.button("🤖 Generate AI Health Report", type="primary", use_container_width=True):
            # Compile patient data
            patient_data = {
                'session_id': st.session_state.session_id,
                'name': patient_name,
                'age': age,  # Add age at the top level
                'demographics': {
                    'age': age,
                    'gender': gender,
                    'weight': weight,
                    'height': height,
                    'bmi': weight / ((height/100) ** 2) if height else None
                },
                'medical_history': {
                    'diabetes_type': diabetes_type,
                    'diagnosis_year': diagnosis_year,
                    'hba1c': hba1c,
                    'medications': medications,
                    'medication_other': medication_other,
                    'lab_date': lab_date.isoformat()
                },
                'lifestyle': {
                    'activity_level': activity_level,
                    'smoking': smoking,
                    'alcohol': alcohol
                },
                'vitals': {
                    'blood_pressure': f"{blood_pressure_sys}/{blood_pressure_dia}",
                    'cholesterol': cholesterol
                },
                'labs': {
                    'fpg': fpg,
                    'ppg_2h': ppg_2h,
                    'lab_date': lab_date.isoformat()
                },
                'report_settings': {
                    'language': report_language,
                    'detail_level': report_detail,
                    'include_diet_plan': include_diet_plan,
                    'include_exercise': include_exercise,
                    'include_monitoring': include_monitoring
                }
            }

            # Store in session state
            st.session_state.patient_data = patient_data

            # Generate report using RAG + LLM (POC uses mock/cached pipeline)
            with st.spinner("🔍 Analyzing your health data with AI..."):
                try:
                    report_generator = ReportGenerator(rag_system)
                    report_content = report_generator.generate_comprehensive_report(patient_data)
                    st.session_state.generated_report = report_content
                    st.success("✅ Report generated successfully!")
                except Exception as e:
                    st.error(f"Error generating report: {str(e)}")
                    st.info("Please check your OpenAI API key in the .env file")

    # Display Generated Report
    if st.session_state.generated_report:
        st.markdown("---")
        st.header("📊 Your Personalized Health Report")

        # Display report sections
        report = st.session_state.generated_report

        # Health Summary
        if 'health_summary' in report:
            st.subheader("🔍 Health Summary")
            st.write(report['health_summary'])

        # Lifestyle Recommendations
        if 'lifestyle_recommendations' in report:
            st.subheader("🏃‍♂️ Lifestyle Recommendations")
            st.write(report['lifestyle_recommendations'])

        # Diet Plan
        if 'diet_plan' in report and st.session_state.patient_data.get('report_settings', {}).get('include_diet_plan', True):
            st.subheader("🥗 Personalized Diet Plan")
            st.write(report['diet_plan'])

        # Monitoring & Follow-up
        if 'monitoring_followup' in report:
            st.subheader("📅 Monitoring & Follow-up")
            st.write(report['monitoring_followup'])

        # Full Markdown preview
        if 'full_markdown' in report:
            st.markdown("---")
            st.subheader("📄 Full Report (Markdown)")
            st.markdown(report['full_markdown'])

        # Download PDF Report
        st.markdown("---")
        d1, d2, d3 = st.columns([1, 2, 1])
        with d2:
            if st.button("📄 Download PDF Report", type="secondary", use_container_width=True):
                try:
                    pdf_generator = PDFGenerator()
                    pdf_content = pdf_generator.generate_pdf_report(
                        st.session_state.patient_data,
                        st.session_state.generated_report
                    )

                    st.download_button(
                        label="💾 Click here to download your report",
                        data=pdf_content,
                        file_name=f"diabetes_report_{st.session_state.session_id[:8]}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error generating PDF: {str(e)}")

    # Chat Interface
    st.markdown("---")
    st.header("💬 Ask Questions About Your Health")

    with st.expander("Chat with your AI Health Assistant", expanded=False):
        chat_interface = ChatInterface(rag_system)

        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # Chat input
        prompt = st.chat_input("Ask about diabetes management, diet, exercise, or medications...")
        if prompt:
            st.session_state.chat_history.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = chat_interface.get_response(
                        prompt,
                        st.session_state.patient_data if 'patient_data' in st.session_state else {}
                    )
                    st.write(response)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})

    # Footer
    st.markdown("---")
    st.markdown(
        f"""
        <div style='text-align: center; color: #666; font-size: 0.8em;'>
        <p>🏥 This AI assistant provides general health information and should not replace professional medical advice.<br>
        Always consult with your healthcare provider for personalized medical guidance.</p>
        <p>Session ID: {st.session_state.session_id[:8]}</p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
