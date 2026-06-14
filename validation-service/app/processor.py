import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime
from app.models import ValidationJob, ErrorRecord, ValidationRule
from app.validator import build_pandera_schema, validate_chunk
from app.s3 import save_parquet_locally

CHUNK_SIZE = 5000

def process_csv(job_id: int, file_path: str, db: Session):
    job = db.query(ValidationJob).filter(ValidationJob.id == job_id).first()
    if not job:
        return

    try:
        # ── Step 1: Update job status to processing ──────────
        job.status = "processing"
        db.commit()

        # ── Step 2: Fetch active validation rules ─────────────
        rules = db.query(ValidationRule).filter(
            ValidationRule.is_active == True
        ).all()

        if not rules:
            job.status = "failed"
            db.commit()
            return

        # ── Step 3: Build Pandera schema from rules ───────────
        schema = build_pandera_schema(rules)

        # ── Step 4: Process CSV in chunks ─────────────────────
        all_valid_rows = []
        all_error_records = []
        total_rows = 0

        for chunk in pd.read_csv(file_path, chunksize=CHUNK_SIZE, dtype=str):
            chunk = chunk.fillna("")
            total_rows += len(chunk)

            valid_rows, error_records = validate_chunk(chunk, schema)

            all_valid_rows.extend(valid_rows)
            all_error_records.extend(error_records)

        # ── Step 5: Save error records to database ────────────
        for error in all_error_records:
            error_record = ErrorRecord(
                job_id=job_id,
                row_number=error["row_number"],
                column_name=error["column_name"],
                error_message=error["error_message"],
                raw_value=error["raw_value"]
            )
            db.add(error_record)

        # ── Step 6: Save valid rows as Parquet ────────────────
        if all_valid_rows:
            valid_df = pd.DataFrame(all_valid_rows)
            save_parquet_locally(valid_df, job_id)

        # ── Step 7: Update job with final counts ──────────────
        job.status = "completed"
        job.total_rows = total_rows
        job.valid_rows = total_rows - len(all_error_records)
        job.error_rows = len(all_error_records)
        job.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        job.status = "failed"
        db.commit()
        raise e