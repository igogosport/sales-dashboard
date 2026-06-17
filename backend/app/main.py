from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
from .database import engine, SessionLocal
from . import models
from .routers import sales, purchase, sync as sync_router, inventory
from .services.sync import sync_ecount, sync_gsheets
from .config import settings

models.Base.metadata.create_all(bind=engine)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    scheduler.add_job(
        lambda: sync_ecount(db),
        "cron",
        hour=settings.sync_schedule_hour,
        minute=0,
    )
    scheduler.add_job(
        lambda: sync_gsheets(db),
        "cron",
        hour=settings.sync_schedule_hour,
        minute=5,
    )
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="Sales Dashboard API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sales.router)
app.include_router(purchase.router)
app.include_router(sync_router.router)
app.include_router(inventory.router)


@app.get("/health")
def health():
    return {"status": "ok"}
