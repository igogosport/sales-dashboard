"""
Google Sheets integration for purchase data.
"""
import json
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from ..config import settings

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def _get_client() -> gspread.Client:
    creds_dict = json.loads(settings.google_service_account_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def fetch_purchases() -> list[dict]:
    """
    Fetch purchase rows from Google Sheets.
    Assumes first row is header. Adjust column names to match your sheet.
    """
    client = _get_client()
    sheet = client.open_by_key(settings.google_sheets_id)
    ws = sheet.get_worksheet(0)
    records = ws.get_all_records()

    parsed = []
    for row in records:
        try:
            date_val = row.get("採購日期") or row.get("日期") or ""
            if isinstance(date_val, str) and date_val:
                purchase_date = datetime.strptime(date_val, "%Y/%m/%d").date()
            elif isinstance(date_val, datetime):
                purchase_date = date_val.date()
            else:
                purchase_date = None

            qty = int(row.get("採購數量") or row.get("數量") or 0)
            unit_cost = float(row.get("單價") or row.get("成本") or 0)

            parsed.append({
                "purchase_date": purchase_date,
                "product_code": str(row.get("品號") or row.get("商品編號") or ""),
                "product_name": str(row.get("品名") or row.get("商品名稱") or ""),
                "brand": str(row.get("品牌") or ""),
                "qty": qty,
                "unit_cost": unit_cost,
                "total_cost": qty * unit_cost,
                "supplier": str(row.get("供應商") or row.get("廠商") or ""),
                "year": purchase_date.year if purchase_date else None,
                "month": purchase_date.month if purchase_date else None,
            })
        except Exception:
            continue

    return parsed
