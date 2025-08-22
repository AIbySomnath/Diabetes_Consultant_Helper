"""
Extended Tab Functions for Diabetes Report Generator
"""

import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List

def render_lifestyle_tab(session_manager):
    """Render Lifestyle & Preferences Tab"""
    
    st.markdown("### 🏃 Lifestyle Factors")
    
    # Physical Activity
    st.markdown("#### Physical Activity")
    col1, col2 = st.columns(2)
    
    with col1:
        from src.ui.components import create_input_with_tooltip
        
        activity_level = create_input_with_tooltip(
            label="Current Activity Level",
            key="activity_level",
            input_type="select",
            options=["", "Sedentary", "Lightly Active", "Moderately Active", "Very Active"],
            tooltip="Average weekly physical activity"
        )
        
        activity_minutes = create_input_with_tooltip(
            label="Minutes per Week",
            key="activity_minutes",
            input_type="number",
            min_value=0,
            max_value=1000,
            step=10,
            help_text="Total moderate activity minutes/week",
            tooltip="NICE recommends ≥150 minutes/week"
        )
    
    with col2:
        activity_barriers = create_input_with_tooltip(
            label="Barriers to Exercise",
            key="activity_barriers",
            input_type="multiselect",
            options=["Joint pain", "Breathlessness", "Lack of time", "Mobility issues",
                    "No facilities", "Lack of motivation", "Fear of hypoglycaemia"],
            placeholder="Select all that apply"
        )
    
    # Dietary Habits
    st.markdown("#### Dietary Habits")
    col1, col2 = st.columns(2)
    
    with col1:
        dietary_pattern = create_input_with_tooltip(
            label="Dietary Pattern",
            key="dietary_pattern",
            input_type="select",
            options=["", "Standard UK", "Mediterranean", "Low carb", "Vegetarian",
                    "Vegan", "Halal", "Kosher", "South Asian", "Caribbean", "Other"],
            tooltip="Current dietary pattern or cultural preferences"
        )
        
        meals_per_day = create_input_with_tooltip(
            label="Meals per Day",
            key="meals_per_day",
            input_type="select",
            options=["", "1-2", "3", "4-5", "6+"],
            help_text="Including snacks"
        )
    
    with col2:
        dietary_restrictions = create_input_with_tooltip(
            label="Dietary Restrictions/Allergies",
            key="dietary_restrictions",
            input_type="multiselect",
            options=["Gluten-free", "Lactose intolerant", "Nut allergy", "Egg allergy",
                    "Fish/seafood allergy", "Soya allergy", "Other"],
            placeholder="Select all that apply"
        )
    
    # Goals & Preferences
    st.markdown("#### Personal Goals")
    
    primary_goal = create_input_with_tooltip(
        label="Primary Health Goal",
        key="primary_goal",
        input_type="select",
        options=["", "Improve HbA1c", "Lose weight", "Increase activity",
                "Reduce medications", "Prevent complications", "Improve energy"],
        tooltip="Most important goal for the patient"
    )
    
    # Save lifestyle data
    lifestyle_data = {
        'activity_level': activity_level,
        'activity_minutes': activity_minutes,
        'activity_barriers': activity_barriers,
        'dietary_pattern': dietary_pattern,
        'meals_per_day': meals_per_day,
        'dietary_restrictions': dietary_restrictions,
        'primary_goal': primary_goal
    }
    
    session_manager.save_lifestyle_data(lifestyle_data)

