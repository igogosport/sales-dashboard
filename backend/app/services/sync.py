"""
Sync orchestration: pull from ECOUNT and Google Sheets, upsert into DB.
"""
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import text
from .. import models
from .ecount import fetch_sale_orders, parse_order
from .gsheets import fetch_purchases


async def sync_ecount(db: Session, days_back: int = 60) -> int:
    end = date.today()
    start = end - timedelta(days=days_back)
    raw_orders = await fetch_sale_orders(start, end)
    count = 0
    for raw in raw_orders:
        parsed = parse_order(raw)
        if not parsed.get("order_no"):
            continue
        existing = db.query(models.SaleOrder).filter_by(order_no=parsed["order_no"]).first()
        if existing:
            for k, v in parsed.items():
                setattr(existing, k, v)
        else:
            db.add(models.SaleOrder(**parsed))
        count += 1
    db.commit()
    _log(db, "ecount", count, "ok")
    return count


def sync_gsheets(db: Session) -> int:
    rows = fetch_purchases()
    db.query(models.Purchase).delete()
    for row in rows:
        db.add(models.Purchase(**row))
    db.commit()
    _log(db, "gsheets", len(rows), "ok")
    return len(rows)


def _log(db: Session, source: str, count: int, status: str, msg: str = ""):
    db.add(models.SyncLog(
        source=source,
        synced_at=datetime.utcnow(),
        records_updated=count,
        status=status,
        message=msg,
    ))
    db.commit()
