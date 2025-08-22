"""
Clinical rule engine for diabetes management.
Evaluates patient data against clinical guidelines and returns relevant flags.
"""
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import date, datetime
from pydantic import BaseModel, validator
from .patient import PatientBase, DiabetesType, CKDStage

class RuleSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"

class ClinicalFlag(BaseModel):
    """A clinical flag raised by the rule engine."""
    id: str
    title: str
    description: str
    severity: RuleSeverity
    category: str
    recommendation: str
    rationale: str
    citation_ids: List[str] = []
    affected_parameters: List[str] = []
    timestamp: datetime = datetime.utcnow()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

class RuleEngine:
    """Evaluates clinical rules against patient data."""
    
    def __init__(self):
        self.rules = [
            self._check_hba1c_above_target,
            self._check_bp_control,
            self._check_albuminuria,
            self._check_hypo_risk,
            self._check_ldl_above_target,
            self._check_smoking_status,
            self._check_foot_screening,
            self._check_retinal_screening,
            self._check_renal_screening,
        ]
    
    def evaluate_patient(self, patient: PatientBase) -> List[ClinicalFlag]:
        """
        Evaluate all clinical rules against a patient's data.
        
        Args:
            patient: The patient data to evaluate
            
        Returns:
            List of ClinicalFlag objects representing any issues found
        """
        flags = []
        
        for rule in self.rules:
            try:
                flag = rule(patient)
                if flag:
                    if isinstance(flag, list):
                        flags.extend(flag)
                    else:
                        flags.append(flag)
            except Exception as e:
                # Log the error but continue with other rules
                print(f"Error evaluating rule {rule.__name__}: {str(e)}")
        
        return flags
    
    def _check_hba1c_above_target(self, patient: PatientBase) -> Optional[ClinicalFlag]:
        """Check if HbA1c is above target for the patient's diabetes type."""
        if patient.hba1c_percent is None:
            return None
            
        target = 6.5 if patient.diabetes_type == DiabetesType.TYPE1 else 7.0
        
        if patient.hba1c_percent > target:
            return ClinicalFlag(
                id="hba1c_above_target",
                title=f"HbA1c above target ({patient.hba1c_percent}% > {target}%)",
                description=(
                    f"Current HbA1c of {patient.hba1c_percent}% is above the target of {target}% "
                    f"for {patient.diabetes_type} diabetes."
                ),
                severity=RuleSeverity.WARNING if patient.hba1c_percent < 8.5 else RuleSeverity.CRITICAL,
                category="Glycemic Control",
                recommendation=(
                    "Consider intensifying diabetes management. Review medications, diet, and lifestyle. "
                    "Consider referral to diabetes specialist if not already done."
                ),
                rationale=(
                    f"NICE guidelines recommend an HbA1c target of {target}% for {patient.diabetes_type} diabetes. "
                    "Higher levels increase the risk of long-term complications."
                ),
                citation_ids=["NG17#1.6.1", "NG28#1.3.1"],
                affected_parameters=["hba1c_percent", "diabetes_type"]
            )
        return None
    
    def _check_bp_control(self, patient: PatientBase) -> Optional[ClinicalFlag]:
        """Check if blood pressure control needs adjustment."""
        if patient.bp_systolic is None or patient.bp_diastolic is None:
            return None
            
        target_sys = 130 if patient.ckd_stage in [CKDStage.STAGE3A, CKDStage.STAGE3B, 
                                                CKDStage.STAGE4, CKDStage.STAGE5] else 140
        target_dia = 80
        
        if patient.bp_systolic >= target_sys or patient.bp_diastolic >= target_dia:
            return ClinicalFlag(
                id="bp_tighten_control",
                title=f"Blood pressure above target ({patient.bp_systolic}/{patient.bp_diastolic} mmHg)",
                description=(
                    f"Current BP {patient.bp_systolic}/{patient.bp_diastolic} mmHg is above the target of "
                    f"{target_sys}/{target_dia} mmHg"
                ),
                severity=RuleSeverity.WARNING if patient.bp_systolic < 160 and patient.bp_diastolic < 100 else RuleSeverity.CRITICAL,
                category="Blood Pressure",
                recommendation=(
                    "Consider optimizing antihypertensive therapy. Review current medications, "
                    "lifestyle modifications, and adherence. Consider 24-hour ambulatory BP monitoring."
                ),
                rationale=(
                    "Tight blood pressure control reduces the risk of cardiovascular and microvascular complications. "
                    f"The target for {patient.diabetes_type} diabetes is <{target_sys}/{target_dia} mmHg, "
                    "with lower targets for patients with chronic kidney disease or proteinuria."
                ),
                citation_ids=["NG28#1.11.1", "NG203#1.2.1"],
                affected_parameters=["bp_systolic", "bp_diastolic", "ckd_stage"]
            )
        return None
    
    def _check_albuminuria(self, patient: PatientBase) -> Optional[ClinicalFlag]:
        """Check for albuminuria based on ACR."""
        if patient.acr is None:
            return None
            
        if patient.acr >= 3:  # A3 or higher
            return ClinicalFlag(
                id="albuminuria_present",
                title=f"Albuminuria detected (ACR: {patient.acr} mg/mmol)",
                description=(
                    f"Albumin:Creatinine Ratio (ACR) of {patient.acr} mg/mmol indicates "
                    "kidney damage and increased cardiovascular risk."
                ),
                severity=RuleSeverity.WARNING if patient.acr < 30 else RuleSeverity.CRITICAL,
                category="Renal Health",
                recommendation=(
                    "Consider ACE inhibitor or ARB therapy if not contraindicated. "
                    "Monitor renal function and potassium. Optimize glycemic and blood pressure control."
                ),
                rationale=(
                    "Albuminuria is a marker of kidney damage and increased cardiovascular risk. "
                    "Early intervention with RAAS blockade can slow progression of kidney disease."
                ),
                citation_ids=["NG28#1.6.1", "NG203#1.5.1"],
                affected_parameters=["acr"]
            )
        return None
    
    def _check_hypo_risk(self, patient: PatientBase) -> Optional[ClinicalFlag]:
        """Check for hypoglycemia risk based on medications."""
        if not patient.medications:
            return None
            
        has_insulin = any(med.is_insulin for med in patient.medications)
        has_sulfonylurea = any(med.is_sulfonylurea for med in patient.medications)
        
        if has_insulin or has_sulfonylurea:
            meds = []
            if has_insulin:
                meds.append("insulin")
            if has_sulfonylurea:
                meds.append("sulfonylurea")
                
            med_list = " and ".join(meds)
                
            return ClinicalFlag(
                id="hypo_risk_from_meds",
                title=f"Hypoglycemia risk from {med_list}",
                description=(
                    f"Patient is on {med_list} which increases the risk of hypoglycemia. "
                    f"Reported {patient.hypos_last_90_days or 'unknown'} hypoglycemic episodes in last 90 days."
                ),
                severity=RuleSeverity.WARNING if not patient.hypos_last_90_days else RuleSeverity.CRITICAL,
                category="Medication Safety",
                recommendation=(
                    "Educate on hypoglycemia recognition/treatment. Consider continuous glucose monitoring. "
                    "Review insulin-to-carb ratios and correction factors. Consider de-escalation if appropriate."
                ),
                rationale=(
                    f"{med_list.capitalize()} therapy is associated with an increased risk of hypoglycemia, "
                    "which can be life-threatening. Patients should be educated on prevention, recognition, "
                    "and treatment of hypoglycemia."
                ),
                citation_ids=["NG17#1.8.1", "NG28#1.6.5"],
                affected_parameters=["medications", "hypos_last_90_days"]
            )
        return None
    
    def _check_ldl_above_target(self, patient: PatientBase) -> Optional[ClinicalFlag]:
        """Check if LDL is above target based on risk factors."""
        if patient.ldl_mmol is None:
            return None
            
        # Higher risk patients (CVD, CKD, or high QRISK) have lower targets
        high_risk = (
            patient.ckd_stage in [CKDStage.STAGE3A, CKDStage.STAGE3B, CKDStage.STAGE4, CKDStage.STAGE5] or
            any(cvd in [c.name.lower() for c in patient.comorbidities] 
                for cvd in ["cvd", "cad", "mi", "stroke", "pad"])
        )
        
        target = 1.4 if high_risk else 2.0  # mmol/L
        
        if patient.ldl_mmol > target:
            return ClinicalFlag(
                id="ldl_above_target",
                title=f"LDL-C above target ({patient.ldl_mmol:.1f} > {target} mmol/L)",
                description=(
                    f"Current LDL-C of {patient.ldl_mmol:.1f} mmol/L is above the target of {target} mmol/L. "
                    f"Patient is considered {'high' if high_risk else 'moderate'} cardiovascular risk."
                ),
                severity=RuleSeverity.WARNING if patient.ldl_mmol < 3.0 else RuleSeverity.CRITICAL,
                category="Lipid Management",
                recommendation=(
                    "Consider high-intensity statin therapy if not already prescribed. "
                    "Optimize lifestyle modifications. Consider ezetimibe or PCSK9 inhibitors if targets not met."
                ),
                rationale=(
                    f"For patients with {patient.diabetes_type} diabetes, NICE recommends an LDL-C target of "
                    f"<{target} mmol/L to reduce cardiovascular risk, with lower targets for higher risk patients."
                ),
                citation_ids=["NG28#1.10.1", "CG181#1.2.1"],
                affected_parameters=["ldl_mmol", "ckd_stage", "comorbidities"]
            )
        return None
    
    def _check_smoking_status(self, patient: PatientBase) -> Optional[ClinicalFlag]:
        """Check smoking status and provide cessation support."""
        if patient.smoking_status == "Current smoker":
            return ClinicalFlag(
                id="current_smoker",
                title="Current smoker - cessation support needed",
                description="Patient reports current tobacco use, which significantly increases cardiovascular risk.",
                severity=RuleSeverity.CRITICAL,
                category="Lifestyle",
                recommendation=(
                    "Offer smoking cessation support. Consider referral to stop-smoking services. "
                    "Discuss pharmacotherapy options (varenicline, bupropion, NRT). Set a quit date within 4 weeks."
                ),
                rationale=(
                    "Smoking cessation is the single most effective intervention to reduce cardiovascular risk in "
                    "people with diabetes. Even brief advice from a healthcare professional increases quit rates."
                ),
                citation_ids=["NG28#1.2.1", "PH10#1.1.1"],
                affected_parameters=["smoking_status"]
            )
        return None
    
    def _check_foot_screening(self, patient: PatientBase) -> Optional[ClinicalFlag]:
        """Check if foot screening is due."""
        if patient.last_foot_screen is None:
            return ClinicalFlag(
                id="foot_screening_due",
                title="Foot screening not documented",
                description="No record of annual diabetic foot screening.",
                severity=RuleSeverity.WARNING,
                category="Preventive Care",
                recommendation=(
                    "Perform annual diabetic foot assessment including inspection, palpation of pulses, "
                    "and assessment of neuropathy (10g monofilament and vibration perception). "
                    "Document risk category and provide appropriate foot care education."
                ),
                rationale=(
                    "Annual foot assessment is recommended for all people with diabetes to identify risk factors "
                    "for foot ulceration and amputation. Early identification of risk factors can prevent complications."
                ),
                citation_ids=["NG19#1.2.1", "NG28#1.7.1"],
                affected_parameters=["last_foot_screen"]
            )
            
        # Check if screening is overdue (more than 15 months since last)
        months_since_screening = (date.today().year - patient.last_foot_screen.year) * 12 + \
                               (date.today().month - patient.last_foot_screen.month)
                               
        if months_since_screening > 15:
            return ClinicalFlag(
                id="foot_screening_overdue",
                title=f"Foot screening overdue (last: {patient.last_foot_screen.strftime('%b %Y')})",
                description=f"Last foot screening was {months_since_screening} months ago.",
                severity=RuleSeverity.WARNING,
                category="Preventive Care",
                recommendation=(
                    "Schedule foot screening as soon as possible. Perform comprehensive assessment including "
                    "inspection, palpation of pulses, and assessment of neuropathy (10g monofilament and vibration perception)."
                ),
                rationale=(
                    "Annual foot assessment is recommended for all people with diabetes to identify risk factors "
                    "for foot ulceration and amputation. Regular screening can detect problems early when they are "
                    "most treatable."
                ),
                citation_ids=["NG19#1.2.1"],
                affected_parameters=["last_foot_screen"]
            )
        return None
    
    def _check_retinal_screening(self, patient: PatientBase) -> Optional[ClinicalFlag]:
        """Check if retinal screening is due."""
        if patient.last_retinal_screen is None:
            return ClinicalFlag(
                id="retinal_screening_due",
                title="Retinal screening not documented",
                description="No record of annual diabetic retinal screening.",
                severity=RuleSeverity.WARNING,
                category="Preventive Care",
                recommendation=(
                    "Refer for annual digital retinal photography. Ensure pupils are dilated for optimal imaging. "
                    "Document results and any required follow-up."
                ),
                rationale=(
                    "Annual retinal screening is essential for early detection of diabetic retinopathy, "
                    "a leading cause of preventable blindness. Early treatment can prevent vision loss."
                ),
                citation_ids=["NG28#1.16.1", "NG17#1.13.1"],
                affected_parameters=["last_retinal_screen"]
            )
            
        # Check if screening is overdue (more than 15 months since last)
        months_since_screening = (date.today().year - patient.last_retinal_screen.year) * 12 + \
                               (date.today().month - patient.last_retinal_screen.month)
                               
        if months_since_screening > 15:
            return ClinicalFlag(
                id="retinal_screening_overdue",
                title=f"Retinal screening overdue (last: {patient.last_retinal_screen.strftime('%b %Y')})",
                description=f"Last retinal screening was {months_since_screening} months ago.",
                severity=RuleSeverity.WARNING,
                category="Preventive Care",
                recommendation=(
                    "Schedule retinal screening as soon as possible. Use mydriatic retinal photography "
                    "for optimal image quality. Document results and any required follow-up."
                ),
                rationale=(
                    "Annual retinal screening is essential for early detection of diabetic retinopathy. "
                    "Delays in screening increase the risk of vision-threatening complications."
                ),
                citation_ids=["NG28#1.16.1"],
                affected_parameters=["last_retinal_screen"]
            )
        return None
    
    def _check_renal_screening(self, patient: PatientBase) -> Optional[ClinicalFlag]:
        """Check if renal screening is due."""
        if patient.last_renal_screen is None:
            return ClinicalFlag(
                id="renal_screening_due",
                title="Renal screening not documented",
                description="No record of annual renal screening (eGFR and ACR).",
                severity=RuleSeverity.WARNING,
                category="Preventive Care",
                recommendation=(
                    "Order renal function tests including eGFR and ACR. Monitor for signs of chronic kidney disease. "
                    "Optimize blood pressure and glycemic control to preserve renal function."
                ),
                rationale=(
                    "Annual assessment of renal function is recommended for all people with diabetes to detect "
                    "early signs of diabetic kidney disease. Early intervention can slow progression."
                ),
                citation_ids=["NG28#1.6.1", "NG203#1.5.1"],
                affected_parameters=["last_renal_screen", "egfr", "acr"]
            )
            
        # Check if screening is overdue (more than 15 months since last)
        months_since_screening = (date.today().year - patient.last_renal_screen.year) * 12 + \
                               (date.today().month - patient.last_renal_screen.month)
                               
        if months_since_screening > 15:
            return ClinicalFlag(
                id="renal_screening_overdue",
                title=f"Renal screening overdue (last: {patient.last_renal_screen.strftime('%b %Y')})",
                description=f"Last renal screening was {months_since_screening} months ago.",
                severity=RuleSeverity.WARNING,
                category="Preventive Care",
                recommendation=(
                    "Order renal function tests including eGFR and ACR. Consider additional testing if indicated. "
                    "Review medications that may affect renal function."
                ),
                rationale=(
                    "Regular monitoring of renal function is essential for early detection and management of "
                    "diabetic kidney disease. Delays in screening may result in missed opportunities for intervention."
                ),
                citation_ids=["NG28#1.6.1"],
                affected_parameters=["last_renal_screen"]
            )
        return None

# Example usage:
# rule_engine = RuleEngine()
# flags = rule_engine.evaluate_patient(patient)
