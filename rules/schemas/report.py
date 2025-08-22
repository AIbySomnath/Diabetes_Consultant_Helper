"""
Pydantic schemas for diabetes report system
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal, Dict
from datetime import date

class PatientIntake(BaseModel):
    uuid: str
    name: str
    dob: str  # YYYY-MM-DD
    sex: Literal["Male", "Female", "Other"]
    diabetes_type: Literal["T1DM", "T2DM"]
    diagnosis_date: Optional[str] = None
    ethnicity: Optional[str] = None
    language: Optional[str] = None
    height_cm: float
    weight_kg: float
    waist_cm: Optional[float] = None
    bp_sys: Optional[float] = None
    bp_dia: Optional[float] = None
    heart_rate: Optional[float] = None
    devices: List[str] = []
    hypos_90d: Optional[int] = None
    severe_hypos_90d: Optional[int] = None
    dka_12m: Optional[int] = None
    meds: List[Dict] = []  # [{name,dose,schedule,notes}]
    allergies: Optional[str] = None
    comorbidities: List[str] = []
    lifestyle: Dict = {}   # {alcohol_units, smoking, sleep_hours, activity_level, diet_pattern}
    screenings: Dict = {}  # {retina_date, foot_date, renal_date, flu_date, pneumo_date}
    labs: Dict = {}        # {hba1c_pct, fpg_mmol, ppg2h_mmol, eGFR, creat, acr, lipids:{tc,ldl,hdl,tg}}
    goals: Optional[str] = None
    notes: Optional[str] = None

    @validator('dob')
    def validate_dob(cls, v):
        try:
            # Validate date format
            date.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')

class Recommendation(BaseModel):
    text: str
    citation_ids: List[str] = []

class ReportOut(BaseModel):
    executive_summary: str
    snapshot: Dict                   # metrics + traffic-light status
    clinical_context: Dict           # therapy, ICR/ISF, device, hypos, DKA, gaps
    labs_table: List[Dict]           # rows {test,value,target,comment}
    interpretation: List[Dict]       # {problem, assessment, plan, citation_ids}
    lifestyle_plan: List[Recommendation]
    diet_plan: Dict                  # principles, sample_day, hydration
    monitoring_plan: Dict            # targets, structured_testing, safety
    screening_tracker: List[Dict]    # {domain,last,result,next_due,status}
    patient_goals: List[str]
    medication_plan: List[Recommendation]
    follow_up: List[Dict]            # {when, actions}
    emr_note: str
    citations: List[Dict]            # {id, source, section}

class PDFExtraction(BaseModel):
    """Schema for PDF extraction results"""
    labs: Dict = {}
    vitals: Dict = {}
    screenings: Dict = {}
    confidence: float = 0.0
    warnings: List[str] = []
    provenance: Dict = {}  # file info, dates found
