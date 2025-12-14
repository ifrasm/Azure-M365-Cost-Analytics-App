import pandas as pd
from app.utils import aggregate_costs_from_excel


def test_aggregate_monthly_quarterly():
    data = {
        "UsageDate": ["2025-01-15", "2025-01-20", "2025-02-05", "2025-04-10"],
        "CostUSD": [10.0, 5.0, 20.0, 40.0],
    }
    df = pd.DataFrame(data)
    result = aggregate_costs_from_excel(df)

    monthly = {r["month"]: r["_cost"] for r in result["monthly"]}
    assert monthly["2025-01"] == 15.0
    assert monthly["2025-02"] == 20.0
    assert monthly["2025-04"] == 40.0

    quarterly = {r["quarter"]: r["_cost"] for r in result["quarterly"]}
    assert quarterly["2025Q1"] == 35.0
    assert quarterly["2025Q2"] == 40.0
