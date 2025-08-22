"""
Report Generator for Diabetes Management System
Generates personalised diabetes reports in UK consultant style
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
import streamlit as st
from src.rag.retrieval import RAGPipeline
from src.utils.validators import validate_red_flags
from .enhanced_generator import EnhancedReportGenerator

class ReportGenerator:
    """Generate personalised diabetes management reports"""
    
    def __init__(self):
        """Initialize report generator with RAG pipeline"""
        self.rag_pipeline = RAGPipeline()
        self.report_sections = [
            "Summary of Health Status",
            "Lifestyle Plan",
            "Diet Plan",
            "Monitoring & Safety",
            "Patient Management & Follow-up",
            "References"
        ]
    
    def generate_report(
        self,
        patient_data: Dict,
        labs_data: Dict,
        lifestyle_data: Dict,
        stream: bool = False
    ) -> tuple[str, Dict[str, Dict]]:
        """
        Generate complete personalised diabetes report
        
        Returns:
            - Generated report text with citations
            - Sources dictionary for references
        """
        try:
            # Initialize the enhanced report generator
            generator = EnhancedReportGenerator()
            
            # Generate the report using the enhanced generator
            report = generator.generate_report(patient_data, labs_data, lifestyle_data)
            
            # For now, return empty sources
            # In a production system, you would retrieve and include actual sources
            sources = {}
            
            return report, sources
            
        except Exception as e:
            error_msg = f"Error generating report: {str(e)}"
            st.error(error_msg)
            return f"<div style='color: red; padding: 15px; border: 1px solid #f5c6cb; background-color: #f8d7da; border-radius: 4px;'>{error_msg}</div>", {}
    
    def _calculate_age(self, dob):
        """Calculate age from date of birth
        
        Args:
            dob: Date of birth as a string in YYYY-MM-DD format or datetime.date object
            
        Returns:
            int: Age in years
        """
        if not dob:
            return 0
            
        if isinstance(dob, str):
            try:
                dob = datetime.strptime(dob, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                return 0
                
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return max(0, age)  # Ensure age is not negative
        
    def _generate_mock_report(
        self,
        patient_data: Dict,
        labs_data: Dict,
        lifestyle_data: Dict,
        red_flags: List[str],
        chunks: List[Dict],
        sources: Dict[str, Dict]
    ) -> str:
        """Generate mock report for POC demonstration"""
        
        # Get patient details - handle both name formats
        if 'name' in patient_data:
            name = patient_data['name']
        else:
            first_name = patient_data.get('first_name', '')
            last_name = patient_data.get('last_name', '')
            name = f"{first_name} {last_name}".strip()
        name = name or 'Patient'
        
        # Get age directly from patient data
        age = patient_data.get('age', 'Not specified')
        sex = patient_data.get('sex', 'Not specified')
        
        # Get lab values
        hba1c = labs_data.get('hba1c', 'Not provided')
        # Get FPG and 2h-PPG from the labs data
        fpg = labs_data.get('fpg', 'Not provided')
        ppg_2h = labs_data.get('ppg_2h', 'Not provided')
        bp_sys = labs_data.get('bp_systolic')
        bp_dia = labs_data.get('bp_diastolic')
        lab_date = labs_data.get('lab_date')
        
        # Format lab date if available
        lab_date_str = ''
        if lab_date:
            try:
                if isinstance(lab_date, str):
                    lab_date = datetime.strptime(lab_date, '%Y-%m-%d').date()
                lab_date_str = f" (as of {lab_date.strftime('%d %b %Y')})"
            except (ValueError, AttributeError):
                pass
        
        # Calculate BMI
        weight = labs_data.get('weight')
        height = labs_data.get('height')
        bmi = None
        if weight and height:
            bmi = weight / ((height/100) ** 2)
        
        # Get lifestyle
        # Normalize activity level to consistent categories
        raw_activity = (lifestyle_data.get('activity_level') or '').strip().lower()
        if raw_activity in ['sedentary', 'inactive', 'none']:
            activity_norm = 'sedentary'
        elif raw_activity in ['light', 'lightly active']:
            activity_norm = 'light'
        elif raw_activity in ['moderate', 'moderately active']:
            activity_norm = 'moderate'
        elif raw_activity in ['very active', 'vigorous']:
            activity_norm = 'very'
        else:
            activity_norm = 'unspecified'
        activity = lifestyle_data.get('activity_level', 'Not specified')
        diet_pattern = lifestyle_data.get('dietary_pattern', 'Not specified')
        goal = lifestyle_data.get('primary_goal', 'Improve overall health')
        
        # Build report
        report = f"""# Personalised Diabetes Management Report

**Patient:** {name}  
**Age:** {age} years  
**Sex:** {sex}  

## Key Laboratory Values{lab_date_str}

| Test | Value | Target Range |
|------|-------|--------------|
| HbA1c | {hba1c} mmol/mol | < 48 mmol/mol (non-diabetic) |
| Fasting Plasma Glucose (FPG) | {fpg} mmol/L | 4.0-5.4 mmol/L (normal) |
| 2-hour Post-Prandial Glucose (2h-PPG) | {ppg_2h} mmol/L | < 7.8 mmol/L (normal) |

