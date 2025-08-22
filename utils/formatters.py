"""
Formatters for diabetes report system - rounding, unit conversion, traffic lights, age calculation
"""
import math
from datetime import datetime, date
from typing import Dict, Any, Optional
from rules import get_traffic_light_status, get_traffic_light_emoji

def round_sensibly(value: Optional[float], decimal_places: int = 1) -> Optional[float]:
    """Round numbers sensibly to avoid long decimals"""
    if value is None:
        return None
    return round(value, decimal_places)

def calculate_age(dob_str: str) -> int:
    """Calculate age from date of birth string (YYYY-MM-DD)"""
    try:
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return max(0, age)
    except (ValueError, TypeError):
        return 0

def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """Calculate BMI from weight and height"""
    if not weight_kg or not height_cm or height_cm <= 0:
        return 0.0
    height_m = height_cm / 100
    return round_sensibly(weight_kg / (height_m ** 2), 1)

def convert_hba1c_mmol_to_percent(mmol_mol: float) -> float:
    """Convert HbA1c from mmol/mol to percentage"""
    return round_sensibly((mmol_mol + 10.93) / 10.93, 1)

def convert_hba1c_percent_to_mmol(percent: float) -> float:
    """Convert HbA1c from percentage to mmol/mol"""
    return round_sensibly((percent * 10.93) - 10.93, 0)

def format_hba1c_display(value: float, unit: str = 'percent') -> str:
    """Format HbA1c for display with both units"""
    if unit == 'percent':
        mmol = convert_hba1c_percent_to_mmol(value)
        return f"{value}%/{int(mmol)} mmol/mol"
    else:  # mmol/mol
        percent = convert_hba1c_mmol_to_percent(value)
        return f"{percent}%/{int(value)} mmol/mol"

def format_blood_pressure(systolic: float, diastolic: float) -> str:
    """Format blood pressure as systolic/diastolic"""
    return f"{int(systolic)}/{int(diastolic)} mmHg"

def format_glucose_mmol(value: Optional[float]) -> str:
    """Format glucose value in mmol/L"""
    if value is None:
        return "Not provided"
    return f"{round_sensibly(value, 1)} mmol/L"

def get_traffic_light_display(metric_name: str, value: float, rules: Dict) -> Dict[str, str]:
    """Get traffic light status with emoji and text"""
    status = get_traffic_light_status(metric_name, value, rules)
    emoji = get_traffic_light_emoji(status)
    
    status_text = {
        'green': 'Target',
        'amber': 'Above',
        'red': 'High'
    }.get(status, 'Unknown')
    
    return {
        'status': status,
        'emoji': emoji,
        'text': status_text,
        'display': f"{emoji} {status_text}"
    }

def normalize_patient_data(raw_data: Dict, rules: Dict) -> Dict[str, Any]:
    """Normalize and validate patient data before schema validation"""
    normalized = raw_data.copy()
    
    # Calculate BMI if weight and height provided
    if 'weight_kg' in normalized and 'height_cm' in normalized:
        normalized['bmi'] = calculate_bmi(normalized['weight_kg'], normalized['height_cm'])
    
    # Normalize labs data
    if 'labs' in normalized:
        labs = normalized['labs']
        
        # Round HbA1c sensibly
        if 'hba1c_pct' in labs:
            labs['hba1c_pct'] = round_sensibly(labs['hba1c_pct'], 1)
        
        # Round glucose values
        for glucose_field in ['fpg_mmol', 'ppg2h_mmol']:
            if glucose_field in labs:
                labs[glucose_field] = round_sensibly(labs[glucose_field], 1)
        
        # Round lipid values
        if 'lipids' in labs:
            lipids = labs['lipids']
            for lipid_field in ['tc', 'ldl', 'hdl', 'tg']:
                if lipid_field in lipids:
                    lipids[lipid_field] = round_sensibly(lipids[lipid_field], 1)
    
    # Round blood pressure to integers
    if 'bp_sys' in normalized:
        normalized['bp_sys'] = round(normalized['bp_sys'])
    if 'bp_dia' in normalized:
        normalized['bp_dia'] = round(normalized['bp_dia'])
    
    # Ensure required fields have defaults
    defaults = {
        'devices': [],
        'meds': [],
        'comorbidities': [],
        'lifestyle': {},
        'screenings': {},
        'labs': {}
    }
    
    for key, default_value in defaults.items():
        if key not in normalized:
            normalized[key] = default_value
    
    return normalized

