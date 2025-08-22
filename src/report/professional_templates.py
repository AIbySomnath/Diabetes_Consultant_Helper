"""
Professional report templates for diabetes management system.
These templates follow NHS clinical reporting standards.
"""
from datetime import datetime
from typing import Dict, Any, Optional

class ProfessionalTemplates:
    """Templates for generating professional diabetes management reports."""
    
    def __init__(self):
        self.now = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    def get_header(self, patient_data: Dict[str, Any]) -> str:
        """Generate report header with patient information."""
        nhs_number = patient_data.get('nhs_number', 'N/A')
        dob = patient_data.get('dob', 'N/A')
        age = patient_data.get('age', 'N/A')
        sex = patient_data.get('sex', 'Not specified')
        
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
            <div style="background-color: #005EB8; color: white; padding: 15px; text-align: center; margin-bottom: 20px;">
                <h1 style="margin: 0; font-size: 24px;">DIABETES MANAGEMENT REPORT</h1>
                <p style="margin: 5px 0 0; font-size: 14px;">NHS Diabetes Specialist Team | {self.now}</p>
            </div>
            
            <div style="border: 1px solid #ddd; padding: 15px; margin-bottom: 20px; background-color: #f9f9f9;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="width: 50%; vertical-align: top;">
                            <p style="margin: 5px 0;"><strong>Name:</strong> {patient_data.get('name', 'N/A')}</p>
                            <p style="margin: 5px 0;"><strong>NHS Number:</strong> {nhs_number}</p>
                            <p style="margin: 5px 0;"><strong>DOB:</strong> {dob} (Age: {age})</p>
                        </td>
                        <td style="width: 50%; vertical-align: top;">
                            <p style="margin: 5px 0;"><strong>Gender:</strong> {sex}</p>
                            <p style="margin: 5px 0;"><strong>Diabetes Type:</strong> {patient_data.get('diabetes_type', 'N/A')}</p>
                            <p style="margin: 5px 0;"><strong>Diagnosis Date:</strong> {patient_data.get('diagnosis_date', 'N/A')}</p>
                        </td>
                    </tr>
                </table>
            </div>
        """
    
    def get_clinical_summary(self, patient_data: Dict[str, Any], labs_data: Dict[str, Any]) -> str:
        """Generate clinical summary section."""
        hba1c = labs_data.get('hba1c')
        hba1c_status = self._get_hba1c_status(hba1c)
        
        bp = f"{labs_data.get('bp_systolic', '--')}/{labs_data.get('diastolic', '--')} mmHg"
        bmi = self._calculate_bmi(labs_data.get('weight'), labs_data.get('height'))
        bmi_status = self._get_bmi_status(bmi)
        
        return f"""
        <div style="margin-bottom: 20px;">
            <h2 style="color: #005EB8; border-bottom: 2px solid #005EB8; padding-bottom: 5px;">1. CLINICAL SUMMARY</h2>
            
            <div style="display: flex; flex-wrap: wrap; margin: 10px 0 20px 0;">
                <div style="flex: 1; min-width: 200px; margin: 5px; padding: 10px; background-color: #f0f7ff; border-radius: 5px;">
                    <p style="font-weight: bold; margin: 0 0 5px 0; color: #003087;">HbA1c</p>
                    <p style="margin: 0; font-size: 18px;">{hba1c or '--'}% {hba1c_status}</p>
                    <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">Target: <7.0%</p>
                </div>
                
                <div style="flex: 1; min-width: 200px; margin: 5px; padding: 10px; background-color: #f0f7ff; border-radius: 5px;">
                    <p style="font-weight: bold; margin: 0 0 5px 0; color: #003087;">Blood Pressure</p>
                    <p style="margin: 0; font-size: 18px;">{bp}</p>
                    <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">Target: <140/85 mmHg</p>
                </div>
                
                <div style="flex: 1; min-width: 200px; margin: 5px; padding: 10px; background-color: #f0f7ff; border-radius: 5px;">
                    <p style="font-weight: bold; margin: 0 0 5px 0; color: #003087;">BMI</p>
                    <p style="margin: 0; font-size: 18px;">{bmi or '--'} {bmi_status}</p>
                    <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">Target: 18.5-24.9</p>
                </div>
            </div>
            
            <div style="margin: 15px 0; padding: 10px; background-color: #f8f8f8; border-left: 4px solid #005EB8;">
                <p style="margin: 0; font-style: italic;">
                    {self._get_clinical_interpretation(patient_data, labs_data)}
                </p>
            </div>
        </div>
        """
    
    def get_management_plan(self, patient_data: Dict[str, Any]) -> str:
        """Generate management plan section."""
        return """
        <div style="margin-bottom: 20px;">
            <h2 style="color: #005EB8; border-bottom: 2px solid #005EB8; padding-bottom: 5px;">2. MANAGEMENT PLAN</h2>
            
            <div style="margin: 15px 0;">
                <h3 style="color: #003087; margin-bottom: 5px;">Lifestyle Recommendations</h3>
                <ul style="margin-top: 5px; padding-left: 20px;">
                    <li>Engage in at least 150 minutes of moderate-intensity physical activity per week</li>
                    <li>Follow a balanced diet focusing on low glycemic index foods</li>
                    <li>Limit alcohol intake to within recommended guidelines (≤14 units/week)</li>
                    <li>Smoking cessation support offered (if applicable)</li>
                </ul>
            </div>
            
            <div style="margin: 15px 0;">
                <h3 style="color: #003087; margin-bottom: 5px;">Medication Review</h3>
                <p>Current medications have been reviewed and adjusted as follows:</p>
                <ul style="margin-top: 5px; padding-left: 20px;">
                    <li>Metformin 1000mg BD (continue)</li>
                    <li>Empagliflozin 25mg OD (newly added)</li>
                    <li>Atorvastatin 40mg ON (continue)</li>
                </ul>
            </div>
        </div>
        """
    
    def get_monitoring_plan(self) -> str:
        """Generate monitoring and follow-up plan."""
        return """
        <div style="margin-bottom: 20px;">
            <h2 style="color: #005EB8; border-bottom: 2px solid #005EB8; padding-bottom: 5px;">3. MONITORING & FOLLOW-UP</h2>
            
            <table style="width: 100%; border-collapse: collapse; margin: 10px 0 20px 0;">
                <tr style="background-color: #f0f7ff;">
                    <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Test</th>
                    <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Frequency</th>
                    <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Next Due</th>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">HbA1c</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">3-monthly</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">01/12/2023</td>
                </tr>
                <tr style="background-color: #f9f9f9;">
                    <td style="padding: 8px; border: 1px solid #ddd;">Renal Function</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">6-monthly</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">01/03/2024</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">Foot Check</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">Annual</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">01/06/2024</td>
                </tr>
                <tr style="background-color: #f9f9f9;">
                    <td style="padding: 8px; border: 1px solid #ddd;">Retinal Screening</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">Annual</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">01/06/2024</td>
                </tr>
            </table>
            
            <div style="margin: 15px 0; padding: 10px; background-color: #fff8e1; border-left: 4px solid #ffc107;">
                <p style="margin: 0; font-weight: bold; color: #e65100;">Next Appointment:</p>
                <p style="margin: 5px 0 0 0;">Diabetes Clinic on 15/12/2023 at 10:30 AM</p>
                <p style="margin: 5px 0 0 0; font-size: 13px;">Please bring your blood glucose meter and food diary.</p>
            </div>
        </div>
        """
    
    def get_safety_advice(self) -> str:
        """Generate safety advice and red flags section."""
        return """
        <div style="margin-bottom: 20px;">
            <h2 style="color: #d32f2f; border-bottom: 2px solid #d32f2f; padding-bottom: 5px;">4. SAFETY & RED FLAGS</h2>
            
            <div style="margin: 15px 0;">
                <h3 style="color: #b71c1c; margin-bottom: 5px;">Seek Immediate Medical Attention If You Experience:</h3>
                <ul style="margin-top: 5px; padding-left: 20px;">
                    <li>Blood glucose persistently >15 mmol/L or <4 mmol/L</li>
                    <li>Signs of DKA (nausea, vomiting, abdominal pain, rapid breathing, fruity-smelling breath)</li>
                    <li>Severe hypoglycemia (unable to self-treat, loss of consciousness)</li>
                    <li>New or worsening chest pain or shortness of breath</li>
                </ul>
                
                <div style="margin: 15px 0; padding: 10px; background-color: #ffebee; border-left: 4px solid #d32f2f;">
                    <p style="margin: 0; font-weight: bold;">Out of Hours Emergency Contact:</p>
                    <p style="margin: 5px 0 0 0;">NHS 111 or attend A&E if severely unwell</p>
                </div>
            </div>
        </div>
        """
    
    def get_footer(self) -> str:
        """Generate report footer."""
        return f"""
        <div style="margin-top: 30px; padding-top: 15px; border-top: 1px solid #ddd; font-size: 12px; color: #666; text-align: center;">
            <p>This report was generated on {self.now} by the NHS Diabetes Management System</p>
            <p>For any queries, please contact the Diabetes Specialist Team on 020 7123 4567</p>
            <p>Confidentiality Notice: This document contains privileged and confidential information intended only for the use of the addressee.</p>
        </div>
        </div>  <!-- Close container div -->
        """
    
    def _get_hba1c_status(self, hba1c: Optional[float]) -> str:
        """Get status indicator for HbA1c value."""
        if hba1c is None:
            return ""
        if hba1c < 7.5:
            return "✅"
        elif hba1c < 9.0:
            return "⚠️"
        else:
            return "❌"
    
    def _get_bmi_status(self, bmi: Optional[float]) -> str:
        """Get status indicator for BMI value."""
        if bmi is None:
            return ""
        if 18.5 <= bmi <= 24.9:
            return "✅"
        elif 25 <= bmi <= 29.9:
            return "⚠️"
        else:
            return "❌"
    
    def _calculate_bmi(self, weight_kg: Optional[float], height_cm: Optional[float]) -> Optional[float]:
        """Calculate BMI from weight and height."""
        if not all([weight_kg, height_cm]) or height_cm == 0:
            return None
        height_m = height_cm / 100
        return round(weight_kg / (height_m ** 2), 1)
    
    def _get_clinical_interpretation(self, patient_data: Dict[str, Any], labs_data: Dict[str, Any]) -> str:
        """Generate clinical interpretation based on patient data."""
        hba1c = labs_data.get('hba1c')
        ldl = labs_data.get('ldl')
        bmi = self._calculate_bmi(labs_data.get('weight'), labs_data.get('height'))
        
        interpretation = []
        
        # HbA1c interpretation
        if hba1c:
            if hba1c > 8.5:
                interpretation.append(f"Poor glycaemic control (HbA1c {hba1c}%) requiring intensification of therapy.")
            elif hba1c > 7.5:
                interpretation.append(f"Suboptimal glycaemic control (HbA1c {hba1c}%) with room for improvement.")
            else:
                interpretation.append(f"Good glycaemic control (HbA1c {hba1c}%) - maintain current management.")
        
        # Lipid management
        if ldl:
            if ldl > 2.5:
                interpretation.append("Elevated LDL cholesterol - consider statin intensification.")
            else:
                interpretation.append("Lipid profile at target - continue current therapy.")
        
        # Weight management
        if bmi:
            if bmi > 30:
                interpretation.append(f"Obesity (BMI {bmi}) - recommend weight management program.")
            elif bmi > 25:
                interpretation.append(f"Overweight (BMI {bmi}) - lifestyle modifications advised.")
        
        # Smoking status
        if patient_data.get('smoking_status', '').lower() in ['yes', 'current']:
            interpretation.append("Current smoker - strongly advised to quit. Referral to smoking cessation service recommended.")
        
        return " ".join(interpretation) if interpretation else "No significant clinical concerns identified."
