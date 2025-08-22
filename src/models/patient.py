"""
Patient data models for the Diabetes Consultant application.
Uses Pydantic for data validation and serialization.
"""
from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from pydantic.functional_validators import model_validator
import re

class Sex(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"
    UNKNOWN = "Unknown"

class DiabetesType(str, Enum):
    TYPE1 = "Type 1"
    TYPE2 = "Type 2"
    GESTATIONAL = "Gestational"
    MODY = "MODY"
    LADA = "LADA"
    OTHER = "Other"

class SmokingStatus(str, Enum):
    NEVER = "Never smoked"
    FORMER = "Former smoker"
    CURRENT = "Current smoker"
    UNKNOWN = "Unknown"

class AlcoholConsumption(str, Enum):
    NONE = "None"
    OCCASIONAL = "Occasional (1-7 units/week)"
    MODERATE = "Moderate (7-14 units/week)"
    HEAVY = "Heavy (>14 units/week)"
    UNKNOWN = "Unknown"

class ActivityLevel(str, Enum):
    SEDENTARY = "Sedentary (little or no exercise)"
    LIGHT = "Light (light exercise 1-3 days/week)"
    MODERATE = "Moderate (moderate exercise 3-5 days/week)"
    ACTIVE = "Active (hard exercise 3-5 days/week)"
    VERY_ACTIVE = "Very active (hard exercise 6-7 days/week)"
    UNKNOWN = "Unknown"

class DietPattern(str, Enum):
    WESTERN = "Western"
    MEDITERRANEAN = "Mediterranean"
    VEGETARIAN = "Vegetarian"
    VEGAN = "Vegan"
    LOW_CARB = "Low carbohydrate"
    UNKNOWN = "Unknown"

class CKDStage(str, Enum):
    STAGE1 = "Stage 1 (eGFR ≥90 with kidney damage)"
    STAGE2 = "Stage 2 (eGFR 60-89 with kidney damage)"
    STAGE3A = "Stage 3a (eGFR 45-59)"
    STAGE3B = "Stage 3b (eGFR 30-44)"
    STAGE4 = "Stage 4 (eGFR 15-29)"
    STAGE5 = "Stage 5 (eGFR <15 or on dialysis)"
    NONE = "No CKD"
    UNKNOWN = "Unknown"

class Medication(BaseModel):
    name: str
    dose: str
    frequency: str
    start_date: Optional[date] = None
    is_insulin: bool = False
    is_sulfonylurea: bool = False

class Comorbidity(BaseModel):
    name: str
    diagnosis_date: Optional[date] = None
    is_controlled: Optional[bool] = None
    notes: Optional[str] = None

class LabResult(BaseModel):
    test_name: str
    value: float
    unit: str
    date: date
    reference_range: Optional[str] = None
    is_abnormal: Optional[bool] = None

class PatientBase(BaseModel):
    # Identification
    first_name: str
    last_name: str
    date_of_birth: date
    sex: Sex
    nhs_number: Optional[str] = None
    
    # Consent
    consent_given: bool = False
    consent_date: Optional[date] = None
    
    # Anthropometrics
    height_cm: float = Field(..., gt=0, le=250, description="Height in centimeters")
    weight_kg: float = Field(..., gt=0, le=300, description="Weight in kilograms")
    
    # Vitals
    bp_systolic: Optional[int] = Field(None, ge=70, le=250, description="Systolic blood pressure in mmHg")
    bp_diastolic: Optional[int] = Field(None, ge=40, le=150, description="Diastolic blood pressure in mmHg")
    
    # Diabetes Profile
    diabetes_type: DiabetesType
    diagnosis_date: date
    devices: List[str] = []
    hypos_last_90_days: Optional[int] = Field(None, ge=0, description="Number of hypoglycemic episodes in last 90 days")
    dka_last_12_months: Optional[int] = Field(None, ge=0, description="Number of DKA episodes in last 12 months")
    
    # Medications
    medications: List[Medication] = []
    allergies: List[str] = []
    
    # Comorbidities
    comorbidities: List[Comorbidity] = []
    ckd_stage: Optional[CKDStage] = None
    
    # Lifestyle
    smoking_status: SmokingStatus
    alcohol_units_week: Optional[int] = Field(None, ge=0, description="Average units of alcohol per week")
    activity_level: ActivityLevel
    diet_pattern: DietPattern
    
    # Labs (most recent)
    hba1c_percent: Optional[float] = Field(None, ge=3.0, le=20.0, description="Most recent HbA1c in %")
    hba1c_mmol_mol: Optional[float] = Field(None, ge=10, le=200, description="Most recent HbA1c in mmol/mol")
    total_cholesterol: Optional[float] = Field(None, ge=1.0, le=20.0, description="Total cholesterol in mmol/L")
    ldl_mmol: Optional[float] = Field(None, ge=0.5, le=15.0, description="LDL cholesterol in mmol/L")
    hdl_mmol: Optional[float] = Field(None, ge=0.1, le=5.0, description="HDL cholesterol in mmol/L")
    triglycerides: Optional[float] = Field(None, ge=0.1, le=30.0, description="Triglycerides in mmol/L")
    egfr: Optional[float] = Field(None, ge=5, le=150, description="eGFR in mL/min/1.73m²")
    acr: Optional[float] = Field(None, ge=0, le=1000, description="Albumin:Creatinine Ratio in mg/mmol")
    
    # Screenings
    last_retinal_screen: Optional[date] = None
    last_foot_screen: Optional[date] = None
    last_renal_screen: Optional[date] = None
    
    # Notes
    consultant_notes: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Validators
    @validator('nhs_number')
    def validate_nhs_number(cls, v):
        if v is None:
            return v
        # Simple NHS number validation (10 digits, last digit is check digit)
        if not re.match(r'^\d{10}$', v):
            raise ValueError("NHS number must be 10 digits")
        return v
    
    @validator('date_of_birth', 'diagnosis_date', pre=True)
    def parse_dates(cls, v):
        if isinstance(v, str):
            try:
                return datetime.strptime(v, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        return v
    
    @model_validator(mode='after')
    def calculate_derived_fields(self) -> 'PatientBase':
        # Calculate BMI
        if self.height_cm and self.weight_kg:
            height_m = self.height_cm / 100
            self.bmi = round(self.weight_kg / (height_m ** 2), 1)
        
        # Calculate diabetes duration in years
        if hasattr(self, 'diagnosis_date') and hasattr(self, 'date_of_birth'):
            if self.diagnosis_date and self.date_of_birth:
                if self.diagnosis_date < self.date_of_birth:
                    raise ValueError("Diagnosis date cannot be before date of birth")
                
                # Calculate diabetes duration in years
                duration_days = (datetime.now().date() - self.diagnosis_date).days
                self.diabetes_duration_years = round(duration_days / 365.25, 1)
        
        # Set CKD stage based on eGFR if not explicitly set
        if hasattr(self, 'egfr') and self.egfr is not None:
            if not hasattr(self, 'ckd_stage') or self.ckd_stage is None:
                if self.egfr >= 90:
                    self.ckd_stage = CKDStage.STAGE1
                elif 60 <= self.egfr < 90:
                    self.ckd_stage = CKDStage.STAGE2
                elif 45 <= self.egfr < 60:
                    self.ckd_stage = CKDStage.STAGE3A
                elif 30 <= self.egfr < 45:
                    self.ckd_stage = CKDStage.STAGE3B
                elif 15 <= self.egfr < 30:
                    self.ckd_stage = CKDStage.STAGE4
                elif self.egfr < 15:
                    self.ckd_stage = CKDStage.STAGE5
                else:
                    self.ckd_stage = CKDStage.NONE
        
        # Convert HbA1c between % and mmol/mol if only one is provided
        if hasattr(self, 'hba1c_percent') and self.hba1c_percent is not None:
            if not hasattr(self, 'hba1c_mmol_mol') or self.hba1c_mmol_mol is None:
                self.hba1c_mmol_mol = round((self.hba1c_percent - 2.15) * 10.929, 1)
        elif hasattr(self, 'hba1c_mmol_mol') and self.hba1c_mmol_mol is not None:
            if not hasattr(self, 'hba1c_percent') or self.hba1c_percent is None:
                self.hba1c_percent = round((self.hba1c_mmol_mol * 0.0915) + 2.15, 1)
        
        # Update timestamp
        self.updated_at = datetime.utcnow()
        
        return self
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat(),
        }

class PatientCreate(PatientBase):
    pass

class PatientUpdate(PatientBase):
    pass

class PatientInDB(PatientBase):
    id: str  # UUID
    
    class Config:
        orm_mode = True

# Example usage:
# patient = Patient(
#     first_name="John",
#     last_name="Doe",
#     date_of_birth="1980-01-15",
#     sex=Sex.MALE,
#     nhs_number="1234567890",
#     consent_given=True,
#     consent_date="2023-01-01",
#     height_cm=175.0,
#     weight_kg=80.0,
#     bp_systolic=120,
#     bp_diastolic=80,
#     diabetes_type=DiabetesType.TYPE2,
#     diagnosis_date="2020-05-15",
#     smoking_status=SmokingStatus.NEVER,
#     alcohol_units_week=5,
#     activity_level=ActivityLevel.MODERATE,
#     diet_pattern=DietPattern.MEDITERRANEAN,
#     hba1c_percent=7.5,
#     total_cholesterol=5.2,
#     ldl_mmol=3.0,
#     hdl_mmol=1.2,
#     triglycerides=1.8,
#     egfr=85.0,
#     acr=2.5,
#     last_retinal_screen="2023-01-15",
#     last_foot_screen="2023-01-15",
#     last_renal_screen="2023-01-15",
#     consultant_notes="Patient doing well on current regimen.",
# )
