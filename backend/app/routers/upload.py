"""
CSV upload endpoint for monthly ECOUNT sales export.

ECOUNT 匯出的銷售 CSV 欄位對應（依實際匯出格式調整）：
  日期/訂單日       → order_date
  訂單號/傳票號     → order_no
  品號/產品代號     → product_code
  品名/產品名稱     → product_name
  品牌              → brand
  通路              → channel
  客戶代號          → customer_code
  客戶名稱          → customer_name
  品類/類別         → category
  數量              → qty
  售價/單價         → unit_price
  折扣/折扣金額     → discount
  小計/金額         → subtotal
"""
import csv
import io
import chardet
from datetime import datetime, date
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db

router = APIRouter(prefix="/api/upload", tags=["upload"])

# Column name aliases — maps common ECOUNT export header names → internal field
FIELD_MAP = {
    # date
    "日期": "order_date", "訂單日": "order_date", "傳票日期": "order_date",
    "銷售日期": "order_date", "出貨日期": "order_date",
    # order no
    "訂單號": "order_no", "傳票號": "order_no", "銷售傳票": "order_no",
    "傳票No": "order_no", "SALE_NO": "order_no",
    # product
    "品號": "product_code", "料號": "product_code", "產品代號": "product_code",
    "PROD_CD": "product_code",
    "品名": "product_name", "產品名稱": "product_name", "品名(品牌名稱)": "product_name",
    "品牌品名": "product_name", "PROD_DES": "product_name",
    # brand / channel / category
    "品牌": "brand", "年度品牌": "brand",
    "通路": "channel", "通路名稱": "channel",
    "品類": "category", "類別": "category",
    # customer
    "客戶代號": "customer_code", "客戶/廠商編號": "customer_code",
    "客戶名稱": "customer_name", "客戶/廠商": "customer_name",
    # numbers
    "數量": "qty", "銷售數量": "qty", "出貨數量": "qty",
    "售價": "unit_price", "單價": "unit_price",
    "折扣": "discount", "折扣金額": "discount",
    "小計": "subtotal", "金額": "subtotal", "銷售金額": "subtotal",
}


def _parse_date(val: str) -> date | None:
    for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%Y%m%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(val.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None


def _parse_num(val, default=0.0) -> float:
    try:
        return float(str(val).replace(",", "").strip())
    except (ValueError, TypeError):
        return default


def _detect_and_decode(raw: bytes) -> str:
    detected = chardet.detect(raw)
    encoding = detected.get("encoding") or "utf-8"
    try:
        return raw.decode(encoding)
    except UnicodeDecodeError:
        return raw.decode("utf-8", errors="replace")


@router.post("/sales")
async def upload_sales_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename.endswith((".csv", ".CSV")):
        raise HTTPException(status_code=400, detail="請上傳 CSV 格式的檔案")

    raw = await file.read()
    text = _detect_and_decode(raw)
    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV 沒有標題列")

    # Build column mapping from this file's headers
    col_map: dict[str, str] = {}
    for header in reader.fieldnames:
        clean = header.strip().strip("﻿")
        if clean in FIELD_MAP:
            col_map[clean] = FIELD_MAP[clean]

    if "order_date" not in col_map.values():
        raise HTTPException(
            status_code=422,
            detail=f"找不到日期欄位。CSV 標題列：{list(reader.fieldnames)}",
        )

    inserted = updated = skipped = 0

    for row in reader:
        # Normalize keys
        norm = {col_map[k.strip().strip("﻿")]: v.strip()
                for k, v in row.items()
                if k.strip().strip("﻿") in col_map}

        order_date = _parse_date(norm.get("order_date", ""))
        if not order_date:
            skipped += 1
            continue

        unit_price = _parse_num(norm.get("unit_price", 0))
        qty        = int(_parse_num(norm.get("qty", 0)))
        discount   = _parse_num(norm.get("discount", 0))
        subtotal   = _parse_num(norm.get("subtotal")) or (unit_price * qty - discount)
        order_no   = norm.get("order_no", "")

        data = {
            "order_date":    order_date,
            "order_no":      order_no,
            "product_code":  norm.get("product_code", ""),
            "product_name":  norm.get("product_name", ""),
            "brand":         norm.get("brand", ""),
            "channel":       norm.get("channel", ""),
            "customer_code": norm.get("customer_code", ""),
            "customer_name": norm.get("customer_name", ""),
            "category":      norm.get("category", ""),
            "qty":           qty,
            "unit_price":    unit_price,
            "discount":      discount,
            "subtotal":      subtotal,
            "year":          order_date.year,
            "month":         order_date.month,
        }

        if order_no:
            existing = db.query(models.SaleOrder).filter_by(order_no=order_no).first()
            if existing:
                for k, v in data.items():
                    setattr(existing, k, v)
                updated += 1
                continue

        db.add(models.SaleOrder(**data))
        inserted += 1

    db.commit()

    return {
        "status": "ok",
        "filename": file.filename,
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
        "total_processed": inserted + updated + skipped,
    }
