from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

# ── Table 1 ──────────────────────────────────────────────
class ValidationRule(Base):
    __tablename__ = "validation_rules"

    id = Column(Integer, primary_key=True, index=True)
    column_name = Column(String, nullable=False)
    rule_type = Column(String, nullable=False)
    rule_value = Column(String, nullable=False)
    error_message = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ── Table 2 ──────────────────────────────────────────────
class ValidationJob(Base):
    __tablename__ = "validation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    status = Column(String, default="pending")
    total_rows = Column(Integer, default=0)
    valid_rows = Column(Integer, default=0)
    error_rows = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    errors = relationship("ErrorRecord", back_populates="job")


# ── Table 3 ──────────────────────────────────────────────
class ErrorRecord(Base):
    __tablename__ = "error_records"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("validation_jobs.id"), nullable=False)
    row_number = Column(Integer, nullable=False)
    column_name = Column(String, nullable=False)
    error_message = Column(String, nullable=False)
    raw_value = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("ValidationJob", back_populates="errors")