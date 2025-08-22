"""
Validators for Diabetes Report Generator
Implements validation logic for red flags and data quality
"""

from typing import Dict, List, Any, Optional, Tuple

def validate_red_flags(patient_data: Dict, labs_data: Dict) -> List[str]:
    """
    Check for red flag conditions requiring urgent review
    
    Red flags per specification:
    - FPG ≥ 13.9 mmol/L
    - 2h-PPG ≥ 16.7 mmol/L  
    - HbA1c ≥ 10%
    - BP ≥ 180/110 mmHg
    """
    
    red_flags = []
    
    # Check HbA1c
    hba1c = labs_data.get('hba1c')
    if hba1c and hba1c >= 10.0:
        red_flags.append(f"HbA1c {hba1c}% (≥10% threshold)")
    
    # Check FPG
    fpg = labs_data.get('fpg')
    if fpg and fpg >= 13.9:
        red_flags.append(f"FPG {fpg} mmol/L (≥13.9 mmol/L threshold)")
    
    # Check 2h-PPG
    ppg_2h = labs_data.get('ppg_2h')
    if ppg_2h and ppg_2h >= 16.7:
        red_flags.append(f"2h-PPG {ppg_2h} mmol/L (≥16.7 mmol/L threshold)")
    
    # Check Blood Pressure
    bp_systolic = labs_data.get('bp_systolic')
    bp_diastolic = labs_data.get('bp_diastolic')
    
    if bp_systolic and bp_diastolic:
        if bp_systolic >= 180 or bp_diastolic >= 110:
            red_flags.append(f"BP {bp_systolic}/{bp_diastolic} mmHg (≥180/110 threshold)")
    
    return red_flags

def validate_report_structure(report: str) -> Tuple[bool, List[str]]:
    """
    Validate that generated report has required structure
    
    Required sections:
    1. Summary of Health Status
    2. Lifestyle Plan
    3. Diet Plan (must include 7-day table)
    4. Monitoring & Safety
    5. Patient Management & Follow-up
    6. References
    """
    
    errors = []
    
    required_sections = [
        "Summary of Health Status",
        "Lifestyle Plan",
        "Diet Plan",
        "Monitoring & Safety",
        "Patient Management & Follow-up",
        "References"
    ]
    
    for section in required_sections:
        if section not in report:
            errors.append(f"Missing section: {section}")
    
    # Check for 7-day menu in Diet Plan
    if "Diet Plan" in report:
        diet_section = report.split("Diet Plan")[1].split("##")[0] if "##" in report else report.split("Diet Plan")[1]
        if "Day" not in diet_section or "Breakfast" not in diet_section:
            errors.append("Diet Plan missing 7-day menu table")
    
    # Check for citations
    if "[S" not in report:
        errors.append("No citations found in report")
    
    is_valid = len(errors) == 0
    return is_valid, errors

def validate_citations(report: str, sources: Dict) -> Tuple[bool, List[str]]:
    """
    Validate that all citations in report are valid and present in sources
    """
    
    errors = []
    
    # Extract all citation references from report
    import re
    citations = re.findall(r'\[S(\d+)\]', report)
    
    if not citations:
        errors.append("No citations found in report")
        return False, errors
    
    # Check each citation exists in sources
    for citation_num in citations:
        citation_key = f"S{citation_num}"
        if citation_key not in sources:
            errors.append(f"Invalid citation: [{citation_key}] not in sources")
    
    # Check that each paragraph has at least one citation
    paragraphs = [p for p in report.split('\n\n') if p.strip() and not p.startswith('#')]
    
    for i, paragraph in enumerate(paragraphs[:10], 1):  # Check first 10 paragraphs
        if len(paragraph) > 50 and '[S' not in paragraph:
            # Only flag substantial paragraphs without citations
            if not any(skip in paragraph for skip in ['|', 'Day', 'References', '---']):
                errors.append(f"Paragraph {i} missing citation")
    
    is_valid = len(errors) == 0
    return is_valid, errors

