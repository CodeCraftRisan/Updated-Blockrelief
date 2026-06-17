from __future__ import annotations

from pathlib import Path
from typing import Iterable
import pandas as pd

class DataValidationError(ValueError):
    pass

def load_csv_safely(path: str | Path, required_columns: Iterable[str] | None = None) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise DataValidationError(f"Missing file: {path}")
    df = pd.read_csv(path)
    if required_columns:
        ensure_columns(df, required_columns, path.name)
    return df

def ensure_columns(df: pd.DataFrame, required_columns: Iterable[str], label: str = "DataFrame") -> None:
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise DataValidationError(f"{label} is missing required columns: {missing}")

def ensure_no_duplicates(df: pd.DataFrame, column: str, label: str = "DataFrame") -> None:
    if df[column].duplicated().any():
        dupes = df.loc[df[column].duplicated(), column].astype(str).tolist()[:10]
        raise DataValidationError(f"{label} contains duplicate values in '{column}': {dupes}")