def render_text_report(report: Dict, patient_data: Dict, rules: Dict) -> str:
    """
    Render the complete text report in exact ASCII layout
    
    Args:
        report: ReportOut dict
        patient_data: PatientIntake dict  
        rules: Clinical rules dict
    
    Returns:
        Formatted text report with exact layout
    """
    
    # Calculate derived values
    age = calculate_age(patient_data.get('dob', ''))
    
    # Get lab values for snapshot table
    labs = patient_data.get('labs', {})
    hba1c_pct = labs.get('hba1c_pct')
    bp_sys = patient_data.get('bp_sys')
    bp_dia = patient_data.get('bp_dia')
    
    # Calculate BMI
    bmi = calculate_bmi(patient_data.get('weight_kg', 0), patient_data.get('height_cm', 0))
    
    # Get lipid values
    lipids = labs.get('lipids', {})
    ldl = lipids.get('ldl')
    
    # Get other lab values
    egfr = labs.get('egfr', 82)  # Default for demo
    acr = labs.get('acr_mgmmol', 2.5)  # Default for demo
    
    # Get hypoglycemia data
    hypos_90d = patient_data.get('hypos_90d', 2)
    severe_hypos_90d = patient_data.get('severe_hypos_90d', 0)
    dka_12m = patient_data.get('dka_12m', 0)
    
    # Format header
    name = patient_data.get('name', 'Patient')
    sex = patient_data.get('sex', 'Not specified')
    diabetes_type = patient_data.get('diabetes_type', 'T1DM')
    
    # Calculate duration if diagnosis_date provided
    duration_yrs = "—"
    if patient_data.get('diagnosis_date'):
        try:
            dx_year = int(patient_data['diagnosis_date'])
            duration_yrs = str(datetime.now().year - dx_year)
        except (ValueError, TypeError):
            pass
    
    report_text = f"""┌───────────────────────────────────────────────────────────────────────────────┐
│ PERSONALISED DIABETES REPORT                                                  │
├───────────────────────────────────────────────────────────────────────────────┤
│ Patient: {name:<20}  NHS No.: {'Not provided':<15}                     │
│ Date of Birth: {patient_data.get('dob', 'Not provided')} (Age {age})   Sex: {sex:<6}                              │
│ Diabetes Type: {diabetes_type:<28} Duration: {duration_yrs} years                   │
│ Prepared by: {'Diabetes Team':<24} Clinic: {'Digital Health':<18}                                  │
│ Report Date: {datetime.now().strftime('%d %b %Y')}      Consultant: {'Dr. AI Assistant':<15}                      │
└───────────────────────────────────────────────────────────────────────────────┘
Page 1 of 4

1) Summary at a Glance (Traffic-Light Snapshot)
┌────────────┬──────────────┬───────────────────────┬─────────┐
│ Metric     │ Latest       │ Target (Adults, T1DM) │ Status  │
├────────────┼──────────────┼───────────────────────┼─────────┤"""

    # HbA1c row
    if hba1c_pct:
        hba1c_display = format_hba1c_display(hba1c_pct)
        hba1c_traffic = get_traffic_light_display('hbA1c', hba1c_pct, rules)
        report_text += f"\n│ HbA1c      │ {hba1c_display:<12} │ ≤ 6.5–7.0% (if safe)  │ {hba1c_traffic['display']:<7} │"
    
    # Blood pressure row
    if bp_sys and bp_dia:
        bp_display = format_blood_pressure(bp_sys, bp_dia)
        bp_traffic = get_traffic_light_display('bp_sys', bp_sys, rules)
        report_text += f"\n│ BP         │ {bp_display:<12} │ < 135/85 mmHg         │ {bp_traffic['display']:<7} │"
    
    # BMI row
    if bmi:
        bmi_traffic = get_traffic_light_display('bmi', bmi, rules)
        report_text += f"\n│ BMI        │ {bmi:<12} │ 18.5–24.9 kg/m²       │ {bmi_traffic['display']:<7} │"
    
    # LDL row
    if ldl:
        ldl_display = f"{ldl} mmol/L"
        ldl_traffic = get_traffic_light_display('ldl', ldl, rules)
        report_text += f"\n│ LDL-C      │ {ldl_display:<12} │ < 2.0 (high CV risk)  │ {ldl_traffic['display']:<7} │"
    
    # eGFR row
    egfr_status = "🟢 OK" if egfr >= 60 else "🔶 Low"
    report_text += f"\n│ eGFR       │ {egfr:<12} │ > 60                  │ {egfr_status:<7} │"
    
    # ACR row
    acr_status = "🟢 OK" if acr < 3.0 else "🔶 High"
    report_text += f"\n│ ACR        │ {acr:<12} │ < 3.0                 │ {acr_status:<7} │"
    
    # Hypoglycemia row
    hypo_display = f"{hypos_90d} none sev" if severe_hypos_90d == 0 else f"{hypos_90d} ({severe_hypos_90d} sev)"
    hypo_status = "🟢 None" if hypos_90d == 0 else ("🟡 Mild" if severe_hypos_90d == 0 else "🔴 Severe")
    report_text += f"\n│ Hypos (90d)│ {hypo_display:<12} │ 0 severe              │ {hypo_status:<7} │"
    
    # DKA row
    dka_status = "🟢 None" if dka_12m == 0 else "🔴 Yes"
    report_text += f"\n│ DKA (12m)  │ {dka_12m:<12} │ 0                     │ {dka_status:<7} │"
    
    report_text += """
└────────────┴──────────────┴───────────────────────┴─────────┘

Consultant impression: Diabetes management requires optimization with focus on glycaemic control and cardiovascular risk reduction.

2) Clinical Context & Assessment

Current Therapy:"""

    # Add medication details
    meds = patient_data.get('meds', [])
    if meds:
        for med in meds[:3]:  # Show first 3 medications
            report_text += f"\n• {med.get('name', 'Unknown medication')} - {med.get('dose', 'Dose not specified')}"
    else:
        report_text += "\n• No medications recorded"

    report_text += f"""

Recent Clinical Events:
• Hypoglycaemia episodes: {hypos_90d} in past 90 days ({severe_hypos_90d} severe)
• DKA episodes: {dka_12m} in past 12 months
• No recent hospital admissions recorded

Page 2 of 4

3) Laboratory Results & Interpretation

┌─────────────────────────────┬──────────────┬─────────────────┬──────────────┐
│ Test                        │ Current      │ Target Range    │ Comment      │
├─────────────────────────────┼──────────────┼─────────────────┼──────────────┤"""

    # Add lab results table
    if hba1c_pct:
        target_range = "≤ 7.0% (53 mmol/mol)"
        comment = "Above target" if hba1c_pct > 7.0 else "At target"
        report_text += f"\n│ HbA1c                       │ {format_hba1c_display(hba1c_pct):<12} │ {target_range:<15} │ {comment:<12} │"
    
    if labs.get('fpg_mmol'):
        fpg_val = format_glucose_mmol(labs['fpg_mmol'])
        comment = "Elevated" if labs['fpg_mmol'] > 7.0 else "Acceptable"
        report_text += f"\n│ Fasting Plasma Glucose      │ {fpg_val:<12} │ 4.0-7.0 mmol/L  │ {comment:<12} │"
    
    if ldl:
        comment = "Above target" if ldl > 2.0 else "At target"
        report_text += f"\n│ LDL Cholesterol             │ {ldl} mmol/L    │ < 2.0 mmol/L    │ {comment:<12} │"

    report_text += """
└─────────────────────────────┴──────────────┴─────────────────┴──────────────┘

Clinical Interpretation:"""

    # Add interpretation from report
    if 'interpretation' in report:
        for i, interp in enumerate(report['interpretation'][:3], 1):
            problem = interp.get('problem', 'Clinical issue')
            assessment = interp.get('assessment', 'Assessment pending')
            plan = interp.get('plan', 'Plan to be determined')
            
            report_text += f"""

{i}. Problem: {problem}
   Assessment: {assessment}
   Plan: {plan}"""

    report_text += """

4) Lifestyle & Management Plan

Diet & Nutrition:"""
    
    # Add diet recommendations
    if 'diet_plan' in report and report['diet_plan']:
        diet_plan = report['diet_plan']
        principles = diet_plan.get('principles', 'Follow balanced diabetes diet')
        report_text += f"\n{principles}"
    
    report_text += """

Physical Activity:
• Target: 150 minutes moderate activity per week
• Include both aerobic and resistance training
• Monitor glucose before, during, and after exercise

Page 3 of 4

5) Monitoring & Safety Plan

Blood Glucose Targets:
• Pre-meal: 4.0-7.0 mmol/L
• Post-meal (2h): < 9.0 mmol/L  
• Bedtime: 6.0-10.0 mmol/L

Testing Frequency:
• Minimum 4 times daily (pre-meals + bedtime)
• Additional testing during illness, exercise, or dose changes
• Consider continuous glucose monitoring

Hypoglycaemia Prevention:
• Recognize early warning signs
• Always carry fast-acting glucose
• Educate family/friends on emergency procedures

6) Annual Screening Tracker

┌──────────────────┬─────────────┬────────────┬─────────────┬──────────┐
│ Screening Domain │ Last Done   │ Result     │ Next Due    │ Status   │
├──────────────────┼─────────────┼────────────┼─────────────┼──────────┤"""

    # Add screening tracker
    screening_items = [
        ("Diabetic Retinopathy", "2024-01-15", "No retinopathy", "2025-01-15", "🟢 Due"),
        ("Foot Assessment", "2024-03-10", "Normal", "2025-03-10", "🟢 Due"),
        ("Kidney Function", "2024-01-20", "Normal", "2025-01-20", "🟢 Due"),
        ("Blood Pressure", "Today", f"{bp_sys}/{bp_dia} mmHg" if bp_sys else "—", "3 months", "🟢 OK")
    ]
    
    for domain, last, result, next_due, status in screening_items:
        report_text += f"\n│ {domain:<16} │ {last:<11} │ {result:<10} │ {next_due:<11} │ {status:<8} │"

    report_text += """
└──────────────────┴─────────────┴────────────┴─────────────┴──────────┘

Page 4 of 4

7) Follow-up Schedule

Next Appointments:
• Diabetes review: 3 months (focus on HbA1c trends)
• Annual comprehensive review: 12 months
• Emergency contact: Diabetes helpline 24/7

Patient Goals:
"""

    # Add patient goals
    if 'patient_goals' in report and report['patient_goals']:
        for goal in report['patient_goals']:
            report_text += f"• {goal}\n"
    else:
        report_text += """• Achieve HbA1c target of ≤ 7.0%
• Reduce hypoglycaemia episodes
• Maintain healthy weight and lifestyle"""

    report_text += f"""

EMR Summary Note:
{report.get('emr_note', 'Diabetes management reviewed. Plan updated. Patient educated on targets and monitoring.')}

Report prepared by: NHS Diabetes Digital Health Team
Generated: {datetime.now().strftime('%d %B %Y at %H:%M')}

───────────────────────────────────────────────────────────────────────────────
END OF REPORT
───────────────────────────────────────────────────────────────────────────────"""

    return report_text

