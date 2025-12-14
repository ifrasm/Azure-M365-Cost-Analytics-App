"""
Helpers to call Microsoft Graph using client credentials.

This module provides a simple helper to request Graph report endpoints
using the service principal credentials from environment variables.

Permissions required (app role):
- Reports.Read.All (for reports endpoints)
- Billing.Read.All (if billing endpoints are used)

Note: Some billing/cost data for Microsoft 365 may require partner/commerce APIs
or tenant billing access beyond Graph. Use this helper to fetch reports and
then aggregate costs in the app.
"""
import os
from typing import Dict, Any
import requests
import pandas as pd

try:
    from azure.identity import ClientSecretCredential
except Exception:
    ClientSecretCredential = None


def _get_graph_token():
    if ClientSecretCredential is None:
        raise RuntimeError("azure-identity not installed; install to use Graph integration")

    tenant_id = os.getenv("AZ_TENANT_ID")
    client_id = os.getenv("AZ_CLIENT_ID")
    client_secret = os.getenv("AZ_CLIENT_SECRET")
    if not all([tenant_id, client_id, client_secret]):
        raise ValueError("Missing AZ_TENANT_ID, AZ_CLIENT_ID or AZ_CLIENT_SECRET for Graph access")

    cred = ClientSecretCredential(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)
    token = cred.get_token("https://graph.microsoft.com/.default")
    return token.token


def fetch_graph_report(report_endpoint: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Call a Microsoft Graph report endpoint and return parsed JSON or CSV.

    Example `report_endpoint`: "https://graph.microsoft.com/v1.0/reports/getEmailActivityUserDetail(period='D30')"
    For CSV responses, this function will attempt to parse into a DataFrame.
    """
    token = _get_graph_token()
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(report_endpoint, headers=headers, params=params)
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "")
    if "text/csv" in content_type or resp.text.strip().startswith("Report refresh date"):
        # Try to parse CSV into DataFrame
        df = pd.read_csv(pd.compat.StringIO(resp.text)) if hasattr(pd, 'compat') else pd.read_csv(pd.io.common.StringIO(resp.text))
        return {"rows": df.to_dict(orient="records"), "columns": list(df.columns)}

    return resp.json()
