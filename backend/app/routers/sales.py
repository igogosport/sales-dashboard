from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from ..database import get_db
from .. import models

router = APIRouter(prefix="/api/sales", tags=["sales"])


@router.get("/monthly")
def monthly_trend(
    year: Optional[int] = None,
    brand: Optional[str] = None,
    channel: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Monthly sales amount and qty, grouped by year+month."""
    q = db.query(
        models.SaleOrder.year,
        models.SaleOrder.month,
        func.sum(models.SaleOrder.subtotal).label("amount"),
        func.sum(models.SaleOrder.qty).label("qty"),
    )
    if year:
        q = q.filter(models.SaleOrder.year == year)
    if brand:
        q = q.filter(models.SaleOrder.brand == brand)
    if channel:
        q = q.filter(models.SaleOrder.channel == channel)

    rows = q.group_by(models.SaleOrder.year, models.SaleOrder.month).order_by(
        models.SaleOrder.year, models.SaleOrder.month
    ).all()

    return [{"year": r.year, "month": r.month, "amount": r.amount, "qty": r.qty} for r in rows]


@router.get("/by-brand")
def by_brand(
    year: Optional[int] = None,
    month: Optional[int] = None,
    channel: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(
        models.SaleOrder.brand,
        func.sum(models.SaleOrder.subtotal).label("amount"),
        func.sum(models.SaleOrder.qty).label("qty"),
    )
    if year:
        q = q.filter(models.SaleOrder.year == year)
    if month:
        q = q.filter(models.SaleOrder.month == month)
    if channel:
        q = q.filter(models.SaleOrder.channel == channel)

    rows = q.group_by(models.SaleOrder.brand).order_by(func.sum(models.SaleOrder.subtotal).desc()).all()
    return [{"brand": r.brand, "amount": r.amount, "qty": r.qty} for r in rows]


@router.get("/by-channel")
def by_channel(
    year: Optional[int] = None,
    month: Optional[int] = None,
    brand: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(
        models.SaleOrder.channel,
        func.sum(models.SaleOrder.subtotal).label("amount"),
        func.sum(models.SaleOrder.qty).label("qty"),
    )
    if year:
        q = q.filter(models.SaleOrder.year == year)
    if month:
        q = q.filter(models.SaleOrder.month == month)
    if brand:
        q = q.filter(models.SaleOrder.brand == brand)

    rows = q.group_by(models.SaleOrder.channel).order_by(func.sum(models.SaleOrder.subtotal).desc()).all()
    return [{"channel": r.channel, "amount": r.amount, "qty": r.qty} for r in rows]


@router.get("/summary")
def summary(year: Optional[int] = None, month: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(
        func.sum(models.SaleOrder.subtotal).label("total_amount"),
        func.sum(models.SaleOrder.qty).label("total_qty"),
        func.count(func.distinct(models.SaleOrder.product_code)).label("product_count"),
        func.count(func.distinct(models.SaleOrder.brand)).label("brand_count"),
    )
    if year:
        q = q.filter(models.SaleOrder.year == year)
    if month:
        q = q.filter(models.SaleOrder.month == month)
    r = q.first()
    return {
        "total_amount": r.total_amount or 0,
        "total_qty": r.total_qty or 0,
        "product_count": r.product_count or 0,
        "brand_count": r.brand_count or 0,
    }


@router.get("/filters")
def filters(db: Session = Depends(get_db)):
    """Return distinct filter values for the UI."""
    years = [r[0] for r in db.query(func.distinct(models.SaleOrder.year)).order_by(models.SaleOrder.year.desc()).all() if r[0]]
    brands = [r[0] for r in db.query(func.distinct(models.SaleOrder.brand)).order_by(models.SaleOrder.brand).all() if r[0]]
    channels = [r[0] for r in db.query(func.distinct(models.SaleOrder.channel)).order_by(models.SaleOrder.channel).all() if r[0]]
    return {"years": years, "brands": brands, "channels": channels}
