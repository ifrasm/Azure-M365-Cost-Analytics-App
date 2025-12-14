from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from io import BytesIO
import pandas as pd
from .utils import aggregate_costs_from_excel
from .azure_client import fetch_azure_costs
from .m365_client import fetch_graph_report

app = FastAPI(title="Azure M365 Cost Analytics - Backend")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.post("/import-excel")
async def import_excel(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="Only Excel files are supported")
    contents = await file.read()
    try:
        df = pd.read_excel(BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read Excel: {e}")

    result = aggregate_costs_from_excel(df)
    return JSONResponse(result)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/azure-costs")
async def azure_costs(start_date: str, end_date: str, subscription_id: str | None = None):
    """Fetch costs directly from Azure Cost Management for the given date range.

    Requires env vars: AZ_TENANT_ID, AZ_CLIENT_ID, AZ_CLIENT_SECRET, AZ_SUBSCRIPTION_ID (unless subscription_id provided).
    """
    try:
        result = fetch_azure_costs(start_date, end_date, subscription_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return JSONResponse(result)


@app.get("/m365-report")
async def m365_report(endpoint: str):
    """Proxy to fetch a Microsoft Graph report endpoint.

    Provide a fully formed Graph URL in `endpoint`, for example:
    `https://graph.microsoft.com/v1.0/reports/getEmailActivityUserDetail(period='D30')`
    """
    try:
        result = fetch_graph_report(endpoint)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return JSONResponse(result)
