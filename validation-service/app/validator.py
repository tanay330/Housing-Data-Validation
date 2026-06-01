import pandas as pd
import pandera as pa
from pandera import Column, DataFrameSchema, Check
from typing import List
from app.models import ValidationRule


def build_pandera_schema(rules: List[ValidationRule]) -> DataFrameSchema:
    columns = {}

    for rule in rules:
        col_name = rule.column_name
        rule_type = rule.rule_type
        rule_value = rule.rule_value
        error_msg = rule.error_message

        # Build check based on rule type
        check = None

        if rule_type == "not_null":
            check = Check.notna(error=error_msg)

        elif rule_type == "greater_than":
            check = Check.greater_than(float(rule_value), error=error_msg)

        elif rule_type == "less_than":
            check = Check.less_than(float(rule_value), error=error_msg)

        elif rule_type == "regex":
            check = Check.str_matches(rule_value, error=error_msg)

        elif rule_type == "allowed_values":
            allowed = rule_value.split(",")
            check = Check.isin(allowed, error=error_msg)

        if check is not None:
            if col_name in columns:
                columns[col_name].checks.append(check)
            else:
                columns[col_name] = Column(
                    nullable=True,
                    checks=[check],
                    required=False
                )

    return DataFrameSchema(columns, strict=False)


def validate_chunk(df: pd.DataFrame, schema: DataFrameSchema):
    valid_rows = []
    error_records = []

    try:
        schema.validate(df, lazy=True)
        valid_rows = df.to_dict(orient="records")

    except pa.errors.SchemaErrors as err:
        error_df = err.failure_cases

        failed_indices = set(error_df["index"].dropna().astype(int).tolist())

        for _, row in error_df.iterrows():
            row_index = row.get("index")
            if pd.isna(row_index):
                continue
            error_records.append({
                "row_number": int(row_index) + 2,
                "column_name": str(row.get("column", "")),
                "error_message": str(row.get("check", "")),
                "raw_value": str(row.get("failure_case", ""))
            })

        valid_df = df.drop(index=list(failed_indices), errors="ignore")
        valid_rows = valid_df.to_dict(orient="records")

    return valid_rows, error_records