from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from ..database import get_db
from .. import models

router = APIRouter(prefix="/api/purchase", tags=["purchase"])


@router.get("/monthly")
def monthly(year: Optional[int] = None, brand: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(
        models.Purchase.year,
        models.Purchase.month,
        func.sum(models.Purchase.total_cost).label("cost"),
        func.sum(models.Purchase.qty).label("qty"),
    )
    if year:
        q = q.filter(models.Purchase.year == year)
    if brand:
        q = q.filter(models.Purchase.brand == brand)
    rows = q.group_by(models.Purchase.year, models.Purchase.month).order_by(
        models.Purchase.year, models.Purchase.month
    ).all()
    return [{"year": r.year, "month": r.month, "cost": r.cost, "qty": r.qty} for r in rows]


@router.get("/by-brand")
def by_brand(year: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(
        models.Purchase.brand,
        func.sum(models.Purchase.total_cost).label("cost"),
        func.sum(models.Purchase.qty).label("qty"),
    )
    if year:
        q = q.filter(models.Purchase.year == year)
    rows = q.group_by(models.Purchase.brand).order_by(func.sum(models.Purchase.total_cost).desc()).all()
    return [{"brand": r.brand, "cost": r.cost, "qty": r.qty} for r in rows]
