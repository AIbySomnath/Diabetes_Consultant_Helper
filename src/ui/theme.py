"""
NHS Theme Configuration for Streamlit
Implements NHS design system colours and styling
"""

import streamlit as st

def apply_nhs_theme():
    """Apply NHS design system theme to Streamlit app"""
    
    # NHS Colour Palette
    nhs_colors = {
        'primary': '#005EB8',      # NHS Blue
        'secondary': '#41B6E6',    # Light Blue
        'success': '#007F3B',      # Green
        'warning': '#FFB81C',      # Yellow
        'danger': '#DA291C',       # Emergency Red
        'text': '#212B32',         # Dark Grey
        'muted': '#768692',        # Mid Grey
        'background': '#FFFFFF',   # White
        'light_grey': '#F0F4F5',   # Light Grey Background
    }
    
    # Custom CSS
    st.markdown(f"""
    <style>
        /* Main app styling */
        .stApp {{
            background-color: {nhs_colors['background']};
            font-family: 'Frutiger', 'Arial', sans-serif;
        }}
        
        /* Headers */
        h1, h2, h3, h4, h5, h6 {{
            color: {nhs_colors['primary']};
            font-weight: 600;
        }}
        
        /* Body text */
        p, li, span {{
            color: {nhs_colors['text']};
            font-size: 16px;
            line-height: 1.5;
        }}
        
        /* Buttons */
        .stButton > button {{
            background-color: {nhs_colors['primary']};
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            font-size: 16px;
            font-weight: 600;
            border-radius: 4px;
            transition: all 0.3s;
        }}
        
        .stButton > button:hover {{
            background-color: #003E74;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        
        /* Primary button styling */
        .primary-button > button {{
            background-color: {nhs_colors['success']};
            font-size: 18px;
            padding: 0.75rem 1.5rem;
        }}
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
            background-color: {nhs_colors['light_grey']};
            padding: 0.5rem;
            border-radius: 8px;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            height: 50px;
            padding: 0 24px;
            background-color: white;
            border-radius: 4px;
            color: {nhs_colors['text']};
            font-weight: 500;
            font-size: 16px;
        }}
        
        .stTabs [aria-selected="true"] {{
            background-color: {nhs_colors['primary']};
            color: white;
        }}
        
        /* Input fields */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > select {{
            border: 2px solid {nhs_colors['muted']};
            border-radius: 4px;
            padding: 0.5rem;
            font-size: 16px;
        }}
        
        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus,
        .stSelectbox > div > div > select:focus {{
            border-color: {nhs_colors['primary']};
            outline: 3px solid {nhs_colors['secondary']}40;
        }}
        
        /* Labels */
        .stTextInput > label,
        .stNumberInput > label,
        .stSelectbox > label,
        .stDateInput > label {{
            color: {nhs_colors['text']};
            font-weight: 600;
            font-size: 16px;
            margin-bottom: 0.25rem;
        }}
        
        /* Help text */
        .stTextInput > div > small,
        .stNumberInput > div > small {{
            color: {nhs_colors['muted']};
            font-size: 14px;
            margin-top: 0.25rem;
        }}
        
        /* Alerts and warnings */
        .stAlert {{
            border-radius: 4px;
            border-left: 4px solid;
            padding: 1rem;
        }}
        
        div[data-testid="stWarning"] {{
            background-color: {nhs_colors['warning']}20;
            border-left-color: {nhs_colors['warning']};
        }}
        
        div[data-testid="stError"] {{
            background-color: {nhs_colors['danger']}20;
            border-left-color: {nhs_colors['danger']};
        }}
        
        div[data-testid="stSuccess"] {{
            background-color: {nhs_colors['success']}20;
            border-left-color: {nhs_colors['success']};
        }}
        
        /* Expander */
        .streamlit-expanderHeader {{
            background-color: {nhs_colors['light_grey']};
            border-radius: 4px;
            font-weight: 600;
            font-size: 16px;
        }}
        
        /* Metrics */
        [data-testid="metric-container"] {{
            background-color: {nhs_colors['light_grey']};
            padding: 1rem;
            border-radius: 4px;
            border-left: 4px solid {nhs_colors['primary']};
        }}
        
        /* File uploader */
        .stFileUploader {{
            background-color: {nhs_colors['light_grey']};
            border: 2px dashed {nhs_colors['muted']};
            border-radius: 8px;
            padding: 2rem;
        }}
        
        .stFileUploader:hover {{
            border-color: {nhs_colors['primary']};
            background-color: {nhs_colors['secondary']}10;
        }}
        
        /* Tooltips */
        .tooltip {{
            background-color: {nhs_colors['text']};
            color: white;
            padding: 0.5rem;
            border-radius: 4px;
            font-size: 14px;
        }}
        
        /* Loading skeleton */
        .skeleton {{
            background: linear-gradient(90deg, 
                {nhs_colors['light_grey']} 25%, 
                {nhs_colors['muted']}20 50%, 
                {nhs_colors['light_grey']} 75%);
            background-size: 200% 100%;
            animation: loading 1.5s infinite;
        }}
        
        @keyframes loading {{
            0% {{ background-position: 200% 0; }}
            100% {{ background-position: -200% 0; }}
        }}
        
        /* Accessibility focus indicators */
        *:focus {{
            outline: 3px solid {nhs_colors['secondary']};
            outline-offset: 2px;
        }}
        
        /* High contrast mode support */
        @media (prefers-contrast: high) {{
            * {{
                border-width: 2px !important;
            }}
        }}
        
        /* Print styles */
        @media print {{
            .stTabs, .stButton, .stFileUploader {{
                display: none;
            }}
            body {{
                font-size: 12pt;
            }}
        }}
    </style>
    """, unsafe_allow_html=True)
