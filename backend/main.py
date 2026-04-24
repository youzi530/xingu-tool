import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from database import engine, Base, SessionLocal
from routes import ipos, bloggers, analyses
from routes.sync import router as sync_router, run_sync_once
from routes.scrape import router as scrape_router

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger(__name__)

SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL_SECONDS", "21600"))  # 默认 6 小时


async def _periodic_sync():
    """后台定时同步任务"""
    await asyncio.sleep(5)  # 等待应用完全启动
    while True:
        logger.info("定时同步：开始拉取 iTick 港股新股数据…")
        db = SessionLocal()
        try:
            await run_sync_once(db)
        finally:
            db.close()
        logger.info("定时同步完成，下次同步将在 %d 秒后执行", SYNC_INTERVAL)
        await asyncio.sleep(SYNC_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建数据表
    Base.metadata.create_all(bind=engine)

    # 后台定时同步（有 Token 才有效）
    task = asyncio.create_task(_periodic_sync())
    logger.info("后台同步任务已启动，同步间隔 %d 秒", SYNC_INTERVAL)

    yield

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="新股通 API",
    description="港股打新分析聚合平台后端服务",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ipos.router)
app.include_router(bloggers.router)
app.include_router(analyses.router)
app.include_router(sync_router)
app.include_router(scrape_router)


@app.get("/", tags=["系统"])
def health_check():
    token_ok = bool(os.getenv("ITICK_TOKEN", "").strip()) and \
               os.getenv("ITICK_TOKEN") != "your_itick_token_here"
    return {
        "status": "ok",
        "service": "新股通 API v1.1",
        "itick_token_configured": token_ok,
        "sync_interval_seconds": SYNC_INTERVAL,
    }
