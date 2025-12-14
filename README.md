# Azure M365 Cost Analytics (local prototype)

Simple prototype to upload Excel exports and visualize monthly/quarterly costs.

Getting started (local):

1. Create a virtualenv and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the app:

```bash
uvicorn app.main:app --reload --port 8000
```

3. Open http://localhost:8000 and upload an Excel file with date and cost columns.

Docker:

```bash
docker build -t m365-cost-analytics .
docker run -p 8000:8000 m365-cost-analytics
```

Azure integration:

- The file `app/azure_client.py` contains a stub and guidance to implement
  calls to Azure Cost Management using `azure-identity` and
  `azure-mgmt-costmanagement` packages.

Azure Cost Management integration
--------------------------------

This prototype supports service-principal based queries to Azure Cost Management.
Set these environment variables (do NOT commit them):

```bash
export AZ_TENANT_ID=<tenant-id>
export AZ_CLIENT_ID=<client-id>
export AZ_CLIENT_SECRET=<client-secret>
export AZ_SUBSCRIPTION_ID=<subscription-id>
```

Then call the endpoint to fetch aggregated costs (example: monthly/quarterly):

```bash
curl 'http://localhost:8000/azure-costs?start_date=2025-01-01&end_date=2025-12-31'
```

The app uses `azure-identity` to acquire a token and the Cost Management REST API
to query usage data. The results are returned as JSON with `monthly` and `quarterly` arrays.

Microsoft 365 reports
--------------------

You can use the `/m365-report` endpoint to fetch Microsoft Graph reports. Example:

```bash
curl "http://localhost:8000/m365-report?endpoint=https://graph.microsoft.com/v1.0/reports/getEmailActivityUserDetail(period='D30')"
```

Note: The app uses the same service-principal credentials as for Azure and requires
`Reports.Read.All` (app) permissions. Some billing/cost data for M365 may not be
available through Graph and could require partner or commerce APIs.

Next steps:
- Implement Azure AD auth (FastAPI + MSAL or azure-identity)
- Implement Azure Cost Management queries and M365 data extraction
- Add user-friendly filters and export features
Deploying static UI to GitHub Pages
---------------------------------

If you only need the frontend (static visualization) available on GitHub Pages, the repo contains a GitHub Action that publishes the `static/` folder to GitHub Pages automatically on pushes to `main`.

Notes:
- The static site uses sample data when a backend is not available, so charts will render on GitHub Pages.
- Backend endpoints (`/import-excel`, `/azure-costs`, `/m365-report`) require the FastAPI server; those will not work from GitHub Pages unless you host the API and update the frontend to point to its URL.

To enable GitHub Pages after the first push to `main`:
1. In the repository Settings → Pages, ensure the source is set to `gh-pages` branch (the action will create/update it).
2. After the workflow runs, the site will be available at `https://<your-org-or-user>.github.io/<repo>`.

You can customize the sample displayed at `static/sample-data.json`.
# Azure-M365-Cost-Analytics-App
Azure-M365-Cost-Analytics-App
