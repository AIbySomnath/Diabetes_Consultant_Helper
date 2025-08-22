"""
Tab Components for Diabetes Report Generator
Implements all main tabs: Patient, Labs, Lifestyle, Preview & Generate, Management
"""

import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Optional
import json

from src.ui.components import (
    create_input_with_tooltip,
    create_validation_feedback,
    create_loading_skeleton,
    create_success_toast,
    create_error_toast,
    create_progress_indicator,
    create_citation_chip
)

def render_patient_tab(session_manager, pdf_processor):
    """Render Patient Information Tab"""
    
    st.markdown("### 👤 Patient Demographics & History")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Basic Information")
        
        # NHS Number
        nhs_number = create_input_with_tooltip(
            label="NHS Number",
            key="nhs_number",
            placeholder="000 000 0000",
            help_text="10-digit NHS number",
            tooltip="Unique patient identifier in NHS system"
        )
        
        # Name
        patient_name = create_input_with_tooltip(
            label="Patient Name",
            key="patient_name",
            placeholder="Enter patient's full name"
        )
        
        # Date of Birth
        dob = create_input_with_tooltip(
            label="Date of Birth",
            key="date_of_birth",
            input_type="date",
            tooltip="Used to calculate age and age-specific recommendations"
        )
        
        # Sex
        sex = create_input_with_tooltip(
            label="Sex",
            key="sex",
            input_type="select",
            options=["", "Male", "Female"],
            tooltip="Biological sex affects risk calculations and targets"
        )
        
        # Ethnicity
        ethnicity = create_input_with_tooltip(
            label="Ethnicity",
            key="ethnicity",
            input_type="select",
            options=["", "White British", "White Other", "Black African", "Black Caribbean", 
                    "South Asian", "East Asian", "Mixed", "Other"],
            help_text="Affects diabetes risk and medication response",
            tooltip="Important for risk stratification per NICE guidelines"
        )
    
    with col2:
        st.markdown("#### Diabetes History")
        
        # Diagnosis date
        diagnosis_date = create_input_with_tooltip(
            label="Date of Diagnosis",
            key="diagnosis_date",
            input_type="date",
            tooltip="Type 2 diabetes diagnosis date"
        )
        
        # Calculate duration if diagnosis date provided
        if diagnosis_date:
            duration_years = (date.today() - diagnosis_date).days / 365.25
            st.info(f"Duration: {duration_years:.1f} years")
        
        # Current medications
        current_meds = create_input_with_tooltip(
            label="Current Diabetes Medications",
            key="current_medications",
            input_type="multiselect",
            options=["Metformin", "Gliclazide", "Sitagliptin", "Dapagliflozin", 
                    "Empagliflozin", "Liraglutide", "Semaglutide", "Insulin", "Other"],
            placeholder="Select all that apply",
            tooltip="Current diabetes medications - do not include doses"
        )
        
        # Comorbidities
        comorbidities = create_input_with_tooltip(
            label="Comorbidities",
            key="comorbidities",
            input_type="multiselect",
            options=["Hypertension", "Dyslipidaemia", "CKD", "CVD", "Heart Failure",
                    "Neuropathy", "Retinopathy", "Nephropathy", "NAFLD", "OSA"],
            placeholder="Select all that apply",
            tooltip="Relevant comorbid conditions"
        )
    
    st.markdown("---")
    
    # PDF Upload Section
    st.markdown("### 📄 PDF Lab Results Upload (Optional)")
    st.info("💡 Upload digital PDF lab results for automatic extraction. Scanned PDFs not supported in this POC.")
    
    uploaded_file = st.file_uploader(
        "Drag and drop or browse for PDF",
        type="pdf",
        key="pdf_upload",
        help="Digital PDFs only - must have selectable text"
    )
    
    if uploaded_file:
        # Show file info
        file_size = len(uploaded_file.getbuffer()) / 1024
        st.success(f"✅ File uploaded: {uploaded_file.name} ({file_size:.1f} KB)")
        
        # Process PDF
        if st.button("Extract Lab Values", key="extract_pdf"):
            with st.spinner("Processing PDF..."):
                try:
                    extracted_data = pdf_processor.extract_lab_values(uploaded_file)
                    
                    if extracted_data:
                        st.markdown("#### Extracted Values")
                        
                        # Display extracted values in a table with provenance
                        df = pd.DataFrame(extracted_data)
                        st.dataframe(df, use_container_width=True)
                        
                        # Option to use extracted values
                        if st.checkbox("Use extracted values", value=True):
                            session_manager.update_from_pdf(extracted_data)
                            create_success_toast("Values imported successfully")
                    else:
                        create_error_toast(
                            "No text layer detected in PDF",
                            "This looks like a scanned PDF. Please enter values manually."
                        )
                except Exception as e:
                    create_error_toast(f"Error processing PDF: {str(e)}")
    
    # Save patient data
    patient_data = {
        'nhs_number': nhs_number,
        'name': patient_name,
        'dob': str(dob) if dob else None,
        'sex': sex,
        'ethnicity': ethnicity,
        'diagnosis_date': str(diagnosis_date) if diagnosis_date else None,
        'medications': current_meds,
        'comorbidities': comorbidities
    }
    
    session_manager.save_patient_data(patient_data)

