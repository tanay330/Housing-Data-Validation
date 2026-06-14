from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# ── Validation Rule Schemas ───────────────────────────────
class ValidationRuleResponse(BaseModel):
    id: int
    column_name: str
    rule_type: str
    rule_value: str
    error_message: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Validation Job Schemas ────────────────────────────────
class ValidationJobResponse(BaseModel):
    id: int
    file_name: str
    file_path: str
    status: str
    total_rows: int
    valid_rows: int
    error_rows: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Error Record Schemas ──────────────────────────────────
class ErrorRecordResponse(BaseModel):
    id: int
    job_id: int
    row_number: int
    column_name: str
    error_message: str
    raw_value: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Upload Response Schema ────────────────────────────────
class UploadResponse(BaseModel):
    message: str
    job_id: int
    file_name: str
    status: str


# ── Status Response Schema ────────────────────────────────
class StatusResponse(BaseModel):
    id: int
    file_name: str
    file_path:str
    status: str
    total_rows: int
    valid_rows: int
    error_rows: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes=True


# ── Error Report Schema ───────────────────────────────────
class ErrorReportResponse(BaseModel):
    job_id: int
    total_errors: int
    errors: List[ErrorRecordResponse]