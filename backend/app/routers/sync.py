from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from .. import models
from ..services.sync import sync_ecount, sync_gsheets

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.post("/ecount")
async def trigger_ecount_sync(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    background_tasks.add_task(sync_ecount, db)
    return {"status": "sync started"}


@router.post("/gsheets")
def trigger_gsheets_sync(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    background_tasks.add_task(sync_gsheets, db)
    return {"status": "sync started"}


@router.get("/logs")
def sync_logs(db: Session = Depends(get_db)):
    logs = db.query(models.SyncLog).order_by(models.SyncLog.synced_at.desc()).limit(20).all()
    return [
        {"source": l.source, "synced_at": l.synced_at, "records": l.records_updated, "status": l.status}
        for l in logs
    ]
