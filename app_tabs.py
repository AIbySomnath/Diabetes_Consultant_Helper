"""
Tabbed NHS-Style Diabetes Report Generator (preserved)
"""
import streamlit as st
from dotenv import load_dotenv
from datetime import date

# Import custom modules
from src.ui.theme import apply_nhs_theme
from src.ui.components import create_at_glance_bar, create_urgent_banner
from src.ui.tabs import (
    render_patient_tab,
    render_labs_tab
)
from src.ui.tabs_extended import (
    render_lifestyle_tab,
    render_preview_generate_tab,
    render_management_tab
)
from src.utils.session_manager import SessionManager
from src.utils.validators import validate_red_flags
from src.pdf.processor import PDFProcessor
from src.rag.retrieval import RAGPipeline
from src.report.generator import ReportGenerator
from src.utils.data_persistence import DataPersistence

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Diabetes Management Report - NHS Style",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply NHS theme
apply_nhs_theme()

# Initialize session manager
session_manager = SessionManager()

# Initialize components
@st.cache_resource
def init_components():
    """Initialize expensive components once"""
    pdf_processor = PDFProcessor()
    rag_pipeline = RAGPipeline()
    report_generator = ReportGenerator()
    data_persistence = DataPersistence()
    return pdf_processor, rag_pipeline, report_generator, data_persistence

pdf_processor, rag_pipeline, report_generator, data_persistence = init_components()

# Main app title
st.markdown(
    """
<div style="text-align: center; padding: 1rem 0;">
    <h1 style="color: #005EB8; font-weight: 600;">
        🏥 Diabetes Management Report Generator
    </h1>
    <p style="color: #425563; font-size: 1.1rem;">
        UK Consultant-Style Personalised Reports • NICE NG28 Compliant
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# Clinical disclaimer
with st.expander("⚠️ Important Clinical Disclaimer", expanded=False):
    st.warning(
        """
    **For Healthcare Professional Use Only**
    
    This tool generates reports based on UK clinical guidelines (NICE NG28, NHS, BDA, Diabetes UK).
    All recommendations require clinical review before implementation.
    
    • Reports are for adult Type 2 diabetes only
    • All medication changes must be reviewed by a qualified clinician
    • Red flag values trigger urgent review recommendations
    • This is a proof of concept (POC) system
    """
    )

# Check for red flags and display urgent banner if needed
patient_data = st.session_state.get("patient_data", {})
labs_data = st.session_state.get("labs_data", {})
red_flags = validate_red_flags(patient_data, labs_data)

if red_flags:
    create_urgent_banner(red_flags)

# At-a-glance sticky bar
if labs_data:
    create_at_glance_bar(labs_data)

# Main tabs
(
    tab_patient,
    tab_labs,
    tab_lifestyle,
    tab_preview,
    tab_management,
) = st.tabs([
    "👤 Patient",
    "🔬 Labs",
    "🏃 Lifestyle",
    "📄 Preview & Generate",
    "📊 Management",
])

# Render each tab
with tab_patient:
    render_patient_tab(session_manager, pdf_processor)

with tab_labs:
    render_labs_tab(session_manager)

with tab_lifestyle:
    render_lifestyle_tab(session_manager)

with tab_preview:
    render_preview_generate_tab(
        session_manager, rag_pipeline, report_generator, data_persistence
    )

with tab_management:
    render_management_tab(session_manager, data_persistence)

# Footer
st.markdown("---")
st.markdown(
    """
<div style="text-align: center; color: #768692; font-size: 0.9rem;">
    <p>POC Version 1.0 | Built with NHS Guidelines | © 2024</p>
    <p>Data stored locally only • GDPR Compliant • Audit Trail Enabled</p>
</div>
""",
    unsafe_allow_html=True,
)

# Autosave functionality
if st.session_state.get("autosave_enabled", True):
    session_manager.autosave()
