from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