def validate_lab_values(labs_data: Dict) -> Tuple[bool, List[str]]:
    """
    Validate laboratory values are within plausible ranges
    """
    
    warnings = []
    
    # HbA1c range check
    hba1c = labs_data.get('hba1c')
    if hba1c:
        if hba1c < 4.0 or hba1c > 15.0:
            warnings.append(f"HbA1c {hba1c}% outside typical range (4-15%)")
    
    # FPG range check  
    fpg = labs_data.get('fpg')
    if fpg:
        if fpg < 3.0 or fpg > 30.0:
            warnings.append(f"FPG {fpg} mmol/L outside typical range (3-30)")
    
    # BP range check
    bp_sys = labs_data.get('bp_systolic')
    bp_dia = labs_data.get('bp_diastolic')
    
    if bp_sys and bp_dia:
        if bp_sys < 70 or bp_sys > 250:
            warnings.append(f"Systolic BP {bp_sys} outside typical range (70-250)")
        if bp_dia < 40 or bp_dia > 150:
            warnings.append(f"Diastolic BP {bp_dia} outside typical range (40-150)")
        if bp_sys <= bp_dia:
            warnings.append("Systolic BP should be greater than diastolic")
    
    # BMI calculation check
    weight = labs_data.get('weight')
    height = labs_data.get('height')
    
    if weight and height:
        bmi = weight / ((height/100) ** 2)
        if bmi < 15 or bmi > 60:
            warnings.append(f"BMI {bmi:.1f} outside typical range (15-60)")
    
    is_valid = len(warnings) == 0
    return is_valid, warnings

def validate_patient_data(patient_data: Dict) -> Tuple[bool, List[str]]:
    """
    Validate patient demographic data
    """
    
    errors = []
    
    # Check required fields
    if not patient_data.get('name'):
        errors.append("Patient name is required")
    
    if not patient_data.get('dob'):
        errors.append("Date of birth is required")
    
    if not patient_data.get('sex'):
        errors.append("Sex is required")
    
    # Validate NHS number format if provided
    nhs_number = patient_data.get('nhs_number', '').replace(' ', '')
    if nhs_number and len(nhs_number) != 10:
        errors.append("NHS number should be 10 digits")
    
    # Check age is reasonable
    if patient_data.get('dob'):
        from datetime import date, datetime
        try:
            if isinstance(patient_data['dob'], str):
                dob = datetime.strptime(patient_data['dob'], '%Y-%m-%d').date()
            else:
                dob = patient_data['dob']
            
            age = (date.today() - dob).days / 365.25
            
            if age < 18:
                errors.append("Patient under 18 - this tool is for adult Type 2 diabetes")
            elif age > 120:
                errors.append("Please check date of birth")
        except:
            errors.append("Invalid date of birth format")
    
    is_valid = len(errors) == 0
    return is_valid, errors

def validate_pdf_extraction(extracted_data: Dict) -> Tuple[bool, List[str]]:
    """
    Validate PDF extracted data quality
    """
    
    warnings = []
    
    if not extracted_data:
        warnings.append("No data extracted from PDF")
        return False, warnings
    
    # Check for key fields
    key_fields = ['HbA1c', 'FPG', 'BP']
    found_fields = [field for field in key_fields if field in extracted_data]
    
    if len(found_fields) < 2:
        warnings.append(f"Only {len(found_fields)} key fields found in PDF")
    
    # Check for date information
    has_dates = any(
        item.get('date') for item in extracted_data.values()
        if isinstance(item, dict)
    )
    
    if not has_dates:
        warnings.append("No dates found in extracted data - using as most recent")
    
    # Check for units
    for field, data in extracted_data.items():
        if isinstance(data, dict) and not data.get('unit'):
            warnings.append(f"{field}: No unit specified, assuming standard UK units")
    
    is_valid = len(warnings) == 0
    return is_valid, warnings

def validate_activity_minutes(minutes: Optional[int]) -> str:
    """
    Validate activity minutes against NICE guidelines
    """
    
    if not minutes:
        return "No activity data provided"
    
    if minutes >= 150:
        return "Meets NICE recommendation (≥150 min/week)"
    elif minutes >= 75:
        return "Partially meets recommendation (75-149 min/week)"
    else:
        return "Below recommended level (<75 min/week)"

def validate_section_regeneration(
    section_name: str,
    original_report: str,
    regenerated_section: str
) -> Tuple[bool, List[str]]:
    """
    Validate that section regeneration maintains consistency
    """
    
    errors = []
    
    # Check section is not empty
    if not regenerated_section.strip():
        errors.append("Regenerated section is empty")
    
    # Check citations are maintained
    import re
    original_citations = set(re.findall(r'\[S(\d+)\]', original_report))
    new_citations = set(re.findall(r'\[S(\d+)\]', regenerated_section))
    
    # New citations should be subset of original
    invalid_citations = new_citations - original_citations
    if invalid_citations:
        errors.append(f"New invalid citations: {invalid_citations}")
    
    # Check specific requirements per section
    if section_name == "Diet Plan":
        if "Day" not in regenerated_section or "Breakfast" not in regenerated_section:
            errors.append("Diet Plan must include 7-day menu table")
    
    is_valid = len(errors) == 0
    return is_valid, errors
