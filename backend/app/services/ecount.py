"""
ECOUNT ERP API integration.
Docs: https://oapi.ecounterp.com
"""
import httpx
from datetime import date, datetime
from ..config import settings


async def get_session_id() -> str:
    """Obtain a session ID from ECOUNT API."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.ecount_api_url}/ECounterP.API.Base/GetSessionID",
            json={
                "ZONE": "TW",
                "COM_CODE": settings.ecount_company_code,
                "API_CERT_KEY": settings.ecount_api_cert_key,
                "LAN_TYPE": "zh-TW",
                "INHERIT_AUTH": "0",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["Data"]["Datas"]["SESSION_ID"]


async def fetch_sale_orders(start_date: date, end_date: date) -> list[dict]:
    """
    Fetch sale orders from ECOUNT for the given date range.
    Returns a list of raw order records.
    """
    session_id = await get_session_id()

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.ecount_api_url}/ECounterP.API.Sale/GetSaleList",
            headers={"SESSION_ID": session_id},
            json={
                "SEARCH_START_DATE": start_date.strftime("%Y%m%d"),
                "SEARCH_END_DATE": end_date.strftime("%Y%m%d"),
                "LIST_COUNT": "1000",
                "START_NUM": "1",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("Data", {}).get("Datas", [])


def parse_order(raw: dict) -> dict:
    """Map ECOUNT raw fields to our internal schema."""
    order_date_str = raw.get("SALE_DATE", "")
    order_date = datetime.strptime(order_date_str, "%Y%m%d").date() if order_date_str else None
    unit_price = float(raw.get("UNIT_PRICE", 0) or 0)
    qty = int(raw.get("QTY", 0) or 0)
    discount = float(raw.get("DISCOUNT_AMOUNT", 0) or 0)

    return {
        "order_date": order_date,
        "order_no": raw.get("SALE_NO", ""),
        "product_code": raw.get("PROD_CD", ""),
        "product_name": raw.get("PROD_DES", ""),
        "brand": raw.get("CLASS_1_DES", ""),   # adjust field names to match your ECOUNT setup
        "channel": raw.get("CLASS_2_DES", ""),
        "customer_code": raw.get("CUST_CD", ""),
        "customer_name": raw.get("CUST_DES", ""),
        "category": raw.get("CLASS_3_DES", ""),
        "qty": qty,
        "unit_price": unit_price,
        "discount": discount,
        "subtotal": unit_price * qty - discount,
        "year": order_date.year if order_date else None,
        "month": order_date.month if order_date else None,
    }
