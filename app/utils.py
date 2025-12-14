from typing import Dict, Any
import pandas as pd


def _find_column(df: pd.DataFrame, keywords):
    for col in df.columns:
        low = str(col).lower()
        for kw in keywords:
            if kw in low:
                return col
    return None


def aggregate_costs_from_excel(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty:
        return {"error": "empty file"}

    date_col = _find_column(df, ["date", "usage_date", "billingdate", "day"]) or df.columns[0]
    cost_col = _find_column(df, ["cost", "amount", "charge", "costusd", "charges"]) or _find_column(df, ["price"]) or df.columns[1]

    try:
        df["_parsed_date"] = pd.to_datetime(df[date_col])
    except Exception:
        df["_parsed_date"] = pd.to_datetime(df[date_col], errors="coerce")

    df = df.dropna(subset=["_parsed_date"]).copy()

    # Try to coerce cost to numeric
    df["_cost"] = pd.to_numeric(df[cost_col], errors="coerce").fillna(0.0)

    df["month"] = df["_parsed_date"].dt.to_period("M").astype(str)
    df["quarter"] = df["_parsed_date"].dt.to_period("Q").astype(str)

    monthly = df.groupby("month")["_cost"].sum().reset_index().to_dict(orient="records")
    quarterly = df.groupby("quarter")["_cost"].sum().reset_index().to_dict(orient="records")

    sample_rows = df.head(10).loc[:, [date_col, cost_col]].to_dict(orient="records")

    return {"monthly": monthly, "quarterly": quarterly, "sample": sample_rows}
