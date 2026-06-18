from __future__ import annotations

import importlib
from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture
def api_module(tmp_path, monkeypatch):
    api_server = importlib.import_module("frontend.api_server")
    monkeypatch.setattr(api_server, "DATA_DIR", tmp_path)

    pd.DataFrame(
        [
            {"Victim_ID": 1, "NID": "NID0001", "Name": "Rahim", "Upazila": "Sylhet", "Vulnerability_Score": 88.5, "Allocated_Fund_BDT": 12000, "Traditional_Equal_BDT": 10000, "Verification_Status": "Verified", "Water_Depth_ft": 8.0, "Duration_Days": 10, "Distance_km": 3.2, "House_Type": 1, "Poverty_Index": 0.7, "MFS_Account": "01700000001"},
            {"Victim_ID": 2, "NID": "NID0002", "Name": "Karim", "Upazila": "Sunamganj", "Vulnerability_Score": 76.25, "Allocated_Fund_BDT": 9000, "Traditional_Equal_BDT": 10000, "Verification_Status": "Verified", "Water_Depth_ft": 6.5, "Duration_Days": 8, "Distance_km": 4.1, "House_Type": 2, "Poverty_Index": 0.55, "MFS_Account": "01700000002"},
        ]
    ).to_csv(tmp_path / "fund_allocation.csv", index=False)

    pd.DataFrame(
        [
            {"Victim_ID": 1, "NID": "NID0001", "Name": "Rahim", "Upazila": "Sylhet", "Vulnerability_Score": 88.5, "Allocated_Fund_BDT": 12000, "Verification_Status": "Verified"},
            {"Victim_ID": 2, "NID": "NID0002", "Name": "Karim", "Upazila": "Sunamganj", "Vulnerability_Score": 76.25, "Allocated_Fund_BDT": 9000, "Verification_Status": "Verified"},
        ]
    ).to_csv(tmp_path / "verified_victims.csv", index=False)

    pd.DataFrame(
        [
            {"NID": "NID0001", "ReceiptID": "FRD-2026-0001", "TxHash": "0xabc", "Amount_BDT": 12000},
        ]
    ).to_csv(tmp_path / "receipts.csv", index=False)

    pd.DataFrame(
        [{"Criterion": "Water_Depth", "Weight": 0.3185}, {"Criterion": "Poverty_Index", "Weight": 0.3822}]
    ).to_csv(tmp_path / "fuzzy_ahp_weights.csv", index=False)

    pd.DataFrame(
        [
            {"Victim_ID": 1, "NID": "NID0001", "Name": "Rahim", "Upazila": "Sylhet", "Vulnerability_Score": 88.5, "Allocated_Fund_BDT": 12000, "Traditional_Equal_BDT": 10000, "Verification_Status": "Verified"},
            {"Victim_ID": 2, "NID": "NID0002", "Name": "Karim", "Upazila": "Sunamganj", "Vulnerability_Score": 76.25, "Allocated_Fund_BDT": 9000, "Traditional_Equal_BDT": 10000, "Verification_Status": "Verified"},
        ]
    ).to_csv(tmp_path / "rejected_entries.csv", index=False)

    pd.DataFrame(
        [
            {"Timestamp": "2026-06-17 10:00:00", "Mobile": "+8801700000001", "Message": "ok", "Status": "SIMULATED", "Response": ""},
        ]
    ).to_csv(tmp_path / "sms_log.csv", index=False)

    pd.DataFrame(
        [
            {"NID": "NID0001", "Water_Depth_ft": 8.0, "Duration_Days": 10, "Distance_km": 3.2},
            {"NID": "NID0002", "Water_Depth_ft": 6.5, "Duration_Days": 8, "Distance_km": 4.1},
        ]
    ).to_csv(tmp_path / "volunteer_input.csv", index=False)

    return api_server


def test_summary_endpoint(api_module):
    client = api_module.app.test_client()
    response = client.get("/api/summary")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["total_submissions"] == 2
    assert payload["verified"] == 2
    assert payload["receipts"] == 1
    assert payload["total_allocated_bdt"] == 21000.0


def test_victim_lookup_endpoint(api_module):
    client = api_module.app.test_client()
    response = client.get("/api/victim?nid=NID0001")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["found"] is True
    assert payload["stage"] == "Disbursed"
    assert payload["receipt_id"] == "FRD-2026-0001"
    assert payload["allocated_fund_bdt"] == 12000.0


def test_victims_and_weights_endpoints(api_module):
    client = api_module.app.test_client()

    victims_response = client.get("/api/victims")
    weights_response = client.get("/api/weights")

    assert victims_response.status_code == 200
    assert len(victims_response.get_json()) == 2

    assert weights_response.status_code == 200
    weights = weights_response.get_json()
    assert len(weights) == 2
    assert weights[0]["Criterion"] == "Water_Depth"