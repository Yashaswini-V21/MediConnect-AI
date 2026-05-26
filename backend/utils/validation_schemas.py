"""
MediConnect-AI Request/Response Validation Schemas
Pydantic v2 models for type-safe API request validation
"""

from pydantic import BaseModel, Field, validator, EmailStr
from datetime import datetime
from typing import Optional, List
from enum import Enum


# ════════════════════════════════════════════════════════════════════════════════
# ENUMS
# ════════════════════════════════════════════════════════════════════════════════

class AppointmentStatusEnum(str, Enum):
    """Valid appointment statuses"""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class UrgencyLevelEnum(str, Enum):
    """Valid urgency levels"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AdminRoleEnum(str, Enum):
    """Valid admin roles"""
    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    HOSPITAL_ADMIN = "HOSPITAL_ADMIN"
    SUPPORT_STAFF = "SUPPORT_STAFF"


# ════════════════════════════════════════════════════════════════════════════════
# M3: APPOINTMENT REQUESTS
# ════════════════════════════════════════════════════════════════════════════════

class AppointmentBookRequest(BaseModel):
    """Validate appointment booking request"""
    hospital_id: int = Field(..., gt=0, description="Hospital ID must be positive")
    doctor_id: Optional[int] = Field(None, gt=0, description="Doctor ID if specific")
    appointment_date: datetime = Field(..., description="Future appointment date/time")
    reason: str = Field(..., min_length=5, max_length=500, description="Medical reason")
    urgency_level: UrgencyLevelEnum = Field(UrgencyLevelEnum.MEDIUM, description="Urgency level")

    @validator('appointment_date')
    def validate_future_date(cls, v):
        """Ensure appointment date is in the future"""
        if v <= datetime.utcnow():
            raise ValueError('Appointment date must be in the future')
        if (v - datetime.utcnow()).days > 365:
            raise ValueError('Cannot book appointments more than 365 days in advance')
        return v

    @validator('reason')
    def validate_reason(cls, v):
        """Sanitize reason text"""
        return v.strip()

    class Config:
        schema_extra = {
            "example": {
                "hospital_id": 1,
                "doctor_id": 5,
                "appointment_date": "2026-06-15T14:30:00",
                "reason": "Regular checkup for hypertension",
                "urgency_level": "MEDIUM"
            }
        }


class AppointmentStatusUpdateRequest(BaseModel):
    """Validate appointment status update"""
    status: AppointmentStatusEnum = Field(..., description="New appointment status")
    notes: Optional[str] = Field(None, max_length=1000, description="Optional admin notes")

    class Config:
        schema_extra = {
            "example": {
                "status": "CONFIRMED",
                "notes": "Patient confirmed via phone call"
            }
        }


# ════════════════════════════════════════════════════════════════════════════════
# M3: ADMIN REQUESTS
# ════════════════════════════════════════════════════════════════════════════════

class AdminUserCreateRequest(BaseModel):
    """Validate admin user creation"""
    email: EmailStr = Field(..., description="Valid email address")
    role: AdminRoleEnum = Field(..., description="Admin role")
    hospital_id: Optional[int] = Field(None, gt=0, description="Hospital ID for Hospital Admin")

    @validator('hospital_id')
    def validate_hospital_for_role(cls, v, values):
        """Hospital Admin must have hospital_id"""
        if values.get('role') == AdminRoleEnum.HOSPITAL_ADMIN and not v:
            raise ValueError('Hospital Admin must specify hospital_id')
        return v

    class Config:
        schema_extra = {
            "example": {
                "email": "admin@hospital.com",
                "role": "HOSPITAL_ADMIN",
                "hospital_id": 1
            }
        }


class DoctorCreateRequest(BaseModel):
    """Validate doctor creation"""
    hospital_id: int = Field(..., gt=0, description="Hospital ID")
    name: str = Field(..., min_length=3, max_length=200, description="Doctor name")
    specialty: str = Field(..., min_length=3, max_length=100, description="Medical specialty")
    degree: Optional[str] = Field(None, max_length=100, description="Medical degree")
    experience_years: int = Field(..., ge=0, le=70, description="Years of experience")

    @validator('name', 'specialty', 'degree')
    def sanitize_text(cls, v):
        """Sanitize text fields"""
        if v:
            return v.strip()
        return v

    class Config:
        schema_extra = {
            "example": {
                "hospital_id": 1,
                "name": "Dr. Rajesh Kumar",
                "specialty": "Cardiology",
                "degree": "MD, DM Cardiology",
                "experience_years": 15
            }
        }


# ════════════════════════════════════════════════════════════════════════════════
# M6: AI/SYMPTOM ANALYSIS REQUESTS
# ════════════════════════════════════════════════════════════════════════════════

class SymptomAnalysisRequest(BaseModel):
    """Validate symptom analysis request"""
    symptoms: str = Field(..., min_length=5, max_length=2000, description="Symptom description")
    language: str = Field("en", pattern="^(en|kn|hi|ta)$", description="Language code")

    @validator('symptoms')
    def validate_symptoms(cls, v):
        """Ensure symptoms contain meaningful text"""
        # Remove extra whitespace
        v = ' '.join(v.split())
        if len(v.split()) < 2:
            raise ValueError('Please provide at least 2 words describing symptoms')
        return v

    class Config:
        schema_extra = {
            "example": {
                "symptoms": "Chest pain and difficulty breathing for 2 days",
                "language": "en"
            }
        }


class HospitalSearchRequest(BaseModel):
    """Validate hospital search request"""
    specialties: List[str] = Field(..., min_items=1, description="Required specialties")
    location: dict = Field(..., description="Location {lat, lng}")
    urgency: UrgencyLevelEnum = Field(UrgencyLevelEnum.MEDIUM, description="Urgency level")
    max_distance_km: int = Field(50, gt=0, le=500, description="Max distance in km")

    @validator('location')
    def validate_location(cls, v):
        """Validate lat/lng"""
        if not isinstance(v, dict) or 'lat' not in v or 'lng' not in v:
            raise ValueError('Location must have lat and lng')
        lat, lng = v['lat'], v['lng']
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            raise ValueError('Invalid latitude/longitude')
        return v

    class Config:
        schema_extra = {
            "example": {
                "specialties": ["Cardiology", "Emergency Medicine"],
                "location": {"lat": 12.9716, "lng": 77.5946},
                "urgency": "HIGH",
                "max_distance_km": 25
            }
        }


# ════════════════════════════════════════════════════════════════════════════════
# M5: NOTIFICATION REQUESTS
# ════════════════════════════════════════════════════════════════════════════════

class NotificationSendRequest(BaseModel):
    """Validate notification send request"""
    user_id: str = Field(..., min_length=1, description="User ID")
    message: str = Field(..., min_length=5, max_length=1000, description="Notification message")
    send_email: bool = Field(False, description="Send email notification")
    send_sms: bool = Field(False, description="Send SMS notification")

    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "message": "Your appointment has been confirmed",
                "send_email": True,
                "send_sms": True
            }
        }


# ════════════════════════════════════════════════════════════════════════════════
# RESPONSE MODELS
# ════════════════════════════════════════════════════════════════════════════════

class AppointmentResponse(BaseModel):
    """Standard appointment response"""
    id: str
    user_id: str
    hospital_id: int
    doctor_id: Optional[int]
    appointment_date: datetime
    status: AppointmentStatusEnum
    urgency_level: UrgencyLevelEnum
    reason: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., pattern="^(healthy|unhealthy)$")
    database: str
    timestamp: datetime
    uptime_seconds: Optional[int] = None
    version: str = "2.0.0"


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[dict] = None

    class Config:
        schema_extra = {
            "example": {
                "error": "Invalid appointment date",
                "code": "VALIDATION_ERROR",
                "details": {"field": "appointment_date", "reason": "Must be in future"}
            }
        }


class PaginatedResponse(BaseModel):
    """Standard paginated response"""
    items: List[dict] = Field(..., description="Page items")
    total: int = Field(..., ge=0, description="Total count")
    page: int = Field(..., ge=1, description="Current page")
    per_page: int = Field(..., ge=1, description="Items per page")
    has_next: bool
    has_prev: bool
    total_pages: int


# ════════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════════

def validate_request(request_data: dict, schema_class):
    """
    Validate request data against a Pydantic schema.
    
    Args:
        request_data: Raw request data (dict or JSON)
        schema_class: Pydantic model class
    
    Returns:
        Validated model instance
    
    Raises:
        ValidationError: If validation fails
    """
    try:
        return schema_class(**request_data)
    except Exception as e:
        raise ValueError(f"Validation failed: {str(e)}")


def error_response(error_msg: str, code: str = "ERROR", details: dict = None) -> dict:
    """
    Generate standard error response.
    
    Args:
        error_msg: Human-readable error message
        code: Error code for logging
        details: Additional error details
    
    Returns:
        Formatted error response dict
    """
    return ErrorResponse(
        error=error_msg,
        code=code,
        details=details
    ).dict()
