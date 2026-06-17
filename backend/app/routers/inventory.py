from fastapi import APIRouter
from ..services.gsheets import fetch_reorder_plan

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("/reorder-plan")
def reorder_plan():
    """
    Return all products from the reorder planning sheet,
    including inventory levels, reorder signals, and 12-month sales history.
    """
    return fetch_reorder_plan()


@router.get("/alerts")
def reorder_alerts():
    """Products that need reordering (是否補貨 = true)."""
    rows = fetch_reorder_plan()
    return [r for r in rows if r["need_reorder"]]


@router.get("/monthly-sales")
def monthly_sales_by_brand():
    """
    Aggregate 12-month sales by brand for trend charts.
    Returns: { brand: { "2025/6": qty, "2025/7": qty, ... } }
    """
    rows = fetch_reorder_plan()
    from collections import defaultdict
    brand_map: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in rows:
        brand = row["brand"] or "未知"
        for month, qty in row["monthly_sales"].items():
            brand_map[brand][month] += qty
    return brand_map
