"""
ECOUNT ERP API integration.

Auth endpoint : https://oapiIB.ecount.com/OAPI/V2/OAPILogin
Inventory     : https://oapiIB.ecount.com/OAPI/V2/InventoryBalance/GetListInventoryBalanceStatusByLocation
Sales (TBD)   : https://oapiIB.ecount.com/OAPI/V2/Sale/GetListSale  ← 待確認正確 endpoint

All credentials come from environment variables — never hardcode here.
"""
import json
from datetime import date, timedelta
import httpx
from ..config import settings

# Warehouse codes used in inventory queries
WAREHOUSE_CODES = [
    "100", "101", "102", "105", "107", "108", "109",
    "111", "B0001", "L0001", "L0004", "L0006",
    "T0002", "113", "T0059", "116", "112", "103",
]
WH_CD_STRING = "∬".join(WAREHOUSE_CODES)   # ∬ separator as used in existing script

LOGIN_URL = "https://oapiIB.ecount.com/OAPI/V2/OAPILogin"
INVENTORY_URL = "https://oapiIB.ecount.com/OAPI/V2/InventoryBalance/GetListInventoryBalanceStatusByLocation"
SALE_LIST_URL = "https://oapiIB.ecount.com/OAPI/V2/Sale/GetListSale"  # ← 請確認此 endpoint 是否正確


async def _login() -> str:
    """Return a fresh SESSION_ID."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            LOGIN_URL,
            json={
                "COM_CODE":     settings.ecount_company_code,
                "USER_ID":      settings.ecount_user_id,
                "API_CERT_KEY": settings.ecount_api_cert_key,
                "LAN_TYPE":     "zh-TW",
                "ZONE":         settings.ecount_zone,
            },
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()["Data"]["Datas"]["SESSION_ID"]


async def fetch_inventory() -> list[dict]:
    """
    Fetch current inventory balance across all warehouses.
    Returns aggregated list: [{PROD_CD, PROD_DES, BAL_QTY}]
    """
    from collections import defaultdict
    import datetime

    session_id = await _login()
    base_date = datetime.date.today().strftime("%Y%m%d")

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{INVENTORY_URL}?SESSION_ID={session_id}",
            json={
                "BASE_DATE":       base_date,
                "WH_CD":           WH_CD_STRING,
                "DEL_LOCATION_YN": "Y",
                "BAL_FLAG":        "N",
                "DEL_GUBUN":       "N",
            },
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()

    raw = resp.json()["Data"]["Result"]
    items = json.loads(raw) if isinstance(raw, str) else raw

    summary = defaultdict(lambda: {"PROD_DES": "", "BAL_QTY": 0.0})
    for item in items:
        cd = item["PROD_CD"]
        summary[cd]["PROD_DES"] = item.get("PROD_DES", "")
        summary[cd]["BAL_QTY"] += float(item.get("BAL_QTY", 0))

    return [{"prod_cd": k, "prod_des": v["PROD_DES"], "bal_qty": v["BAL_QTY"]} for k, v in summary.items()]


async def fetch_sale_orders(start_date: date, end_date: date) -> list[dict]:
    """
    Fetch sale orders from ECOUNT for the given date range.

    ⚠️  SALE_LIST_URL endpoint is unconfirmed — verify against ECOUNT API docs
        or check existing export to identify correct endpoint + field names.
    """
    session_id = await _login()

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{SALE_LIST_URL}?SESSION_ID={session_id}",
            json={
                "START_DATE": start_date.strftime("%Y%m%d"),
                "END_DATE":   end_date.strftime("%Y%m%d"),
            },
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()

    raw = resp.json().get("Data", {}).get("Result") or resp.json().get("Data", {}).get("Datas", [])
    return json.loads(raw) if isinstance(raw, str) else (raw if isinstance(raw, list) else [])


def parse_order(raw: dict) -> dict:
    """
    Map ECOUNT sale order fields to internal schema.

    Field names below are guesses based on ECOUNT conventions.
    Confirm by printing a raw record from fetch_sale_orders().
    """
    from datetime import datetime

    date_str = raw.get("SALE_DATE") or raw.get("IO_DATE", "")
    try:
        order_date = datetime.strptime(date_str, "%Y%m%d").date()
    except (ValueError, TypeError):
        order_date = None

    unit_price = float(raw.get("UNIT_PRICE", 0) or 0)
    qty        = int(float(raw.get("QTY", 0) or 0))
    discount   = float(raw.get("DISCOUNT_AMOUNT", 0) or 0)

    return {
        "order_date":    order_date,
        "order_no":      raw.get("SALE_NO") or raw.get("IO_NO", ""),
        "product_code":  raw.get("PROD_CD", ""),
        "product_name":  raw.get("PROD_DES", ""),
        "brand":         raw.get("CLASS_1_DES") or raw.get("GRP_DES", ""),   # ← 確認品牌欄位名稱
        "channel":       raw.get("CLASS_2_DES") or raw.get("WH_DES", ""),    # ← 確認通路欄位名稱
        "customer_code": raw.get("CUST_CD", ""),
        "customer_name": raw.get("CUST_DES", ""),
        "category":      raw.get("CLASS_3_DES", ""),
        "qty":           qty,
        "unit_price":    unit_price,
        "discount":      discount,
        "subtotal":      unit_price * qty - discount,
        "year":          order_date.year  if order_date else None,
        "month":         order_date.month if order_date else None,
    }