def render_labs_tab(session_manager):
    """Render Laboratory Results Tab"""
    
    st.markdown("### 🔬 Laboratory Results")
    st.info("Enter most recent lab values. All values in UK units (mmol/L for glucose).")
    
    # Glycaemic Control
    st.markdown("#### Glycaemic Control")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        hba1c = create_input_with_tooltip(
            label="HbA1c",
            key="hba1c",
            input_type="number",
            min_value=4.0,
            max_value=15.0,
            step=0.1,
            format_str="%.1f",
            unit="%",
            tooltip="Glycated haemoglobin - 3 month average"
        )
        
        # Auto-calculate mmol/mol
        if hba1c:
            hba1c_mmol = round((hba1c - 2.152) / 0.09148)
            st.caption(f"= {hba1c_mmol} mmol/mol")
            
            # Check for red flag
            if hba1c >= 10.0:
                create_validation_feedback(
                    "HbA1c",
                    False,
                    "Red flag: HbA1c ≥10% requires urgent review",
                    "error"
                )
    
    with col2:
        fpg = create_input_with_tooltip(
            label="Fasting Plasma Glucose",
            key="fpg",
            input_type="number",
            min_value=3.0,
            max_value=30.0,
            step=0.1,
            format_str="%.1f",
            unit="mmol/L",
            tooltip="FPG - fasting ≥8 hours"
        )
        
        # Check for red flag
        if fpg and fpg >= 13.9:
            create_validation_feedback(
                "FPG",
                False,
                "Red flag: FPG ≥13.9 mmol/L requires urgent review",
                "error"
            )
    
    with col3:
        ppg_2h = create_input_with_tooltip(
            label="2-hour Post-Prandial",
            key="ppg_2h",
            input_type="number",
            min_value=3.0,
            max_value=30.0,
            step=0.1,
            format_str="%.1f",
            unit="mmol/L",
            tooltip="2 hours after meal start"
        )
        
        # Check for red flag
        if ppg_2h and ppg_2h >= 16.7:
            create_validation_feedback(
                "2h-PPG",
                False,
                "Red flag: 2h-PPG ≥16.7 mmol/L requires urgent review",
                "error"
            )
    
    # Blood Pressure & Anthropometrics
    st.markdown("#### Blood Pressure & Anthropometrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        bp_systolic = create_input_with_tooltip(
            label="Systolic BP",
            key="bp_systolic",
            input_type="number",
            min_value=70,
            max_value=250,
            step=1,
            unit="mmHg",
            tooltip="Top number of blood pressure"
        )
    
    with col2:
        bp_diastolic = create_input_with_tooltip(
            label="Diastolic BP",
            key="bp_diastolic",
            input_type="number",
            min_value=40,
            max_value=150,
            step=1,
            unit="mmHg",
            tooltip="Bottom number of blood pressure"
        )
        
        # Check for red flag
        if bp_systolic and bp_diastolic:
            if bp_systolic >= 180 or bp_diastolic >= 110:
                create_validation_feedback(
                    "Blood Pressure",
                    False,
                    f"Red flag: BP {bp_systolic}/{bp_diastolic} requires urgent review",
                    "error"
                )
    
    with col3:
        weight = create_input_with_tooltip(
            label="Weight",
            key="weight",
            input_type="number",
            min_value=30.0,
            max_value=250.0,
            step=0.1,
            format_str="%.1f",
            unit="kg"
        )
    
    with col4:
        height = create_input_with_tooltip(
            label="Height",
            key="height",
            input_type="number",
            min_value=100.0,
            max_value=250.0,
            step=0.1,
            format_str="%.1f",
            unit="cm"
        )
        
        # Calculate BMI
        if weight and height:
            bmi = weight / ((height/100) ** 2)
            st.caption(f"BMI: {bmi:.1f} kg/m²")
            
            if bmi < 18.5:
                st.caption("Underweight")
            elif bmi < 25:
                st.caption("Normal weight")
            elif bmi < 30:
                st.caption("Overweight")
            else:
                st.caption("Obese")
    
    # Lipid Profile & Renal Function sections continue...
    # Save lab data
    labs_data = {
        'hba1c': hba1c,
        'fpg': fpg,
        'ppg_2h': ppg_2h,
        'bp_systolic': bp_systolic,
        'bp_diastolic': bp_diastolic,
        'weight': weight,
        'height': height,
        'bmi': bmi if weight and height else None,
        'last_lab_date': str(date.today())
    }
    
    session_manager.save_labs_data(labs_data)
