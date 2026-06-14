import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ValidationJob, ErrorRecord, ValidationRule
from app.schemas import UploadResponse, StatusResponse, ErrorReportResponse, ValidationRuleResponse
from app.dependencies import verify_token
from app.s3 import save_file_locally
from app.processor import process_csv
from typing import List

router = APIRouter()


# ── Endpoint 1: Upload CSV ────────────────────────────────
@router.post("/upload", response_model=UploadResponse)
async def upload_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    email: str = Depends(verify_token)
):
    # Validate file type
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed"
        )

    # Read file content
    file_content = await file.read()

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}_{file.filename}"

    # Save file locally
    file_path = save_file_locally(file_content, unique_filename)

    # Create validation job in database
    job = ValidationJob(
        file_name=file.filename,
        file_path=file_path,
        status="pending"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Start background processing
    background_tasks.add_task(
        process_csv,
        job_id=job.id,
        file_path=file_path,
        db=db
    )

    return UploadResponse(
        message="File uploaded successfully. Validation started.",
        job_id=job.id,
        file_name=file.filename,
        status="pending"
    )


# ── Endpoint 2: Check Status ──────────────────────────────
@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(
    job_id: int,
    db: Session = Depends(get_db),
    email: str = Depends(verify_token)
):
    job = db.query(ValidationJob).filter(ValidationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    return job


# ── Endpoint 3: Get Error Report ──────────────────────────
@router.get("/errors/{job_id}", response_model=ErrorReportResponse)
async def get_errors(
    job_id: int,
    db: Session = Depends(get_db),
    email: str = Depends(verify_token)
):
    job = db.query(ValidationJob).filter(ValidationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    errors = db.query(ErrorRecord).filter(
        ErrorRecord.job_id == job_id
    ).all()

    return ErrorReportResponse(
        job_id=job_id,
        total_errors=len(errors),
        errors=errors
    )


# ── Endpoint 4: Get Validation Rules ─────────────────────
@router.get("/rules", response_model=List[ValidationRuleResponse])
async def get_rules(
    db: Session = Depends(get_db),
    email: str = Depends(verify_token)
):
    rules = db.query(ValidationRule).filter(
        ValidationRule.is_active == True
    ).all()
    return rules