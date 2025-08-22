<<<<<<< HEAD
# Personalised UK Diabetes Management Report Generator - POC

## 🚀 Deployment

### Prerequisites
- Python 3.10+
- Git
- Streamlit Cloud account
- OpenAI API key

### Local Development
1. Clone the repository
   ```bash
   git clone <your-repo-url>
   cd <repo-name>
   ```
2. Create and activate a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```
3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables
   - Copy `.env.example` to `.env`
   - Add your OpenAI API key

5. Run the application
   ```bash
   streamlit run app.py
   ```

### Streamlit Cloud Deployment
1. Push your code to a GitHub repository
2. Go to [Streamlit Cloud](https://share.streamlit.io/)
3. Click "New app" and select your repository
4. Configure the app:
   - Branch: `main`
   - Main file path: `app.py`
5. Click "Advanced settings" and add your environment variables
6. Click "Deploy!"

---

## Overview
A Streamlit proof-of-concept application that generates fully personalised diabetes management reports for adult Type 2 diabetes patients, styled as a UK consultant would write them. The system adheres strictly to UK clinical guidelines (NICE NG28, NHS, BDA, Diabetes UK).

## Features

### ✅ Core Functionality
- **Patient Data Intake**: Demographics, medical history, medications
- **PDF Processing**: Digital text extraction of lab values with provenance tracking
- **Lab Management**: Comprehensive lab value input with red-flag detection
- **Lifestyle Assessment**: Activity, diet, sleep, stress, and goals tracking
- **Report Generation**: Personalised reports with UK consultant style
- **RAG Pipeline**: Evidence retrieval from UK guidelines with inline citations
- **Safety Features**: Red-flag alerts for critical values requiring urgent review
- **Export Options**: NHS-styled PDF export with at-a-glance summaries

### 🎯 Key Capabilities
- **Red Flag Detection**: Automatic identification of critical values (HbA1c ≥10%, FPG ≥13.9 mmol/L, etc.)
- **Evidence-Based**: All recommendations backed by UK guidelines with citations [S#]
- **Personalisation**: Tailored to individual patient context and goals
- **7-Day Menu Plans**: Structured diet plans following NHS Eatwell Guide
- **Session Management**: Autosave, draft recovery, and data persistence
- **Accessibility**: WCAG AA compliant with NHS design system

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup Instructions

1. **Clone or Download the Repository**
```bash
cd c:\Users\Admin\Downloads\Dibetic_Consultnat_POC
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure Environment Variables**
Create a `.env` file based on `.env.example`:
```bash
copy .env.example .env
```

Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=your-api-key-here
```

4. **Run the Application**
```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

## Usage Guide

### 1. Patient Tab
- Enter patient demographics (name, DOB, sex, NHS number)
- Add diagnoses and current medications
- Upload PDF lab reports (digital text only, no OCR)

### 2. Labs Tab
- Input latest lab values manually or via PDF extraction
- System automatically calculates BMI
- Red flags are highlighted immediately
- All values use UK units (mmol/L, mmHg, etc.)

### 3. Lifestyle Tab
- Record activity levels and weekly exercise minutes
- Document dietary patterns and restrictions
- Set primary health goals
- Note sleep quality and stress levels

### 4. Preview & Generate Tab
- Select temperature (0.3 for consistent, 0.7 for creative)
- Choose sections to include
- Generate personalised report
- Preview with streaming updates
- Export to PDF or save draft

### 5. Management Tab
- View patient overview and red flags
- Access follow-up checklist
- Review encounter history
- Track trends (charts in development)

## Report Structure

Generated reports include:
1. **Summary of Health Status**: Current control, risk factors
2. **Lifestyle Plan**: Personalised activity recommendations
3. **Diet Plan**: 7-day menu following NHS guidelines
4. **Monitoring & Safety**: Testing schedule, targets, sick day rules
5. **Patient Management & Follow-up**: Review schedule, red flags
6. **References**: All cited UK guidelines with URLs

## Red Flag Thresholds

The system monitors for critical values:
- HbA1c ≥ 10%
- FPG ≥ 13.9 mmol/L
- 2h-PPG ≥ 16.7 mmol/L
- BP ≥ 180/110 mmHg

When detected, the system:
- Displays urgent banner at top of screen
- Includes prominent alert in report
- Blocks unsafe medication recommendations
- Advises immediate clinical review

## Technical Architecture

```
src/
├── ui/              # User interface components
│   ├── theme.py     # NHS design system
│   ├── components.py # Reusable UI elements
│   ├── tabs.py      # Patient and Labs tabs
│   └── tabs_extended.py # Other tabs
├── pdf/             # PDF processing
│   └── processor.py # Text extraction logic
├── rag/             # Retrieval pipeline
│   └── retrieval.py # UK guidelines RAG
├── report/          # Report generation
│   ├── generator.py # Report creation logic
│   └── exporter.py  # PDF export
├── utils/           # Utilities
│   ├── session_manager.py # State management
│   └── validators.py # Data validation
└── knowledge/       # Guidelines corpus
```

## Development Status

### ✅ Completed
- Core UI with all 5 tabs
- NHS theme and styling
- Input validation and red flags
- Session state management
- Mock report generation
- PDF upload interface
- Basic RAG structure

### 🚧 In Progress
- GPT-4 integration for report generation
- Full PDF text extraction
- ChromaDB vector storage
- Section regeneration
- Trend charts

### 📋 Planned
- Audit logging
- Multi-language support
- API endpoints
- Batch processing

## Testing

Run the test patient flow:
1. Enter "John Smith", DOB: 01/01/1960, Male
2. Add Type 2 Diabetes diagnosis
3. Enter HbA1c: 8.5%, FPG: 9.2 mmol/L
4. Set activity: Light, Diet: Mediterranean
5. Generate report
6. Verify all sections present with citations

## Safety & Compliance

- **Clinical Disclaimer**: Prominent on all reports
- **Data Protection**: GDPR-aware, minimal PHI storage
- **Audit Trail**: Tracks all retrievals and generations
- **Version Control**: Model versions recorded
- **No OCR**: Prevents misreading of scanned values

## Support

For issues or questions:
- Review the inline help tooltips (ℹ️ icons)
- Check red flag warnings for critical values
- Ensure all required fields are complete
- Verify PDF has extractable text layer

## License

This is a proof-of-concept for demonstration purposes. Not for clinical use without proper validation and regulatory approval.

## Acknowledgments

Built following guidelines from:
- NICE (National Institute for Health and Care Excellence)
- NHS England
- Diabetes UK
- British Dietetic Association

---

**Version**: 1.0.0-POC  
**Last Updated**: December 2024  
**Status**: Proof of Concept - Not for Clinical Use
=======
# Diabetes_Consultant_Helper
>>>>>>> 78bf14acdf76bd2660ded7a7cebdb27237596182
