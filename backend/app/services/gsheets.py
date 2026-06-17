"""
Google Sheets integration for purchase / in-transit PO data.

Sheet: ✨在途採購表
  Col C (idx 2)  : 進倉單號
  Col D (idx 3)  : 產品代號
  Col F (idx 5)  : PO 數量
  Col K (idx 10) : 盤差
  Col O (idx 14) : 已入庫 (checkbox)
  Col AG (idx 32): 已入庫日

Sheet: 每日庫存IN
  Col D (idx 3)  : 進倉單號
  Col E (idx 4)  : 產品代號
  Col G (idx 6)  : 實收數量
"""
import json
from datetime import datetime, date
import gspread
from google.oauth2.service_account import Credentials
from ..config import settings

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

SHEET_PO = "✨在途採購表"
SHEET_IN = "每日庫存IN"
SHEET_REORDER_GID = 477337278   # 補貨規劃表 (gid from URL)


def _get_client() -> gspread.Client:
    creds_dict = json.loads(settings.google_service_account_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def _to_date(val) -> date | None:
    if not val:
        return None
    if isinstance(val, (datetime,)):
        return val.date()
    if isinstance(val, date):
        return val
    for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(str(val).strip(), fmt).date()
        except ValueError:
            continue
    return None


def _to_int(val) -> int:
    try:
        return int(str(val).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0


def fetch_po_table() -> list[dict]:
    """
    Read ✨在途採購表 and return structured PO rows.
    """
    client = _get_client()
    sheet = client.open_by_key(settings.google_sheets_id)
    ws = sheet.worksheet(SHEET_PO)
    rows = ws.get_all_values()

    if len(rows) < 2:
        return []

    result = []
    for row in rows[1:]:  # skip header
        def col(idx): return row[idx] if idx < len(row) else ""

        receipt_no = col(2).strip()   # C
        product_code = col(3).strip() # D
        if not receipt_no and not product_code:
            continue

        po_qty = _to_int(col(5))      # F
        discrepancy = col(10).strip() # K
        received = col(14) == "TRUE" or col(14) is True  # O checkbox
        received_date = _to_date(col(32))  # AG

        result.append({
            "receipt_no": receipt_no,
            "product_code": product_code,
            "po_qty": po_qty,
            "discrepancy": discrepancy,
            "received": received,
            "received_date": received_date,
        })

    return result


def fetch_daily_in() -> list[dict]:
    """
    Read 每日庫存IN and return structured inbound records.
    """
    client = _get_client()
    sheet = client.open_by_key(settings.google_sheets_id)
    ws = sheet.worksheet(SHEET_IN)
    rows = ws.get_all_values()

    if len(rows) < 2:
        return []

    result = []
    for row in rows[1:]:
        def col(idx): return row[idx] if idx < len(row) else ""

        receipt_no = col(3).strip()   # D
        product_code = col(4).strip() # E
        actual_qty = _to_int(col(6))  # G

        if not receipt_no or not product_code:
            continue

        result.append({
            "receipt_no": receipt_no,
            "product_code": product_code,
            "actual_qty": actual_qty,
        })

    return result


# ── 補貨規劃表 ──────────────────────────────────────────────────────────────

# Header columns (0-indexed):
# 0=狀態, 1=商品ID, 2=品牌, 3=商品名稱, 4=類別,
# 5=成長率, 6=成長率係數, 7=安庫月數, 8=未來+2+3銷售佔比, 9=季節係數,
# 10=安全庫存, 11=交期, 12=再訂購點, 13=需訂購量, 14=東興庫存,
# 15=是否補貨, 16=銷售月數, 17=全部庫存, 18=平均3個月月銷,
# 19..30 = 月銷 2025/6 ~ 2026/5 (12 months)
_MONTHLY_START_COL = 19
_MONTHLY_HEADERS = [
    "2025/6","2025/7","2025/8","2025/9","2025/10","2025/11","2025/12",
    "2026/1","2026/2","2026/3","2026/4","2026/5",
]


def fetch_reorder_plan() -> list[dict]:
    """
    Read the procurement reorder planning sheet (gid=477337278).
    Returns per-product rows with inventory levels, reorder signals,
    and 12-month sales history.
    """
    client = _get_client()
    spreadsheet = client.open_by_key(settings.google_sheets_id)

    ws = None
    for w in spreadsheet.worksheets():
        if w.id == SHEET_REORDER_GID:
            ws = w
            break
    if ws is None:
        raise ValueError(f"Cannot find worksheet with gid={SHEET_REORDER_GID}")

    rows = ws.get_all_values()
    if len(rows) < 2:
        return []

    result = []
    for row in rows[1:]:
        def col(idx, default=""): return row[idx] if idx < len(row) else default

        product_id = col(1).strip()
        brand = col(2).strip()
        product_name = col(3).strip()
        if not product_id and not product_name:
            continue

        monthly_sales = {}
        for i, label in enumerate(_MONTHLY_HEADERS):
            monthly_sales[label] = _to_int(col(_MONTHLY_START_COL + i))

        result.append({
            "status": col(0).strip(),
            "product_id": product_id,
            "brand": brand,
            "product_name": product_name,
            "category": col(4).strip(),
            "total_inventory": _to_int(col(17)),
            "avg_monthly_sales_3m": _to_int(col(18)),
            "reorder_qty": _to_int(col(13)),
            "safety_stock": _to_int(col(10)),
            "lead_time_days": _to_int(col(11)),
            "reorder_point": _to_int(col(12)),
            "need_reorder": col(15).strip() in ("TRUE", "是", "Y", "✓"),
            "monthly_sales": monthly_sales,
        })

    return result


def fetch_purchases() -> list[dict]:
    """
    Combined view: PO table joined with actual inbound quantities.
    Returns rows suitable for the Purchase model.
    """
    po_rows = fetch_po_table()
    in_rows = fetch_daily_in()

    # Build lookup: (receipt_no, product_code) -> total actual qty
    in_map: dict[tuple, int] = {}
    for r in in_rows:
        key = (r["receipt_no"], r["product_code"])
        in_map[key] = in_map.get(key, 0) + r["actual_qty"]

    result = []
    for po in po_rows:
        key = (po["receipt_no"], po["product_code"])
        actual = in_map.get(key, 0)
        received_date = po["received_date"]
        year = received_date.year if received_date else None
        month = received_date.month if received_date else None

        result.append({
            "purchase_date": received_date,
            "product_code": po["product_code"],
            "product_name": "",        # add more columns if available in your sheet
            "brand": "",
            "qty": po["po_qty"],
            "actual_qty": actual,
            "unit_cost": 0.0,
            "total_cost": 0.0,
            "supplier": po["receipt_no"],
            "year": year,
            "month": month,
        })

    return result