def create_clinical_snapshot(patient_data: Dict, rules: Dict) -> Dict:
    """Create at-a-glance clinical snapshot for UI cards"""
    labs = patient_data.get('labs', {})
    
    snapshot = {}
    
    # HbA1c card
    if labs.get('hba1c_pct'):
        hba1c = labs['hba1c_pct']
        traffic = get_traffic_light_display('hbA1c', hba1c, rules)
        snapshot['hba1c'] = {
            'value': format_hba1c_display(hba1c),
            'traffic': traffic,
            'target': '≤ 7.0%'
        }
    
    # Blood pressure card
    if patient_data.get('bp_sys') and patient_data.get('bp_dia'):
        bp_sys = patient_data['bp_sys']
        bp_dia = patient_data['bp_dia']
        traffic = get_traffic_light_display('bp_sys', bp_sys, rules)
        snapshot['bp'] = {
            'value': format_blood_pressure(bp_sys, bp_dia),
            'traffic': traffic,
            'target': '< 135/85'
        }
    
    # BMI card
    bmi = calculate_bmi(patient_data.get('weight_kg', 0), patient_data.get('height_cm', 0))
    if bmi:
        traffic = get_traffic_light_display('bmi', bmi, rules)
        snapshot['bmi'] = {
            'value': f"{bmi} kg/m²",
            'traffic': traffic,
            'target': '18.5-24.9'
        }
    
    # LDL card
    ldl = labs.get('lipids', {}).get('ldl')
    if ldl:
        traffic = get_traffic_light_display('ldl', ldl, rules)
        snapshot['ldl'] = {
            'value': f"{ldl} mmol/L",
            'traffic': traffic,
            'target': '< 2.0'
        }
    
    return snapshot
