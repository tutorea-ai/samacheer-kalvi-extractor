from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from datetime import datetime

from .models import (
    PDFRequest, 
    PDFResponse, 
    ErrorResponse,
    FileInfo
)
from .processor import processor
from .utils import get_file_size, generate_download_url, get_file_creation_time
from .config import settings

router = APIRouter()

@router.post(
    "/generate",
    response_model=PDFResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Generate PDF or TXT",
    description="Process request and generate PDF/TXT file from Samacheer Kalvi textbooks"
)
async def generate_pdf(request: PDFRequest):
    """
    Generate PDF or TXT file based on request parameters
    
    **Full Book Example:**
```json
    {
        "class_num": 12,
        "subject": "english",
        "mode": "full_book",
        "output_format": "pdf"
    }
```
    
    **Specific Lesson Example:**
```json
    {
        "class_num": 12,
        "subject": "english",
        "mode": "lesson",
        "unit": 6,
        "lesson_choice": 2,
        "output_format": "txt"
    }
```
    """
    
    # Convert Pydantic model to dict
    request_data = request.model_dump()
    
    # Process
    result = processor.process_request(request_data)
    
    # Handle errors
    if result.get("error"):
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": result["message"],
                "error_code": "PROCESSING_ERROR"
            }
        )
    
    # Get file info
    file_path = Path(result["file_path"])
    
    if not file_path.exists():
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "File was processed but not found",
                "error_code": "FILE_NOT_FOUND"
            }
        )
    
    # Build response
    size_info = get_file_size(file_path)
    
    file_info = FileInfo(
        filename=result["filename"],
        file_path=str(file_path),
        file_size_bytes=size_info["bytes"],
        file_size_mb=size_info["mb"],
        download_url=generate_download_url(result["filename"]),
        created_at=get_file_creation_time(file_path)
    )
    
    response = PDFResponse(
        status="success",
        message="File generated successfully",
        request_details={
            "class": request.class_num,
            "subject": request.subject,
            "mode": request.mode,
            "format": request.output_format
        },
        file_info=file_info
    )
    
    return response


@router.get(
    "/download/{filename}",
    response_class=FileResponse,
    summary="Download Generated File",
    description="Download the generated PDF or TXT file"
)
async def download_file(filename: str):
    """
    Download file from temp storage
    
    Example: GET /api/download/Class12-Unit6-Poem-IncidentoftheFrenchCamp.pdf
    """
    file_path = settings.TEMP_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail={
                "status": "error",
                "message": f"File not found: {filename}",
                "error_code": "FILE_NOT_FOUND"
            }
        )
    
    # Determine media type
    media_type = "application/pdf" if filename.endswith(".pdf") else "text/plain"
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )