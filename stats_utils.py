import pandas as pd
import numpy as np
import math
from scipy.stats import spearmanr
from pandas.api.types import (
    is_numeric_dtype, is_bool_dtype, is_categorical_dtype, is_object_dtype, is_string_dtype
)


_IDENTIFIER_TOKENS = ("id", "uuid", "guid", "key", "code", "identifier")

def safe_float(v):
    """Convert a value to a JSON-safe float, or None if NaN."""
    # Genuinely have no clue what this is supposed to do
    if v is None or pd.isna(v):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError, OverflowError):
        return None
    return None if math.isnan(f) else round(f, 5)
    

def is_identifier(series, name=None, unique_ratio_threshold=0.95):
    s = series
    n = s.notna().sum()
    if n == 0:
        return True
    
    # Heuristic 1: name-based rules
    if name is not None:
        name_lower = name.casefold()
        if any(tok in name_lower for tok in _IDENTIFIER_TOKENS):
            return True
        
    # Heuristic 2: uniqueness ratio
    unique_ratio = s.nunique(dropna=True) / n
    return unique_ratio >= unique_ratio_threshold


def classify_columns(df, categoric_threshold=5, categoric_ratio=0.05):
    numeric_cols = []
    categoric_cols = []
    skipped_cols = []

    for col, s in df.items():
        if is_identifier(s, col):
            skipped_cols.append(col)
            continue

        if is_bool_dtype(s):
            categoric_cols.append(col)
            continue

        if is_numeric_dtype(s):
            # Heuristic: if very few distinct values, is maybe categorical
            # Heuristic: if values are often repeated, is maybe categorical
            n = s.notna().sum()
            if n == 0:
                skipped_cols.append(col)
                continue

            nunique = s.nunique(dropna=True)
            ratio = nunique / n

            if nunique < categoric_threshold and ratio < categoric_ratio:
                categoric_cols.append(col)
            else:
                numeric_cols.append(col)

        elif is_categorical_dtype(s) or is_object_dtype(s) or is_string_dtype(s):
            categoric_cols.append(col)

        else:
            categoric_cols.append(col)

    return numeric_cols, categoric_cols, skipped_cols

    
def spearman(x, y) -> float:
    # print("---Computing Spearman's Rho...")
    x = pd.to_numeric(x, errors="coerce").to_numpy(dtype=float, copy=False)
    y = pd.to_numeric(y, errors="coerce").to_numpy(dtype=float, copy=False)

    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 2:
        return np.nan
    
    return spearmanr(x[mask], y[mask]).correlation


def eta(x, y) -> float:
    # print("---Computing Eta...")
    # IMPORTANT: assumes x is categorical, and y is numerical
    x = pd.Series(x, copy=False)
    y = pd.to_numeric(y, errors="coerce")

    mask = x.notna() & y.notna()
    if mask.sum() < 2:
        return np.nan

    x = x[mask]
    y = y[mask].to_numpy(dtype=float, copy=False)

    codes, _ = pd.factorize(x, sort=False)
    counts = np.bincount(codes)
    sums = np.bincount(codes, weights=y)
    means = sums / counts

    grand_mean = y.mean()
    ss_between = np.sum(counts * (means - grand_mean) ** 2)
    ss_total = np.sum((y - grand_mean) ** 2)

    return np.nan if ss_total == 0 else np.sqrt(ss_between / ss_total)
    

def cramers_v(x, y) -> float:
    # print("---Computing Cramer's V...")
    x = pd.Series(x, copy=False)
    y = pd.Series(y, copy=False)

    mask = x.notna() & y.notna()
    if mask.sum() < 2:
        return np.nan

    x_codes, _ = pd.factorize(x[mask], sort=False)
    y_codes, _ = pd.factorize(y[mask], sort=False)

    r = x_codes.max() + 1
    k = y_codes.max() + 1

    table = np.zeros((r, k), dtype=np.int64)
    np.add.at(table, (x_codes, y_codes), 1)

    n = table.sum()
    if n <= 1:
        return np.nan

    row_sums = table.sum(axis=1, keepdims=True)
    col_sums = table.sum(axis=0, keepdims=True)
    expected = (row_sums @ col_sums) / n

    with np.errstate(divide="ignore", invalid="ignore"):
        chi2 = np.nansum((table - expected) ** 2 / expected)

    phi2 = chi2 / n
    phi2corr = max(0.0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
    rcorr = r - ((r - 1) ** 2) / (n - 1)
    kcorr = k - ((k - 1) ** 2) / (n - 1)

    denom = min(kcorr - 1, rcorr - 1)
    return 0.0 if denom <= 0 else np.sqrt(phi2corr / denom)


def prepare_frame(df):
    numeric_cols, categoric_cols, skipped_cols = classify_columns(df)

    column_types = {}
    for col in df.columns:
        if col in skipped_cols:
            column_types[col] = "skipped"
        elif col in numeric_cols:
            column_types[col] = "numeric"
        else:
            column_types[col] = "categorical"

    numeric_data = pd.DataFrame({
        col: pd.to_numeric(df[col], errors="coerce") for col in numeric_cols
    })

    categoric_data = pd.DataFrame({
        col: df[col] for col in categoric_cols
    })

    return {
        "columns": df.columns.tolist(),
        "column_types": column_types,
        "numeric_cols": numeric_cols,
        "categoric_cols": categoric_cols,
        "skipped_cols": skipped_cols,
        "numeric_data": numeric_data,
        "categoric_data": categoric_data,
        "df": df,
    }


if __name__ == "__main__":
    df = pd.read_csv("student_data.csv")
    x_label = "primary_language"
    y_label = "work_mode"

    x = df[x_label]
    y = df[y_label]

