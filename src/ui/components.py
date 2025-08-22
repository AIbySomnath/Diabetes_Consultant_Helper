"""
Reusable UI Components for Diabetes Report Generator
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional

def create_at_glance_bar(labs_data: Dict) -> None:
    """Create sticky at-a-glance bar with key metrics"""
    
    # Convert HbA1c to mmol/mol if needed
    hba1c_percent = labs_data.get('hba1c', 0)
    hba1c_mmol = round((hba1c_percent - 2.152) / 0.09148) if hba1c_percent else 0
    
    st.markdown("""
    <div style="position: sticky; top: 0; z-index: 999; background: white; 
                border-bottom: 2px solid #005EB8; padding: 1rem; margin-bottom: 1rem;">
        <style>
            .metric-box {
                display: inline-block;
                margin: 0 1rem;
                padding: 0.5rem 1rem;
                background: #F0F4F5;
                border-radius: 4px;
                border-left: 3px solid #005EB8;
            }
            .metric-label {
                font-size: 12px;
                color: #768692;
                font-weight: 600;
                text-transform: uppercase;
            }
            .metric-value {
                font-size: 20px;
                color: #212B32;
                font-weight: bold;
            }
            .metric-unit {
                font-size: 14px;
                color: #768692;
            }
        </style>
    """, unsafe_allow_html=True)
    
    cols = st.columns(6)
    
    with cols[0]:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">HbA1c</div>
            <div class="metric-value">{labs_data.get('hba1c', '--')}%
                <span class="metric-unit">({hba1c_mmol} mmol/mol)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">FPG</div>
            <div class="metric-value">{labs_data.get('fpg', '--')}
                <span class="metric-unit">mmol/L</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[2]:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">2h-PPG</div>
            <div class="metric-value">{labs_data.get('ppg_2h', '--')}
                <span class="metric-unit">mmol/L</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[3]:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">BP</div>
            <div class="metric-value">{labs_data.get('bp_systolic', '--')}/{labs_data.get('bp_diastolic', '--')}
                <span class="metric-unit">mmHg</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[4]:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">BMI</div>
            <div class="metric-value">{labs_data.get('bmi', '--')}
                <span class="metric-unit">kg/m²</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[5]:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Last Lab</div>
            <div class="metric-value" style="font-size: 16px;">
                {labs_data.get('last_lab_date', '--')}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

def create_urgent_banner(red_flags: List[str]) -> None:
    """Display urgent banner for red flag conditions"""
    
    st.markdown(f"""
    <div role="alert" aria-live="assertive" style="
        background: #DA291C;
        color: white;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-weight: 600;
        box-shadow: 0 4px 6px rgba(218, 41, 28, 0.2);
    ">
        <h3 style="color: white; margin: 0 0 0.5rem 0;">
            ⚠️ URGENT CLINICAL REVIEW REQUIRED
        </h3>
        <p style="color: white; margin: 0.5rem 0;">
            The following red flag values have been detected:
        </p>
        <ul style="margin: 0.5rem 0;">
    """, unsafe_allow_html=True)
    
    for flag in red_flags:
        st.markdown(f"<li style='color: white;'>{flag}</li>", unsafe_allow_html=True)
    
    st.markdown("""
        </ul>
        <p style="color: white; margin: 0.5rem 0 0 0; font-style: italic;">
            Immediate clinical assessment recommended. All medication changes require clinician review.
        </p>
    </div>
    """, unsafe_allow_html=True)

def create_input_with_tooltip(
    label: str,
    key: str,
    input_type: str = "text",
    help_text: str = "",
    placeholder: str = "",
    options: List = None,
    min_value: float = None,
    max_value: float = None,
    step: float = None,
    format_str: str = None,
    unit: str = "",
    tooltip: str = ""
) -> any:
    """Create input field with NHS styling and tooltip"""
    
    # Add tooltip if provided
    if tooltip:
        label_html = f"""
        <div style="position: relative; display: inline-block;">
            <label style="font-weight: 600; color: #212B32;">
                {label}
                <span style="
                    display: inline-block;
                    width: 16px;
                    height: 16px;
                    background: #005EB8;
                    color: white;
                    border-radius: 50%;
                    font-size: 12px;
                    text-align: center;
                    margin-left: 0.5rem;
                    cursor: help;
                " title="{tooltip}">?</span>
            </label>
        </div>
        """
        st.markdown(label_html, unsafe_allow_html=True)
        label = ""  # Clear label as we've already displayed it
    
    # Add unit display if provided
    if unit:
        help_text = f"{unit} • {help_text}" if help_text else unit
    
    # Create appropriate input based on type
    if input_type == "select" and options:
        return st.selectbox(
            label=label,
            options=options,
            key=key,
            help=help_text,
            placeholder=placeholder
        )
    elif input_type == "number":
        return st.number_input(
            label=label,
            key=key,
            min_value=min_value,
            max_value=max_value,
            step=step,
            format=format_str,
            help=help_text
        )
    elif input_type == "date":
        return st.date_input(
            label=label,
            key=key,
            help=help_text
        )
    elif input_type == "multiselect":
        return st.multiselect(
            label=label,
            options=options,
            key=key,
            help=help_text,
            placeholder=placeholder
        )
    elif input_type == "textarea":
        return st.text_area(
            label=label,
            key=key,
            help=help_text,
            placeholder=placeholder
        )
    else:  # Default to text input
        return st.text_input(
            label=label,
            key=key,
            help=help_text,
            placeholder=placeholder
        )

def create_loading_skeleton(section_name: str) -> None:
    """Create loading skeleton for report sections"""
    
    st.markdown(f"""
    <div class="skeleton" style="
        background: linear-gradient(90deg, #F0F4F5 25%, #76869240 50%, #F0F4F5 75%);
        background-size: 200% 100%;
        animation: loading 1.5s infinite;
        padding: 1rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    ">
        <p style="color: #768692;">Generating {section_name}...</p>
        <div style="height: 20px; margin: 0.5rem 0;"></div>
        <div style="height: 20px; margin: 0.5rem 0; width: 80%;"></div>
        <div style="height: 20px; margin: 0.5rem 0; width: 60%;"></div>
    </div>
    """, unsafe_allow_html=True)

def create_citation_chip(citation_id: str, source_info: Dict) -> str:
    """Create expandable citation chip"""
    
    return f"""
    <span class="citation-chip" style="
        display: inline-block;
        background: #41B6E6;
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 12px;
        cursor: pointer;
        margin: 0 2px;
    " title="{source_info.get('title', '')} - {source_info.get('url', '')}">
        [{citation_id}]
    </span>
    """

def create_validation_feedback(
    field_name: str,
    is_valid: bool,
    message: str,
    severity: str = "info"
) -> None:
    """Display validation feedback for form fields"""
    
    colors = {
        "success": "#007F3B",
        "warning": "#FFB81C",
        "error": "#DA291C",
        "info": "#005EB8"
    }
    
    icon = {
        "success": "✓",
        "warning": "⚠",
        "error": "✗",
        "info": "ℹ"
    }
    
    if not is_valid or severity != "info":
        st.markdown(f"""
        <div style="
            background: {colors[severity]}20;
            border-left: 3px solid {colors[severity]};
            padding: 0.5rem;
            margin: 0.5rem 0;
            border-radius: 4px;
        ">
            <span style="color: {colors[severity]}; font-weight: bold;">
                {icon[severity]} {field_name}:
            </span>
            <span style="color: #212B32;">
                {message}
            </span>
        </div>
        """, unsafe_allow_html=True)

def create_progress_indicator(current_step: int, total_steps: int) -> None:
    """Create step progress indicator"""
    
    progress = (current_step / total_steps) * 100
    
    st.markdown(f"""
    <div style="margin: 1rem 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span style="font-weight: 600; color: #212B32;">
                Step {current_step} of {total_steps}
            </span>
            <span style="color: #768692;">
                {int(progress)}% Complete
            </span>
        </div>
        <div style="
            background: #F0F4F5;
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
        ">
            <div style="
                background: #005EB8;
                height: 100%;
                width: {progress}%;
                transition: width 0.3s ease;
            "></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_success_toast(message: str) -> None:
    """Display success toast notification"""
    
    st.success(message, icon="✅")

def create_error_toast(message: str, action_text: str = None) -> None:
    """Display error toast with optional action"""
    
    error_html = f"""
    <div style="
        background: #DA291C20;
        border-left: 4px solid #DA291C;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    ">
        <strong style="color: #DA291C;">Error:</strong>
        <span style="color: #212B32;">{message}</span>
    """
    
    if action_text:
        error_html += f"""
        <div style="margin-top: 0.5rem;">
            <em style="color: #768692;">{action_text}</em>
        </div>
        """
    
    error_html += "</div>"
    st.markdown(error_html, unsafe_allow_html=True)
