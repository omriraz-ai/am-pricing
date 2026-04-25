from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from database import get_db
from db_models import Project
from models.project import ProjectCreate, ProjectUpdate, ProjectResponse
from utils.region_mapper import city_to_region

router = APIRouter(prefix="/projects", tags=["פרויקטים"])

VALID_BUSINESS_STATUSES = {"בטיפול", "הוגש", "זכינו", "לא_זכינו", "הסתיים"}


def _validate_override(multiplier: float, reason: str) -> None:
    """אכיפת נימוק override — אם המכפיל שונה מ-1.0, חובה לצרף סיבה."""
    if abs(multiplier - 1.0) > 0.001 and not (reason or "").strip():
        raise HTTPException(
            status_code=400,
            detail=(
                f"מכפיל מורכבות ידני הוגדר כ-{multiplier:.2f}. "
                "שדה 'סיבת שינוי מכפיל' (manual_override_reason) הוא חובה כאשר המכפיל שונה מ-1.0."
            ),
        )


def _to_response(p: Project) -> ProjectResponse:
    return ProjectResponse(
        id=p.id,
        status=p.status,
        is_test=p.is_test or False,
        is_exception_pricing=p.is_exception_pricing or False,
        project_name=p.project_name,
        client_name=p.client_name,
        location_city=p.location_city,
        project_type=p.project_type,
        num_units=p.num_units,
        num_floors_above=p.num_floors_above,
        execution_phases=p.execution_phases,
        pricing_mode=p.pricing_mode,
        num_buildings=p.num_buildings,
        num_floors_underground=p.num_floors_underground,
        plot_area_sqm=p.plot_area_sqm,
        timeline_planning=p.timeline_planning,
        timeline_excavation=p.timeline_excavation,
        timeline_underground=p.timeline_underground,
        timeline_above_ground=p.timeline_above_ground,
        timeline_finishes=p.timeline_finishes,
        timeline_handover=p.timeline_handover,
        manual_complexity_multiplier=p.manual_complexity_multiplier,
        manual_override_reason=p.manual_override_reason,
        manual_total_price=p.manual_total_price,
        use_manual_pricing=p.use_manual_pricing,
        index_type=p.index_type,
        includes_vat=p.includes_vat,
        notes_pricing=p.notes_pricing,
        business_status=p.business_status or "בטיפול",
        is_archived=p.is_archived or False,
        calculation_result=p.calculation_result,
        exception_pricing_override=p.exception_pricing_override,
        created_at=str(p.created_at) if p.created_at else None,
        updated_at=str(p.updated_at) if p.updated_at else None,
        
    )


@router.post("/", response_model=ProjectResponse, summary="יצירת פרויקט חדש")
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    _validate_override(
        data.manual_complexity_multiplier or 1.0,
        data.manual_override_reason or "",
    )
    project = Project(
        project_name=data.project_name,
        client_name=data.client_name,
        location_city=data.location_city,
        pricing_region=city_to_region(data.location_city),
        project_type=data.project_type.value,
        pricing_mode=data.pricing_mode.value,
        # תיקון קריטי: is_test=False כברירת מחדל
        is_test=data.is_test,
        is_exception_pricing=data.is_exception_pricing,
        num_units=data.num_units,
        num_buildings=data.num_buildings,
        num_floors_above=data.num_floors_above,
        num_floors_underground=data.num_floors_underground,
        execution_phases=data.execution_phases,
        plot_area_sqm=data.plot_area_sqm,
        area_residential_sqm=data.area_residential_sqm,
        area_commercial_sqm=data.area_commercial_sqm,
        area_employment_sqm=data.area_employment_sqm,
        timeline_planning=data.timeline_planning,
        timeline_excavation=data.timeline_excavation,
        timeline_underground=data.timeline_underground,
        timeline_above_ground=data.timeline_above_ground,
        timeline_finishes=data.timeline_finishes,
        timeline_handover=data.timeline_handover,
        manual_complexity_multiplier=data.manual_complexity_multiplier,
        manual_override_reason=data.manual_override_reason,
        index_type=data.index_type.value,
        includes_vat=data.includes_vat,
        notes_pricing=data.notes_pricing,
        business_status=data.business_status.value if hasattr(data.business_status, "value") else "בטיפול",
        is_archived=data.is_archived,
        status="draft",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return _to_response(project)


@router.get("/", response_model=List[ProjectResponse], summary="רשימת פרויקטים")
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return [_to_response(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse, summary="פרויקט בודד")
def get_project(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="פרויקט לא נמצא")
    return _to_response(p)


@router.patch("/{project_id}", response_model=ProjectResponse, summary="עדכון פרויקט")
def update_project(project_id: str, data: ProjectUpdate, db: Session = Depends(get_db)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="פרויקט לא נמצא")

    update_data = data.dict(exclude_unset=True)

    new_multiplier = update_data.get("manual_complexity_multiplier", p.manual_complexity_multiplier) or 1.0
    new_reason = update_data.get("manual_override_reason", p.manual_override_reason) or ""
    _validate_override(new_multiplier, new_reason)

    for field, value in update_data.items():
        if hasattr(value, "value"):
            value = value.value
        setattr(p, field, value)

    # טיפול מיוחד ל-override
    if data.exception_pricing_override is not None:
         p.exception_pricing_override = data.exception_pricing_override    

    if "location_city" in update_data:
        p.pricing_region = city_to_region(p.location_city)

    db.commit()
    db.refresh(p)
    return _to_response(p)


@router.delete("/{project_id}", summary="מחיקת פרויקט (טיוטה בלבד)")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="פרויקט לא נמצא")
    if p.status == "saved_to_db":
        raise HTTPException(status_code=400, detail="לא ניתן למחוק פרויקט שנשמר בבסיס הנתונים")
    db.delete(p)
    db.commit()
    return {"message": "פרויקט נמחק"}


# ── סטטוס עסקי (פאזה 1) ──────────────────────────────────────────────

class BusinessStatusUpdate(BaseModel):
    """עדכון סטטוס עסקי בלבד — לא נוגע בלוגיקת תמחור."""
    business_status: str
    is_archived: Optional[bool] = None


@router.patch("/{project_id}/business-status", response_model=ProjectResponse, summary="עדכון סטטוס עסקי")
def update_business_status(
    project_id: str,
    data: BusinessStatusUpdate,
    db: Session = Depends(get_db),
):
    """
    שינוי סטטוס עסקי וסימון ארכיון.
    לא נוגע בלוגיקת תמחור, אישור, חישוב או DOCX.
    """
    if data.business_status not in VALID_BUSINESS_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"סטטוס לא חוקי: '{data.business_status}'. ערכים מותרים: {', '.join(VALID_BUSINESS_STATUSES)}",
        )

    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="פרויקט לא נמצא")

    p.business_status = data.business_status

    if data.is_archived is not None:
        p.is_archived = data.is_archived
    elif data.business_status == "הסתיים":
        p.is_archived = True

    db.commit()
    db.refresh(p)
    return _to_response(p)
