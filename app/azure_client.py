"""
Stubbed Azure integration helpers.

This file contains example helper functions and guidance for integrating
with Azure Cost Management and Microsoft 365 billing data. To enable
real extraction, install `azure-identity` and `azure-mgmt-costmanagement`
then implement the `fetch_azure_costs` function using your tenant
credentials.
"""
from typing import Dict, Any, Optional
import os
import requests
import pandas as pd

try:
    from azure.identity import ClientSecretCredential
except Exception:
    ClientSecretCredential = None


def fetch_azure_costs(start_date: str, end_date: str, subscription_id: Optional[str] = None) -> Dict[str, Any]:
    """Fetch cost data using Azure Cost Management REST API.

    This function uses a service principal from environment variables:
    `AZ_TENANT_ID`, `AZ_CLIENT_ID`, `AZ_CLIENT_SECRET`, and either
    `subscription_id` parameter or `AZ_SUBSCRIPTION_ID` env var.

    Returns a dict with `monthly` and `quarterly` aggregated totals.
    """
    if ClientSecretCredential is None:
        raise RuntimeError("azure-identity is not installed; install it to enable Azure integration")

    tenant_id = os.getenv("AZ_TENANT_ID")
    client_id = os.getenv("AZ_CLIENT_ID")
    client_secret = os.getenv("AZ_CLIENT_SECRET")
    sub = subscription_id or os.getenv("AZ_SUBSCRIPTION_ID")

    if not all([tenant_id, client_id, client_secret, sub]):
        raise ValueError("Missing one of AZ_TENANT_ID, AZ_CLIENT_ID, AZ_CLIENT_SECRET, AZ_SUBSCRIPTION_ID")

    cred = ClientSecretCredential(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)
    token = cred.get_token("https://management.azure.com/.default")
    access_token = token.token

    url = f"https://management.azure.com/subscriptions/{sub}/providers/Microsoft.CostManagement/query?api-version=2021-10-01"

    # Query: daily granularity for the provided date range; aggregation on PreTaxCost
    body = {
        "type": "Usage",
        "timeframe": "Custom",
        "timePeriod": {"from": start_date, "to": end_date},
        "dataset": {
            "granularity": "Daily",
            "aggregation": {"totalCost": {"name": "PreTaxCost", "function": "Sum"}},
        }
    }

    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    resp = requests.post(url, json=body, headers=headers)
    resp.raise_for_status()
    data = resp.json()

    props = data.get("properties", {})
    columns = [c.get("name") for c in props.get("columns", [])]
    rows = props.get("rows", [])

    # Build DataFrame
    if rows and columns:
        df = pd.DataFrame(rows, columns=columns)
    else:
        df = pd.DataFrame()

    # Normalize column names to find date/cost
    date_col = None
    cost_col = None
    for c in df.columns:
        lc = str(c).lower()
        if "date" in lc or "usage" in lc:
            date_col = c
        if "cost" in lc or "pre" in lc or "amount" in lc or "usage" in lc:
            cost_col = c

    if date_col is None and not df.empty:
        date_col = df.columns[0]
    if cost_col is None and df.shape[1] >= 2:
        cost_col = df.columns[1]

    if df.empty:
        return {"monthly": [], "quarterly": [], "raw": data}

    df["_parsed_date"] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=["_parsed_date"]).copy()
    df["_cost"] = pd.to_numeric(df[cost_col], errors="coerce").fillna(0.0)
    df["month"] = df["_parsed_date"].dt.to_period("M").astype(str)
    df["quarter"] = df["_parsed_date"].dt.to_period("Q").astype(str)

    monthly = df.groupby("month")["_cost"].sum().reset_index().to_dict(orient="records")
    quarterly = df.groupby("quarter")["_cost"].sum().reset_index().to_dict(orient="records")

    return {"monthly": monthly, "quarterly": quarterly}
