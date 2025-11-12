from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


@dataclass
class DatasetContext:
    dataframe: pd.DataFrame
    profile: dict


class DatasetStore:
    """In-memory cache keyed by session identifier."""

    _datasets: dict[str, DatasetContext] = {}

    @classmethod
    def set(cls, session_id: str, dataframe: pd.DataFrame, profile: dict) -> None:
        if not session_id:
            return
        cls._datasets[session_id] = DatasetContext(dataframe=dataframe, profile=profile)

    @classmethod
    def get(cls, session_id: Optional[str]) -> Optional[DatasetContext]:
        if session_id is None:
            return None
        return cls._datasets.get(session_id)


def load_dataframe(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError("Unsupported file type. Please upload CSV or Excel files.")


def profile_dataframe(df: pd.DataFrame) -> dict:
    summary = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_details": [],
    }

    for column in df.columns:
        series = df[column]
        dtype = str(series.dtype)
        missing = int(series.isna().sum())
        unique = int(series.nunique(dropna=True))
        col_info = {
            "name": column,
            "dtype": dtype,
            "missing": missing,
            "unique": unique,
        }

        if pd.api.types.is_numeric_dtype(series):
            col_info.update(
                mean=float(np.round(series.mean(), 4)) if not series.empty else None,
                median=float(np.round(series.median(), 4)) if not series.empty else None,
                min=float(np.round(series.min(), 4)) if not series.empty else None,
                max=float(np.round(series.max(), 4)) if not series.empty else None,
            )
        else:
            top_values = (
                series.value_counts(dropna=True).head(3).index.tolist()
                if not series.empty
                else []
            )
            col_info["top_values"] = [str(v) for v in top_values]

        summary["column_details"].append(col_info)

    return summary


def summary_to_text(profile: dict) -> str:
    header = f"Rows: {profile['rows']}, Columns: {profile['columns']}"
    lines = [header, "Columns:"]
    for col in profile["column_details"]:
        base = f"- {col['name']} ({col['dtype']})"
        if "mean" in col and col["mean"] is not None:
            base += f" | mean={col['mean']} median={col['median']}"
        if "top_values" in col and col["top_values"]:
            base += f" | top values: {', '.join(col['top_values'])}"
        if col["missing"]:
            base += f" | missing={col['missing']}"
        lines.append(base)
    return "\n".join(lines)


def find_column(question: str, df: pd.DataFrame) -> Optional[str]:
    lowered = question.lower()
    for column in df.columns:
        if column.lower() in lowered:
            return column
    tokens = re.findall(r"[a-zA-Z0-9_]+", lowered)
    for column in df.columns:
        col_tokens = set(re.findall(r"[a-zA-Z0-9_]+", column.lower()))
        if col_tokens.intersection(tokens):
            return column
    return None


def answer_dataset_question(question: str, context: DatasetContext) -> Optional[str]:
    df = context.dataframe
    profile = context.profile
    lower = question.lower()

    if any(kw in lower for kw in ["column names", "columns", "fields", "headers"]):
        cols = ", ".join(df.columns)
        return f"The dataset contains {len(df.columns)} columns: {cols}."

    if any(kw in lower for kw in ["row count", "rows", "records", "entries"]):
        return f"The dataset has {len(df)} rows and {len(df.columns)} columns."

    column = find_column(question, df)
    if column is None:
        if any(kw in lower for kw in ["summary", "describe", "overview", "profile"]):
            return summary_to_text(profile)
        return None

    series = df[column].dropna()

    if series.empty:
        return f"The column '{column}' has only missing values."

    is_numeric = pd.api.types.is_numeric_dtype(series)

    if any(kw in lower for kw in ["average", "mean"]):
        if is_numeric:
            return f"The average of '{column}' is {round(series.mean(), 4)}."
        return f"The column '{column}' is not numeric, so an average is not applicable."

    if any(kw in lower for kw in ["median"]):
        if is_numeric:
            return f"The median of '{column}' is {round(series.median(), 4)}."
        return f"The column '{column}' is not numeric, so a median is not applicable."

    if any(kw in lower for kw in ["sum", "total"]):
        if is_numeric:
            return f"The total of '{column}' is {round(series.sum(), 4)}."
        return f"The column '{column}' is not numeric, so a sum is not applicable."

    if any(kw in lower for kw in ["minimum", "min", "lowest"]):
        if is_numeric:
            return f"The minimum of '{column}' is {round(series.min(), 4)}."
        return f"'{column}' is not numeric; minimum is not computed."

    if any(kw in lower for kw in ["maximum", "max", "highest"]):
        if is_numeric:
            return f"The maximum of '{column}' is {round(series.max(), 4)}."
        return f"'{column}' is not numeric; maximum is not computed."

    if any(kw in lower for kw in ["unique", "distinct"]):
        unique_count = series.nunique()
        return f"'{column}' has {unique_count} unique values."

    if any(kw in lower for kw in ["missing", "null", "na", "empty"]):
        missing = df[column].isna().sum()
        return f"The column '{column}' has {missing} missing values."

    if any(kw in lower for kw in ["most common", "top value", "frequent"]):
        top = series.value_counts().head(3)
        formatted = ", ".join(f"{idx} ({count})" for idx, count in top.items())
        return f"The most common values in '{column}' are: {formatted}."

    return None
