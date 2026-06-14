import pandas as pd
import pandera as pa
from pandera import DataFrameSchema, Column, Check
from typing import List
from app.models import ValidationRule
import re


def build_pandera_schema(rules: List[ValidationRule]) -> DataFrameSchema:
    columns = {}

    for rule in rules:
        col_name = rule.column_name
        rule_type = rule.rule_type
        rule_value = rule.rule_value
        error_msg = rule.error_message

        check = None

        if rule_type == "not_null":
            def make_not_null_check(msg):
                return Check(
                    lambda x, m=msg: x is not None
                    and str(x).strip() != "" 
                    and str(x).lower() != "none"
                    and str(x).lower() != "nan"
                    and str(x).lower() != "nat",
                    element_wise=True,
                    error=msg
                )
            check = make_not_null_check(error_msg)

        elif rule_type == "greater_than":
            def make_gt_check(threshold, msg):
                def gt_check(x):
                    try:
                        return float(x) > threshold
                    except (ValueError, TypeError):
                        return False
                return Check(gt_check, element_wise=True, error=msg)
            check = make_gt_check(float(rule_value), error_msg)

        elif rule_type == "less_than":
            def make_lt_check(threshold, msg):
                def lt_check(x):
                    try:
                        return float(x) < threshold
                    except (ValueError, TypeError):
                        return False
                return Check(lt_check, element_wise=True, error=msg)
            check = make_lt_check(float(rule_value), error_msg)

        elif rule_type == "regex":
            def make_regex_check(pattern, msg):
                def regex_check(x):
                    if x is None or str(x).strip() == "":
                        return False
                    return bool(re.match(pattern, str(x).strip()))
                return Check(regex_check, element_wise=True, error=msg)
            check = make_regex_check(rule_value, error_msg)

        elif rule_type == "allowed_values":
            def make_allowed_check(allowed_list, msg):
                def allowed_check(x):
                    if x is None or str(x).strip() == "":
                        return False
                    return str(x).strip() in allowed_list
                return Check(allowed_check, element_wise=True, error=msg)
            allowed = [v.strip() for v in rule_value.split(",")]
            check = make_allowed_check(allowed, error_msg)

        if check is not None:
            if col_name in columns:
                columns[col_name] = Column(
                    nullable=True,
                    checks=columns[col_name].checks + [check],
                    required=False
                )
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

        failed_indices = set()
        for _, row in error_df.iterrows():
            row_index = row.get("index")
            if row_index is not None and not pd.isna(row_index):
                failed_indices.add(int(row_index))
                error_records.append({
                    "row_number": int(row_index) + 2,
                    "column_name": str(row.get("column", "")),
                    "error_message": str(row.get("check", "")),
                    "raw_value": str(row.get("failure_case", ""))
                })

        valid_df = df.drop(index=list(failed_indices), errors="ignore")
        valid_rows = valid_df.to_dict(orient="records")

    return valid_rows, error_records