from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from db_models import ReferenceProject
from models.reference import ReferenceProjectResponse

router = APIRouter(prefix="/reference", tags=["בסיס נתונים"])


@router.get("/projects", response_model=List[ReferenceProjectResponse], summary="כל הפרויקטים בבסיס")
def list_reference_projects(db: Session = Depends(get_db)):
    projects = db.query(ReferenceProject).order_by(ReferenceProject.project_name).all()
    return projects


@router.get("/projects/{project_id}", response_model=ReferenceProjectResponse, summary="פרויקט בודד מהבסיס")
def get_reference_project(project_id: str, db: Session = Depends(get_db)):
    p = db.query(ReferenceProject).filter(ReferenceProject.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="פרויקט לא נמצא בבסיס הנתונים")
    return p
