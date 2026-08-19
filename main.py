# main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pathlib import Path

from api.whatsapp import router as whatsapp_router
from api.telegram import router as telegram_router
from api.admin import router as admin_router
from core.database import init_db
from core.config import get_settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    await init_db()
    yield

app_configs = {
    "title": "FastAPI WhatsApp & Telegram AI Agent & CRM Template",
    "description": "Production-ready boilerplate for autonomous WhatsApp & Telegram AI sales agents with Real-Time Admin CRM & Live Takeover.",
    "version": "1.0.0",
    "lifespan": lifespan,
}

if get_settings().ENVIRONMENT != "production":
    app_configs["docs_url"] = "/docs"
    app_configs["redoc_url"] = "/redoc"
    app_configs["openapi_url"] = "/openapi.json"

app = FastAPI(**app_configs)

# Include Routers
app.include_router(whatsapp_router, prefix="", tags=["WhatsApp"])
app.include_router(whatsapp_router, prefix="/whatsapp", tags=["WhatsApp"])
app.include_router(telegram_router, tags=["Telegram"])
app.include_router(admin_router, tags=["Admin Dashboard"])

# Admin Dashboard Web App Route
@app.get("/admin", include_in_schema=False)
async def serve_admin_dashboard():
    dashboard_path = Path(__file__).parent / "static" / "admin" / "index.html"
    return FileResponse(dashboard_path)

@app.get("/", tags=["Health Check"])
async def root():
    return {
        "status": "ok",
        "message": "FastAPI WhatsApp & Telegram AI Agent & CRM Template is live!",
        "dashboard": "/admin"
    }
