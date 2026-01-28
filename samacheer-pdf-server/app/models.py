from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional
from datetime import datetime

class PDFRequest(BaseModel):
    """Request model for PDF generation"""
    
    class_num: int = Field(
        ..., 
        ge=6, 
        le=12, 
        description="Class number (6-12)"
    )
    
    subject: str = Field(
        ..., 
        description="Subject name (e.g., english, tamil, maths, socialscience)"
    )
    
    # 👇 NEW FIELD ADDED HERE
    discipline: Optional[str] = Field(
        None,
        description="Discipline for Social Science (history, geography, civics, economics)"
    )
    
    term: Optional[int] = Field(
        0, 
        ge=0, 
        le=3, 
        description="Term number (0=full year, 1-3 for classes 6-7)"
    )
    
    medium: Optional[Literal["english", "tamil"]] = Field(
        "english",
        description="Medium of instruction"
    )
    
    mode: Literal["full_book", "lesson"] = Field(
        "full_book",
        description="Download mode"
    )
    
    unit: Optional[int] = Field(
        None,
        ge=1,
        le=30,  # Increased limit for Science/History having many units
        description="Unit number (required if mode=lesson)"
    )
    
    lesson_choice: Optional[int] = Field(
        None,
        ge=1,
        description="Lesson choice number (required if mode=lesson)"
    )
    
    output_format: Literal["pdf", "txt", "md", "html"] = Field(
        "pdf",
        description="Output format: pdf, txt, md (markdown), or html"
    )
    
    @field_validator('subject')
    @classmethod
    def subject_lowercase(cls, v: str) -> str:
        """Convert subject to lowercase"""
        return v.lower().strip()
    
    @field_validator('term')
    @classmethod
    def validate_term(cls, v: int, info) -> int:
        """Auto-adjust term for classes 8-12"""
        class_num = info.data.get('class_num')
        if class_num and class_num >= 8:
            return 0
        return v
    
    @field_validator('unit', 'lesson_choice')
    @classmethod
    def validate_lesson_params(cls, v, info):
        """Ensure unit and lesson_choice are provided when mode=lesson"""
        mode = info.data.get('mode')
        # We relax this check slightly because 'lesson_choice' is not needed for Social Science
        if mode == 'lesson' and info.field_name == 'unit' and v is None:
            raise ValueError(f"{info.field_name} is required when mode='lesson'")
        return v


class FileInfo(BaseModel):
    """File information model"""
    filename: str
    file_path: str
    file_size_bytes: int
    file_size_mb: float
    download_url: str
    created_at: datetime


class PDFResponse(BaseModel):
    """Success response model"""
    status: Literal["success"]
    message: str
    request_details: dict
    file_info: FileInfo


class ErrorResponse(BaseModel):
    """Error response model"""
    status: Literal["error"]
    message: str
    error_code: str
    details: Optional[dict] = None


class HealthResponse(BaseModel):
    """Health check response"""
    service: str
    status: str
    version: str
    timestamp: datetime