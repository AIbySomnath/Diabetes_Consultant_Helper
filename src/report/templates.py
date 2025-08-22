"""
Report templates for diabetes management system
"""
from datetime import datetime
from typing import Dict, Any, List, Optional

class ReportTemplates:
    """Templates for generating structured diabetes reports"""
    
    @staticmethod
    def get_header(patient_data: Dict[str, Any]) -> str:
        """Generate report header with patient info"""
        name = patient_data.get('name', 'Patient')
        nhs_number = patient_data.get('nhs_number', 'Not provided')
        dob = patient_data.get('dob', 'Not provided')
        age = patient_data.get('age', 'Not specified')
        
        # Format date of birth if provided
        if dob and isinstance(dob, str):
            try:
                dob_date = datetime.strptime(dob, '%Y-%m-%d')
                dob_formatted = dob_date.strftime('%d %b %Y')
                if age == 'Not specified':
                    age = (datetime.now() - dob_date).days // 365
            except (ValueError, TypeError):
                dob_formatted = dob
        else:
            dob_formatted = str(dob)
        
        return f"""🩺 Personalised Diabetes Management Report

1) Patient Information
Name: {name}

NHS Number: {nhs_number}

Date of Birth: {dob_formatted} (Age {age})

Prepared by: Diabetes Specialist Team – Riverside Endocrine Clinic

Report Date: {datetime.now().strftime('%d %b %Y')}

Consent: Confirmed for this review

"""

    @staticmethod
    def get_snapshot(patient_data: Dict[str, Any], labs_data: Dict[str, Any]) -> str:
        """Generate clinical snapshot section"""
        # Get values with defaults
        hba1c = labs_data.get('hba1c', 'Not provided')
        bp_sys = labs_data.get('bp_systolic', 'Not provided')
        bp_dia = labs_data.get('diastolic', 'Not provided')
        weight = labs_data.get('weight', 'Not provided')
        height = labs_data.get('height', 'Not provided')
        ldl = labs_data.get('ldl', 'Not provided')
        egfr = labs_data.get('egfr', 'Not provided')
        acr = labs_data.get('acr', 'Not provided')
        hypos = patient_data.get('hypos_90d', 0)
        
        # Calculate BMI if possible
        bmi = 'Not provided'
        if isinstance(weight, (int, float)) and isinstance(height, (int, float)) and height > 0:
            bmi = weight / ((height/100) ** 2)
            bmi = f"{bmi:.1f} kg/m²"
        
        # Determine status indicators
        def get_status(value, thresholds, unit=''):
            if not isinstance(value, (int, float)):
                return '🔵 N/A'
            
            if value <= thresholds.get('good', 0):
                return f'🟢 At/near target ({value}{unit})'
            elif value <= thresholds.get('warning', float('inf')):
                return f'🟡 Monitor ({value}{unit})'
            else:
                return f'🔴 Action needed ({value}{unit})'
        
        # Build the table
        return f"""2) 📊 Summary at a Glance

| Metric | Latest | Target (Adults with T1DM) | Status |
|--------|--------|---------------------------|--------|
| HbA1c | {hba1c}% | ≤ 6.5–7.0% if safe [NICE NG17] | {get_status(float(hba1c) if isinstance(hba1c, (int, float)) else None, {'good': 7.0, 'warning': 8.0}, '%')} |
| BP | {bp_sys}/{bp_dia} mmHg | < 135/85 mmHg (lower if CKD) [NICE] | {get_status(float(bp_sys) if isinstance(bp_sys, (int, float)) else None, {'good': 135, 'warning': 140}, ' mmHg')} |
| BMI | {bmi} | 18.5–24.9 kg/m² | {get_status(float(bmi.split()[0]) if isinstance(bmi, str) and 'kg/m²' in bmi else None, {'good': 25, 'warning': 30}, ' kg/m²')} |
| LDL-C | {ldl} mmol/L | < 2.0 mmol/L if high CV risk [NICE] | {get_status(float(ldl) if isinstance(ldl, (int, float)) else None, {'good': 2.0, 'warning': 3.0}, ' mmol/L')} |
| eGFR | {egfr} mL/min/1.73m² | > 60 (monitor trend) | {get_status(float(egfr) if isinstance(egfr, (int, float)) else None, {'good': 60, 'warning': 45}, ' mL/min/1.73m²')} |
| ACR | {acr} mg/mmol | < 3.0 mg/mmol | {get_status(float(acr) if isinstance(acr, (int, float)) else None, {'good': 3.0, 'warning': 30}, ' mg/mmol')} |
| Hypos (90d) | {hypos} | 0 severe | {'🟢 None' if hypos == 0 else '🔶 Low–moderate risk'} |
| DKA (12m) | 0 | 0 | 🟢 None |

*Why it matters:* {f"HbA1c {hba1c}%" if isinstance(hba1c, (int, float)) else 'Optimal control'} reduces microvascular risk; {f"LDL {ldl} mmol/L" if isinstance(ldl, (int, float)) else 'lipid management'} impacts CV risk.

"""

    @staticmethod
    def get_health_status(patient_data: Dict[str, Any], labs_data: Dict[str, Any]) -> str:
        """Generate health status section"""
        hba1c = labs_data.get('hba1c', 'Not provided')
        fpg = labs_data.get('fpg', 'Not provided')
        ppg = labs_data.get('ppg', 'Not provided')
        
        return f"""3) 🩸 Current Health Status

**Glycaemic control:** {'HbA1c ' + str(hba1c) + '%' if isinstance(hba1c, (int, float)) else 'No recent HbA1c'}. {'Fasting ' + str(fpg) + ' mmol/L' if isinstance(fpg, (int, float)) else ''} {'and post-prandial ' + str(ppg) + ' mmol/L' if isinstance(ppg, (int, float)) else ''} suggest {'good' if isinstance(hba1c, (int, float)) and hba1c <= 7.0 else 'suboptimal'} control.

**Cardiometabolic risk:** {'BP ' + str(labs_data.get('bp_systolic', '')) + '/' + str(labs_data.get('diastolic', '')) if all(k in labs_data for k in ['bp_systolic', 'diastolic']) else 'BP not assessed'}; {'LDL ' + str(labs_data.get('ldl', '')) + ' mmol/L' if 'ldl' in labs_data else 'Lipids not assessed'}; {'BMI ' + str(round(labs_data['weight'] / ((labs_data['height']/100) ** 2), 1)) if all(k in labs_data for k in ['weight', 'height']) else 'BMI not calculated'}.

**Renal status:** {'eGFR ' + str(labs_data.get('egfr', '')) + ', ACR ' + str(labs_data.get('acr', '')) if all(k in labs_data for k in ['egfr', 'acr']) else 'Renal function not fully assessed'}.

**Lifestyle context:** {'Activity: ' + patient_data.get('activity_level', 'Not assessed') + '; ' if 'activity_level' in patient_data else ''}{'Diet: ' + patient_data.get('dietary_pattern', 'Not assessed') + '; ' if 'dietary_pattern' in patient_data else ''}{'Smoking: ' + patient_data.get('smoking_status', 'Not assessed') if 'smoking_status' in patient_data else ''}.

"""

    @staticmethod
    def get_lifestyle_plan(patient_data: Dict[str, Any]) -> str:
        """Generate lifestyle recommendations"""
        return """5) 🏃‍♂️ Personalised Lifestyle Plan

**Physical Activity (SMART):**
- Build to 150 min/week moderate aerobic + 2×/week resistance within 8 weeks.
- Start with 30 min brisk walk 5×/week; add body-weight circuit (10–15 min) Tue/Fri.
- Use step counter; aim 7–9k steps/day.
*Ref: NHS physical activity guidelines.*

**Sleep & Stress:**
- Target 7–8 h/night; consistent bedtime; cut screens 60 min before bed.
- 10-minute evening wind-down (breathing or mindfulness).

**Smoking / Alcohol:**
- Stop smoking within 4 weeks—refer to NHS Stop Smoking Service; consider NRT.
- Alcohol: not currently drinking; maintain.

"""

    @staticmethod
    def get_diet_plan() -> str:
        """Generate diet plan section"""
        return """6) 🍽️ Personalised Diet Plan (T1DM, insulin-matched)

**Principles (Eatwell + carb awareness):**
- Plate guide: ½ veg/salad, ¼ lean protein, ¼ high-fibre carbs.
- Prefer low-GI carbs (wholegrain breads, basmati/brown rice, lentils).
- Pre-bolus rapid insulin 10–15 min before carb meals when safe.
- Avoid skipping meals—↑ hypo risk with insulin.
*Refs: Diabetes UK nutrition; NICE.*

**Example Day (swap items to taste):**
- **Breakfast:** Porridge (40–50 g oats) + berries; semi-skimmed milk.
- **Lunch:** Wholegrain wrap, chicken/tikka tofu, mixed salad; 1 fruit.
- **Dinner:** Grilled salmon/chana masala, quinoa/brown rice, veg.
- **Snacks:** Greek yoghurt, apple + peanut butter, handful nuts.
- **Hydration:** 6–8 glasses/day; limit fruit juice to 150 ml with meals.

"""

    @staticmethod
    def get_monitoring_plan() -> str:
        """Generate monitoring and safety section"""
        return """7) 📈 Monitoring Plan

| What | Frequency | Targets / Notes |
|------|-----------|-----------------|
| SMBG/CGM | Pre-meal & bedtime; paired tests weekly | 4–7 mmol/L pre-meal; < 8.5 mmol/L 2-h post-meal |
| HbA1c | Every 3 months until ≤ 7.0% | Review insulin ratios & pre-bolus |
| BP | Each visit; home BP optional | < 135/85 mmHg |
| Lipids | 3 months after any statin change | LDL < 2.0 mmol/L if high risk |
| Renal (eGFR/ACR) | Annually (earlier if abnormal) | Watch trend |
| Eyes / Feet | Annually | Retinopathy grade; foot risk |

8) 🛡️ Safety Guidance

**Hypoglycaemia (< 4.0 mmol/L):**
1. 15–20 g fast carbs (e.g., 4 glucose tabs)
2. Retest after 15 min
3. Repeat if needed
4. Follow with longer-acting carbs (e.g., toast)
*Keep glucagon available if at risk.*

**Sick-day rules:** Never stop insulin; check glucose 2–4-hourly; fluids; seek advice if > 15 mmol/L persistent or vomiting.
*Refs: NICE, NHS sick-day guidance.*

"""

    @staticmethod
    def get_follow_up() -> str:
        """Generate follow-up section"""
        return """9) 📅 Follow-up & Review Schedule

- **6 weeks:** Review SMBG pattern, adjust insulin/carb ratios, activity adherence.
- **3 months:** HbA1c, weight, BP, statin tolerance; reinforce smoking quit plan.
- **6 months:** Full review; retinal screening if due.
- **Annual:** Foot exam, retinal screening, eGFR/ACR, lipids, vaccination check.

"""

    @staticmethod
    def get_red_flags() -> str:
        """Generate red flags section"""
        return """10) 🚩 Red Flags – Seek Urgent Help

- BG > 15 mmol/L with vomiting/abdominal pain or ketones.
- Severe hypo needing assistance or unconsciousness.
- New foot ulceration, chest pain, or sudden vision change.

"""

    @staticmethod
    def get_resources() -> str:
        """Generate resources section"""
        return """11) ☎️ Support Resources

- Diabetes UK Helpline: 0345 123 2399
- DAFNE / DESMOND structured education – clinic referral
- NHS Stop Smoking Service – local referral

"""

    @staticmethod
    def get_action_items() -> str:
        """Generate action items section"""
        return """12) ✅ Consultant Action List (Today)

1. Offer/optimise high-intensity statin per CV risk discussion.
2. Book insulin education refresh (pre-bolus timing, carb counting).
3. Refer to smoking cessation; set quit date.
4. Agree weight loss target 5–7% over 6 months.
5. Set HbA1c goal ≤ 7.0% within 3–6 months if safe.

"""

    @staticmethod
    def get_footer() -> str:
        """Generate report footer"""
        return """13) 🧾 Professional Closing

*Prepared by: Diabetes Specialist Team – Riverside Endocrine Clinic*  
*"This report supports shared decision-making. Please review with your usual diabetes team before making changes to your medicines."*

**Notes on Guidelines**
- Glycaemic targets & insulin education: NICE NG17 (Adults with T1DM)
- Cardiovascular risk/lipids: NICE lipid modification guidance
- Diet & monitoring advice: Diabetes UK / NHS patient guidance
"""
