"""
============================================================
  Block-Relief : Flask API Bridge
  frontend/api_server.py  (or backend/api_server.py)
============================================================
  Frontend (React) --> This Flask API --> CSV data + Python logic

  চালু করো:
    pip install flask flask-cors pandas
    python api_server.py

  Default: http://127.0.0.1:5000
============================================================
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import os
import json
from pathlib import Path

app = Flask(__name__)
CORS(app)  # React frontend cross-origin allow করবে

# ---- Paths (config.py এর মতো) ----
BASE_DIR   = Path(__file__).resolve().parent.parent
DATA_DIR   = BASE_DIR / "data"

def read_csv(filename):
    path = DATA_DIR / filename
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()

# ============================================================
#   GET /api/summary  —  Admin overview stats
# ============================================================
@app.route('/api/summary')
def summary():
    try:
        verified   = read_csv('verified_victims.csv')
        rejected   = read_csv('rejected_entries.csv')
        volunteer  = read_csv('volunteer_input.csv')
        allocation = read_csv('fund_allocation.csv')
        receipts   = read_csv('receipts.csv')

        avg_score = 0.0
        if not allocation.empty and 'Vulnerability_Score' in allocation.columns:
            avg_score = float(allocation['Vulnerability_Score'].mean())

        total_allocated = 0
        if not allocation.empty and 'Allocated_Fund_BDT' in allocation.columns:
            total_allocated = float(allocation['Allocated_Fund_BDT'].sum())

        return jsonify({
            "total_submissions":    len(volunteer),
            "verified":             len(verified),
            "rejected":             len(rejected),
            "total_victims":        len(verified),
            "verification_rate":    round(len(verified) / max(len(volunteer), 1) * 100, 1),
            "avg_score":            round(avg_score, 2),
            "total_allocated_bdt":  total_allocated,
            "receipts":             len(receipts),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
#   GET /api/victim?nid=NID00091  —  Victim status lookup
# ============================================================
@app.route('/api/victim')
def victim_lookup():
    nid = request.args.get('nid', '').strip().upper()
    if not nid:
        return jsonify({"found": False, "error": "NID required"}), 400

    try:
        allocation = read_csv('fund_allocation.csv')
        receipts   = read_csv('receipts.csv')

        if allocation.empty:
            return jsonify({"found": False})

        # NID match
        row = allocation[allocation['NID'].astype(str).str.upper() == nid]
        if row.empty:
            return jsonify({"found": False})

        r = row.iloc[0]

        # Receipt check
        receipt = {}
        if not receipts.empty:
            rec_row = receipts[receipts['NID'].astype(str).str.upper() == nid]
            if not rec_row.empty:
                rec = rec_row.iloc[0]
                receipt = {
                    "receipt_id": str(rec.get('ReceiptID', '')),
                    "tx_hash":    str(rec.get('TxHash', '')),
                    "amount_bdt": float(rec.get('Amount_BDT', 0)),
                }

        # House type label
        house_map = {1: "Kutcha (Type 1)", 1.0: "Kutcha (Type 1)",
                     2: "Semi-pucca (Type 2)", 2.0: "Semi-pucca (Type 2)",
                     3: "Pucca (Type 3)", 3.0: "Pucca (Type 3)"}
        house_val = r.get('House_Type', 1)
        house_label = house_map.get(house_val, str(house_val))

        # Stage
        v_status = str(r.get('Verification_Status', 'Pending'))
        stage = "Disbursed" if receipt else ("Approved" if v_status == 'Verified' else v_status)

        return jsonify({
            "found":                  True,
            "nid":                    str(r.get('NID', nid)),
            "name":                   str(r.get('Name', 'Unknown')),
            "upazila":                str(r.get('Upazila', '—')),
            "mfs_account":            str(r.get('MFS_Account', '—')),
            "verification_status":    v_status,
            "vulnerability_score":    round(float(r.get('Vulnerability_Score', 0)), 2),
            "allocated_fund_bdt":     round(float(r.get('Allocated_Fund_BDT', 0)), 0),
            "traditional_equal_bdt":  round(float(r.get('Traditional_Equal_BDT', 0)), 0),
            "water_depth_ft":         float(r.get('Water_Depth_ft', 0)),
            "duration_days":          int(r.get('Duration_Days', 0)),
            "distance_km":            float(r.get('Distance_km', 0)),
            "house_type":             house_label,
            "poverty_index":          float(r.get('Poverty_Index', 0)),
            "stage":                  stage,
            **receipt,
        })
    except Exception as e:
        return jsonify({"found": False, "error": str(e)}), 500


# ============================================================
#   GET /api/victims  —  All victims list (Admin)
# ============================================================
@app.route('/api/victims')
def all_victims():
    try:
        df = read_csv('fund_allocation.csv')
        if df.empty:
            return jsonify([])
        cols = ['Victim_ID', 'NID', 'Name', 'Upazila', 'Vulnerability_Score',
                'Allocated_Fund_BDT', 'Verification_Status']
        cols = [c for c in cols if c in df.columns]
        return jsonify(df[cols].to_dict(orient='records'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
#   GET /api/donors  —  Donor activity (from receipts)
# ============================================================
@app.route('/api/receipts')
def receipts():
    try:
        df = read_csv('receipts.csv')
        if df.empty:
            return jsonify([])
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
#   GET /api/weights  —  Fuzzy AHP weights
# ============================================================
@app.route('/api/weights')
def weights():
    try:
        df = read_csv('fuzzy_ahp_weights.csv')
        if df.empty:
            return jsonify([])
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
#   GET /api/rejected  —  Fraud/rejected entries
# ============================================================
@app.route('/api/rejected')
def rejected():
    try:
        df = read_csv('rejected_entries.csv')
        if df.empty:
            return jsonify([])
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
#   GET /api/sms_log  —  SMS activity log
# ============================================================
@app.route('/api/sms_log')
def sms_log():
    try:
        df = read_csv('sms_log.csv')
        if df.empty:
            return jsonify([])
        # NaN → empty string করো (JSON NaN invalid)
        df = df.fillna('').astype(str)
        return jsonify(df.tail(50).to_dict(orient='records'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
#   GET /api/outcome_report  —  Demographic & Socio-Economic stats
# ============================================================
@app.route('/api/outcome_report')
def outcome_report():
    try:
        report_path = DATA_DIR / "distribution_outcome_report.md"
        report_md = ""
        if report_path.exists():
            with open(report_path, "r", encoding="utf-8") as f:
                report_md = f.read()

        demo_csv = DATA_DIR / "demographic_distribution.csv"
        if not demo_csv.exists():
            return jsonify({
                "report_md": report_md,
                "gender_stats": [],
                "housing_stats": [],
                "poverty_stats": [],
                "upazila_stats": [],
                "error": "Demographic distribution data not found. Run fairness_analysis.py first."
            })

        df = pd.read_csv(demo_csv)
        total_fund = float(df['Allocated_Fund_BDT'].sum())
        flat_share = float(df['Traditional_Equal_BDT'].iloc[0]) if not df.empty else 10000.0

        # Gender
        gender_grp = df.groupby('Gender').agg(
            Count=('Gender', 'count'),
            Avg_Score=('Vulnerability_Score', 'mean'),
            Avg_Fund_Fuzzy=('Allocated_Fund_BDT', 'mean'),
            Total_Fund_Fuzzy=('Allocated_Fund_BDT', 'sum')
        ).reset_index()
        gender_grp['Percentage_of_Pool'] = (gender_grp['Total_Fund_Fuzzy'] / total_fund * 100).round(1)
        gender_grp['Avg_Fund_Trad'] = flat_share
        gender_grp['Avg_Difference_Pct'] = ((gender_grp['Avg_Fund_Fuzzy'] - flat_share) / flat_share * 100).round(1)

        # Housing Class
        housing_grp = df.groupby('Housing_Class').agg(
            Count=('Housing_Class', 'count'),
            Avg_Score=('Vulnerability_Score', 'mean'),
            Avg_Fund_Fuzzy=('Allocated_Fund_BDT', 'mean'),
            Total_Fund_Fuzzy=('Allocated_Fund_BDT', 'sum')
        ).reset_index()
        # Sort Kutcha first, then Semi-pucca, then Pucca
        housing_grp['sort_order'] = housing_grp['Housing_Class'].map({"Kutcha": 0, "Semi-pucca": 1, "Pucca": 2}).fillna(3)
        housing_grp = housing_grp.sort_values('sort_order').drop(columns=['sort_order']).reset_index(drop=True)
        housing_grp['Percentage_of_Pool'] = (housing_grp['Total_Fund_Fuzzy'] / total_fund * 100).round(1)
        housing_grp['Avg_Fund_Trad'] = flat_share
        housing_grp['Avg_Difference_Pct'] = ((housing_grp['Avg_Fund_Fuzzy'] - flat_share) / flat_share * 100).round(1)

        # Poverty Class
        poverty_grp = df.groupby('Poverty_Class').agg(
            Count=('Poverty_Class', 'count'),
            Avg_Score=('Vulnerability_Score', 'mean'),
            Avg_Fund_Fuzzy=('Allocated_Fund_BDT', 'mean'),
            Total_Fund_Fuzzy=('Allocated_Fund_BDT', 'sum')
        ).reset_index()
        poverty_grp['sort_order'] = poverty_grp['Poverty_Class'].apply(
            lambda x: 0 if "Extremely" in x else (1 if "Moderately" in x else 2)
        )
        poverty_grp = poverty_grp.sort_values('sort_order').drop(columns=['sort_order']).reset_index(drop=True)
        poverty_grp['Percentage_of_Pool'] = (poverty_grp['Total_Fund_Fuzzy'] / total_fund * 100).round(1)
        poverty_grp['Avg_Fund_Trad'] = flat_share
        poverty_grp['Avg_Difference_Pct'] = ((poverty_grp['Avg_Fund_Fuzzy'] - flat_share) / flat_share * 100).round(1)

        # Upazila
        upazila_grp = df.groupby('Upazila').agg(
            Count=('Upazila', 'count'),
            Avg_Score=('Vulnerability_Score', 'mean'),
            Avg_Fund_Fuzzy=('Allocated_Fund_BDT', 'mean'),
            Total_Fund_Fuzzy=('Allocated_Fund_BDT', 'sum')
        ).sort_values('Avg_Fund_Fuzzy', ascending=False).reset_index()
        upazila_grp['Percentage_of_Pool'] = (upazila_grp['Total_Fund_Fuzzy'] / total_fund * 100).round(1)
        upazila_grp['Avg_Fund_Trad'] = flat_share
        upazila_grp['Avg_Difference_Pct'] = ((upazila_grp['Avg_Fund_Fuzzy'] - flat_share) / flat_share * 100).round(1)

        return jsonify({
            "report_md": report_md,
            "gender_stats": gender_grp.to_dict(orient='records'),
            "housing_stats": housing_grp.to_dict(orient='records'),
            "poverty_stats": poverty_grp.to_dict(orient='records'),
            "upazila_stats": upazila_grp.to_dict(orient='records'),
            "total_fund": total_fund,
            "flat_share": flat_share
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
#   GET /api/outcome_chart  —  Demographic Outcome visualization image
# ============================================================
from flask import send_file
@app.route('/api/outcome_chart')
def outcome_chart():
    try:
        chart_path = DATA_DIR / "distribution_outcome_report.png"
        if chart_path.exists():
            return send_file(chart_path, mimetype='image/png')
        return jsonify({"error": "Chart not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("=" * 50)
    print("  Block-Relief Flask API")
    print("  http://127.0.0.1:5000")
    print("=" * 50)

    debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
    app.run(debug=debug_mode, port=5000)