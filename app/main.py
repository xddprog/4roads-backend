from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.routers import api_v1_routers
from app.infrastructure.database.adapters.pg_connection import DatabaseConnection
from app.infrastructure.logging.logger import configure_logging, get_logger
from app.infrastructure.middleware import LoggingMiddleware
from app.infrastructure.config.config import APP_CONFIG

from admin.admin import create_admin, sync_engine

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app):
    logger.info("application_startup", app_name=APP_CONFIG.APP_NAME, debug=APP_CONFIG.DEBUG)
    
    db_connection = DatabaseConnection()
    await db_connection.init_test_db()
    app.state.db_connection = db_connection
    
    logger.info("database_connected")
    
    yield
    
    logger.info("application_shutdown")


app = FastAPI(
    title=APP_CONFIG.APP_NAME,
    debug=APP_CONFIG.DEBUG,
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=APP_CONFIG.CORS_ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)

static_dir = Path(APP_CONFIG.STATIC_DIR)
if not static_dir.exists():
    static_dir.mkdir(parents=True, exist_ok=True)
    logger.info("static_directory_created", path=str(static_dir))

app.mount("/static", StaticFiles(directory=APP_CONFIG.STATIC_DIR), name="static")
logger.info("static_files_mounted", directory=APP_CONFIG.STATIC_DIR)

app.include_router(api_v1_routers)

admin = create_admin(engine=sync_engine)
admin.mount_to(app)
