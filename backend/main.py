import hmac
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from database import engine, SessionLocal
from db_models import Base
from seed_data import seed_database
from api.routes import projects, pricing, approval, proposal, reference
from api.routes import import_project


# יצירת טבלאות
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AM הנדסה — מערכת הצעות מחיר",
    description="מערכת אוטומטית לחישוב תמחור ויצירת הצעות מחיר לפרויקטי בנייה",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://am-pricing.vercel.app",
        "https://am-pricing-ddy5qf0vp-omri-razs-projects.vercel.app",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Internal-service authentication ──────────────────────────────────────────
# כל בקשה חייבת X-Internal-Service-Token הזהה ל-INTERNAL_SERVICE_TOKEN מה-env
# (ללא fallback). מוחרג: /health בלבד — גם /docs ו-/ נחסמים בכוונה.
# חסר token ב-env → fail-closed: 503 לכל בקשה לא-מוחרגת.
EXEMPT_PATHS = {"/health"}


@app.middleware("http")
async def internal_service_auth(request: Request, call_next):
    if request.url.path in EXEMPT_PATHS:
        return await call_next(request)
    expected = os.getenv("INTERNAL_SERVICE_TOKEN")
    if not expected:
        return JSONResponse(status_code=503, content={
            "detail": "SERVER_MISCONFIGURED: INTERNAL_SERVICE_TOKEN is not set"})
    received = request.headers.get("X-Internal-Service-Token")
    if not received:
        return JSONResponse(status_code=401, content={
            "detail": "Missing X-Internal-Service-Token header"})
    if not hmac.compare_digest(received, expected):
        return JSONResponse(status_code=403, content={
            "detail": "Invalid internal service token"})
    return await call_next(request)


# רישום routes
app.include_router(projects.router, prefix="/api/v1")
app.include_router(pricing.router, prefix="/api/v1")
app.include_router(approval.router, prefix="/api/v1")
app.include_router(proposal.router, prefix="/api/v1")
app.include_router(reference.router, prefix="/api/v1")
app.include_router(import_project.router, prefix="/api/v1")


@app.on_event("startup")
def on_startup():
    """טעינת נתוני בסיס בהפעלה הראשונה."""
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


@app.get("/", tags=["מערכת"])
def root():
    return {
        "message": "AM הנדסה — מערכת הצעות מחיר",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["מערכת"])
def health():
    return {"status": "ok"}