def render_preview_generate_tab(session_manager, rag_pipeline, report_generator, data_persistence):
    """Render Preview & Generate Report Tab"""
    
    st.markdown("### 📄 Report Preview & Generation")
    
    # Data completeness check
    patient_data = st.session_state.get('patient_data', {})
    labs_data = st.session_state.get('labs_data', {})
    lifestyle_data = st.session_state.get('lifestyle_data', {})
    
    # Check minimum required fields
    if not patient_data.get('name') or not labs_data.get('hba1c'):
        st.warning("⚠️ Please enter patient name and HbA1c at minimum")
        return
    
    # Generation controls
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.button("🎯 Generate Full Report", type="primary", use_container_width=True):
            generate_report(session_manager, rag_pipeline, report_generator, data_persistence, patient_data, labs_data, lifestyle_data)
    
    with col2:
        model_choice = st.selectbox(
            "Model",
            ["GPT-4", "GPT-4-mini"],
            help="GPT-4 for best quality"
        )
    
    # Report preview area
    if 'generated_report' in st.session_state:
        st.markdown("---")
        st.markdown("### Generated Report Preview")
        
        # Display report
        report_container = st.container()
        with report_container:
            st.markdown(st.session_state['generated_report'])
        
        # Export options
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Export as PDF", use_container_width=True):
                # Generate NHS-styled PDF and offer download
                from src.report.exporter import PDFExporter
                exporter = PDFExporter()
                report_text = st.session_state.get('generated_report', '')
                if not report_text:
                    st.warning("No report to export. Please generate a report first.")
                else:
                    patient = st.session_state.get('patient_data', {})
                    labs = st.session_state.get('labs_data', {})
                    # Minimal sources map for exporter (not strictly required)
                    sources = {}
                    pdf_buffer = exporter.export_report(report_text, patient, labs, sources)
                    st.download_button(
                        label="Download PDF",
                        data=pdf_buffer,
                        file_name=f"diabetes_report_{patient.get('name','patient')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
        
        with col2:
            if st.button("💾 Save to Database", use_container_width=True):
                # Persist report locally under .data/
                from src.utils.data_persistence import DataPersistence
                from src.ui.components import create_success_toast, create_error_toast
                report_text = st.session_state.get('generated_report', '')
                if not report_text:
                    create_error_toast("No report to save. Please generate a report first.")
                else:
                    try:
                        dp = DataPersistence()
                        patient = st.session_state.get('patient_data', {})
                        labs = st.session_state.get('labs_data', {})
                        meta = {
                            'patient': patient,
                            'labs': labs,
                            'generated_at': datetime.now().isoformat()
                        }
                        path = dp.save_report(patient.get('name','patient'), report_text, meta)
                        create_success_toast(f"Report saved: {path}")
                    except Exception as e:
                        create_error_toast(f"Save failed: {str(e)}")

def render_management_tab(session_manager, data_persistence):
    """Render Patient Management Tab"""
    
    st.markdown("### 📊 Patient Management Dashboard")
    
    patient_data = st.session_state.get('patient_data', {})
    labs_data = st.session_state.get('labs_data', {})
    
    if not patient_data.get('name'):
        st.info("Please enter patient information in the Patient tab first.")
        return
    
    # Patient header
    st.markdown(f"#### Patient: {patient_data.get('name', 'Unknown')}")
    st.caption(f"NHS Number: {patient_data.get('nhs_number', 'Not provided')}")
    
    # Follow-up checklist
    st.markdown("#### Follow-up Checklist")
    
    checklist_items = [
        {'item': 'HbA1c', 'frequency': '3-6 months', 'due_date': date.today() + timedelta(days=90)},
        {'item': 'Blood Pressure', 'frequency': '3-6 months', 'due_date': date.today() + timedelta(days=90)},
        {'item': 'Lipid Profile', 'frequency': 'Annual', 'due_date': date.today() + timedelta(days=365)},
        {'item': 'UACR', 'frequency': 'Annual', 'due_date': date.today() + timedelta(days=365)},
        {'item': 'Foot Examination', 'frequency': 'Annual', 'due_date': date.today() + timedelta(days=365)},
        {'item': 'Eye Screening', 'frequency': 'Annual', 'due_date': date.today() + timedelta(days=365)}
    ]
    
    for item in checklist_items:
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        
        with col1:
            st.checkbox(item['item'], key=f"check_{item['item'].replace(' ', '_').lower()}")
        
        with col2:
            st.caption(f"Frequency: {item['frequency']}")
        
        with col3:
            due_color = "red" if item['due_date'] < date.today() else "green"
            st.markdown(f"<span style='color: {due_color}'>Due: {item['due_date']}</span>", unsafe_allow_html=True)
        
        with col4:
            if item['due_date'] < date.today():
                st.warning("Overdue")

def generate_report(session_manager, rag_pipeline, report_generator, data_persistence, patient_data, labs_data, lifestyle_data):
    """Generate the diabetes management report"""
    
    from src.ui.components import create_loading_skeleton, create_success_toast, create_error_toast
    
    with st.spinner("Generating personalised report..."):
        try:
            # Show loading skeletons for each section
            placeholder = st.empty()
            
            sections = [
                "Summary of Health Status",
                "Lifestyle Plan", 
                "Diet Plan",
                "Monitoring & Safety",
                "Patient Management & Follow-up"
            ]
            
            for section in sections:
                with placeholder.container():
                    create_loading_skeleton(section)
                    st.write("")  # Small spacing
            
            # Simulate report generation (replace with actual implementation)
            import time
            time.sleep(2)
            
            # Generate sample report (replace with actual report generator)
            report = generate_sample_report(patient_data, labs_data, lifestyle_data)
            
            # Store in session state
            st.session_state['generated_report'] = report
            
            # Clear loading and show success
            placeholder.empty()
            create_success_toast("Report generated successfully!")
            
        except Exception as e:
            create_error_toast(f"Error generating report: {str(e)}")

def generate_sample_report(patient_data, labs_data, lifestyle_data):
    """Generate a sample report for demonstration"""
    
    hba1c = labs_data.get('hba1c', 7.5)
    name = patient_data.get('name', 'Patient')
    
    report = f"""
# Personalised Diabetes Management Report

**Patient:** {name}  
**Date:** {date.today().strftime('%d %B %Y')}  
**Report Generated:** NHS Consultant Style

---

## Summary of Health Status

Your current HbA1c is {hba1c}% indicating {'good' if hba1c < 7 else 'suboptimal'} glycaemic control [S1]. 
Based on NICE NG28 guidelines, your individualised target is <7.0% [S2].

## Lifestyle Plan

The NHS recommends at least 150 minutes of moderate-intensity activity per week [S3].
Start with 10-minute walks after meals and gradually increase duration.

## Diet Plan

Follow the NHS Eatwell plate model with portion control [S4]:
- Fill half your plate with vegetables
- One quarter with wholegrain carbohydrates  
- One quarter with lean protein

### 7-Day Menu Example

| Day | Breakfast | Lunch | Dinner |
|-----|-----------|-------|--------|
| Mon | Porridge with berries | Chicken salad sandwich | Grilled salmon with vegetables |
| Tue | Wholemeal toast with eggs | Lentil soup | Chicken stir-fry |
| Wed | Greek yoghurt with nuts | Tuna wrap | Bean chilli with rice |
| Thu | Overnight oats | Vegetable soup | Grilled chicken with sweet potato |
| Fri | Scrambled eggs on toast | Quinoa salad | Fish curry with cauliflower rice |
| Sat | Smoothie bowl | Chicken wrap | Vegetable lasagne |
| Sun | Full English (grilled) | Roast dinner | Light soup and sandwich |

## Monitoring & Safety

Monitor blood glucose before meals and 2 hours after [S5].
Target ranges:
- Before meals: 4-7 mmol/L
- 2 hours after meals: <8.5 mmol/L

## Patient Management & Follow-up

Schedule HbA1c recheck in 3 months. Annual reviews due for:
- Eye screening
- Foot examination  
- Kidney function (UACR)

## References

[S1] NICE NG28 - Type 2 diabetes in adults: management (2022)  
[S2] NHS - Type 2 diabetes targets  
[S3] NHS - Physical activity guidelines  
[S4] NHS Eatwell Guide  
[S5] Diabetes UK - Blood glucose monitoring
"""
    
    return report