## Clinical Assessment
**Date:** {datetime.now().strftime('%d %B %Y')}  
**Prepared by:** Diabetes Specialist Team

---

## Clinical Disclaimer
This report is generated as a clinical decision support tool and should be reviewed by a qualified healthcare professional before implementation. It does not replace clinical judgement.

"""
        
        # Add red flag alert if present
        if red_flags:
            report += """## ⚠️ URGENT CLINICAL REVIEW REQUIRED

The following red flag conditions have been identified requiring immediate medical attention:

"""
            for flag in red_flags:
                report += f"- {flag}\n"
            report += "\nPlease arrange urgent consultation with diabetes specialist team.\n\n---\n\n"
        
        # Section 1: Summary of Health Status
        report += f"""## 1. Summary of Health Status

### Current Glycaemic Control
{name}'s most recent HbA1c is {hba1c}% (recorded {labs_data.get('lab_date', 'recently')}), """
        
        if isinstance(hba1c, (int, float)):
            if hba1c < 7:
                report += "which indicates good glycaemic control meeting NICE targets [S1]. "
            elif hba1c < 8:
                report += "which is slightly above the NICE recommended target of 7% [S1]. "
            elif hba1c < 10:
                report += "indicating suboptimal control requiring treatment optimisation [S1]. "
            else:
                report += "indicating very poor control requiring urgent intervention [S1]. "
        else:
            report += "which requires clinical interpretation. "
        
        report += f"""The fasting plasma glucose is {fpg} mmol/L and 2-hour post-prandial glucose is {ppg_2h} mmol/L.

### Cardiovascular Risk Factors
"""
        
        if bp_sys and bp_dia:
            report += f"Blood pressure: {bp_sys}/{bp_dia} mmHg. "
            if bp_sys < 130 and bp_dia < 80:
                report += "This is within target range for diabetes [S2]. "
            else:
                report += "Consider optimising antihypertensive therapy [S2]. "
        
        if bmi:
            report += f"\nBMI: {bmi:.1f} kg/m². "
            if bmi < 25:
                report += "Healthy weight range. "
            elif bmi < 30:
                report += "Overweight - weight reduction advised. "
            else:
                report += "Obese - structured weight management programme recommended [S2]. "
        
        report += "\n\n"
        
        # Section 2: Lifestyle Plan
        report += f"""## 2. Lifestyle Plan

### Physical Activity Recommendations
Current activity level: {activity}

"""
        
        if activity_norm == 'sedentary':
            report += """Recommended progression:
- **Week 1-2:** Start with 10-minute walks after meals, 3 times daily [S3]
- **Week 3-4:** Increase to 15-minute walks, add gentle stretching
- **Week 5-6:** Progress to 20-minute walks, consider swimming or cycling
- **Target:** Build to 150 minutes moderate activity per week [S4]

Start slowly and gradually increase intensity. Any activity is better than none.
"""
        elif activity_norm in ['light', 'moderate']:
            report += """Recommended progression:
- **Current:** Continue current activities
- **Enhancement:** Add resistance exercises 2 days/week [S3]
- **Variety:** Include swimming, cycling, or dancing
- **Target:** Achieve 150 minutes moderate activity per week [S4]
"""
        elif activity_norm == 'very':
            report += """Excellent activity level. Maintain current routine:
- Continue 150+ minutes moderate activity weekly [S4]
- Include resistance training 2-3 days/week
- Monitor for hypoglycaemia if on insulin/sulfonylureas [S5]
"""
        else:
            report += "Aim to gradually increase activity towards 150 minutes/week of moderate intensity [S4]. Choose activities you enjoy and can sustain.\n"
        
        report += f"""
### Lifestyle Modifications
Primary goal: {goal}

Key recommendations:
- Regular meal timing to stabilise blood glucose
- Stress management through mindfulness or yoga
- Aim for 7-9 hours quality sleep nightly
- Smoking cessation support if applicable

"""
        
        # Section 3: Diet Plan
        report += """## 3. Diet Plan

### Dietary Principles
Following NHS Eatwell Guide with diabetes-specific modifications [S3]:
- **50% plate:** Non-starchy vegetables
- **25% plate:** Lean protein
- **25% plate:** Complex carbohydrates
- **Portions:** Use 9-inch plate for portion control

### 7-Day Menu Plan

| Day | Breakfast | Lunch | Dinner | Snacks |
|-----|-----------|-------|--------|--------|
| **Monday** | Porridge (40g oats) with berries, chopped nuts | Chicken salad sandwich (wholegrain), apple | Grilled salmon, roasted vegetables, quinoa | Greek yoghurt, handful almonds |
| **Tuesday** | 2 scrambled eggs, wholegrain toast, tomatoes | Lentil soup, mixed salad, oatcake | Chicken stir-fry with brown rice | Apple slices with peanut butter |
| **Wednesday** | Greek yoghurt with granola (30g), berries | Tuna jacket potato, side salad | Lean beef chilli, cauliflower rice | Carrot sticks with hummus |
| **Thursday** | Overnight oats with chia seeds, banana | Chicken wrap with salad, orange | Baked cod, new potatoes, green beans | Mixed nuts (25g) |
| **Friday** | Wholegrain cereal (30g), semi-skimmed milk, berries | Minestrone soup, wholegrain roll | Turkey meatballs, courgetti, tomato sauce | Low-fat cheese, crackers |
| **Saturday** | Poached eggs on toast, grilled mushrooms | Quinoa salad with feta, cucumber | Roast chicken, roasted root veg, greens | Dark chocolate (20g), berries |
| **Sunday** | Protein pancakes with berries | Smoked salmon bagel (thin), rocket | Lean roast beef, Yorkshire pud (small), veg | Rice cakes with almond butter |

**Hydration:** 6-8 glasses water daily. Limit fruit juice to 150ml/day with meals.

"""
        
        # Section 4: Monitoring & Safety
        report += """## 4. Monitoring & Safety

### Blood Glucose Monitoring
"""
        
        if 'Insulin' in patient_data.get('medications', []):
            report += """**Insulin users - Test 4+ times daily [S5]:**
- Before each meal
- Before bed
- Before driving
- If feeling unwell/hypoglycaemic symptoms
"""
        else:
            report += """**Structured monitoring recommended:**
- Test before breakfast and 2 hours after main meal
- Weekly paired testing to understand food impact
- More frequent during illness or medication changes
"""
        
        report += """
### Target Ranges
- **Before meals:** 4-7 mmol/L
- **2 hours after meals:** <8.5 mmol/L
- **Before bed:** 6-10 mmol/L

### Hypoglycaemia Management (if <4 mmol/L)
1. Take 15-20g fast-acting carbohydrate immediately
2. Retest after 15 minutes
3. Repeat if still <4 mmol/L
4. Follow with longer-acting carbohydrate

### Sick Day Rules [S6]
- Continue diabetes medications (never stop insulin)
- Test blood glucose every 2-4 hours
- Stay hydrated - sip fluids regularly
- Seek urgent help if glucose >15 mmol/L persistently

"""
        
        # Section 5: Patient Management & Follow-up
        report += """## 5. Patient Management & Follow-up

### Follow-up Schedule
- **6 weeks:** Review progress, adjust targets
- **3 months:** HbA1c, weight, BP check
- **6 months:** Full diabetes review
- **Annual:** Complete assessment including:
  - Retinal screening
  - Foot assessment
  - Kidney function (eGFR, ACR)
  - Lipid profile
  - Flu vaccination

### Red Flags Requiring Urgent Review
- Blood glucose consistently >15 mmol/L
- Symptoms of DKA (nausea, vomiting, abdominal pain)
- Severe hypoglycaemia requiring assistance
- Signs of infection with poor glycaemic control
- New vision changes or foot problems

### Support Resources
- Diabetes UK Helpline: 0345 123 2399
- NHS Diabetes Prevention Programme
- Local diabetes support groups
- DESMOND/DAFNE structured education

"""
        
        # Section 6: References
        report += """## 6. References

"""
        for source_id, source_data in sources.items():
            report += f"""[{source_id}] {source_data['title']}. {source_data['source']}. Updated: {source_data['updated']}. Available at: {source_data['url']}

"""
        
        report += """
---

**Report prepared in accordance with:**
- NICE NG28: Type 2 diabetes in adults: management (2022)
- NHS England: Framework for personalised care in diabetes
- Diabetes UK: Evidence-based nutrition guidelines (2023)

**Next Review Date:** """ + (datetime.now() + timedelta(days=90)).strftime('%d %B %Y')
        
        return report
    
    def _calculate_age(self, dob) -> int:
        """Calculate age from date of birth"""
        if not dob:
            return 0
        
        try:
            if isinstance(dob, str):
                from datetime import datetime
                dob = datetime.strptime(dob, '%Y-%m-%d').date()
            
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return age
        except:
            return 0
    
    def regenerate_section(
        self,
        section_name: str,
        original_report: str,
        patient_context: Dict,
        sources: Dict[str, Dict]
    ) -> str:
        """Regenerate a specific section of the report"""
        
        # For POC, return the original section
        # In production, this would call GPT-4 with section-specific prompt
        
        if section_name not in self.report_sections:
            raise ValueError(f"Invalid section: {section_name}")
        
        # Extract original section
        try:
            section_num = self.report_sections.index(section_name) + 1
            section_header = f"## {section_num}. {section_name}"
            
            parts = original_report.split(section_header)
            if len(parts) < 2:
                return f"Could not find section: {section_name}"
            
            # Get content until next section
            section_content = parts[1].split("\n## ")[0]
            
            # For POC, return with minor modification
            regenerated = f"{section_header}\n\n*[Section regenerated at {datetime.now().strftime('%H:%M')}]*\n{section_content}"
            
            return regenerated
            
        except Exception as e:
            return f"Error regenerating section: {str(e)}"
