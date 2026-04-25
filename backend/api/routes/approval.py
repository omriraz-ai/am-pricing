"""
מסלול אישור — שער קריטי לפני יצירת הצעה ושמירה לבסיס הנתונים.

שינויים:
    1 — user_id נשמר ב-ApprovalLog
    2 — אכיפת override_reason לפני אישור
    3 — כתיבה ל-ReferenceProject רק דרך reference_service
    4 — override_active + override_reason נשמרים ב-ApprovalLog
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from db_models import Project, ApprovalLog
from models.reference import SaveToDbRequest
from services.reference_service import save_project_to_reference

router = APIRouter(prefix="/approval", tags=["אישור"])

# placeholder — להחלפה כשתוטמע מערכת משתמשים אמיתית
_DEFAULT_USER_ID = "משתמש_ידני"


class ApprovalRequest(BaseModel):
    project_id: str
    notes: Optional[str] = None


def _check_override_reason(p: Project) -> None:
    """
    שינוי 2 — אכיפת נימוק override ב-API לפני אישור.
    אם המכפיל שונה מ-1.0, חייבת להיות סיבה שמולאה.
    """
    multiplier = p.manual_complexity_multiplier or 1.0
    if abs(multiplier - 1.0) > 0.001 and not (p.manual_override_reason or "").strip():
        raise HTTPException(
            status_code=400,
            detail=(
                f"מכפיל מורכבות ידני הוגדר כ-{multiplier:.2f} — "
                "שדה 'סיבת שינוי מכפיל' הוא חובה לפני אישור ההצעה."
            ),
        )


def _is_override_active(p: Project) -> bool:
    return abs((p.manual_complexity_multiplier or 1.0) - 1.0) > 0.001


@router.post("/confirm", summary="אישור יצירת הצעת מחיר")
def confirm_approval(req: ApprovalRequest, db: Session = Depends(get_db)):
    """
    שער קריטי — המשתמש אישר את הנתונים והמחיר.
    שינוי 2: חסום אם override ללא נימוק.
    שינויים 1+4: שומר user_id, override_active, override_reason ב-log.
    """
    p = db.query(Project).filter(Project.id == req.project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="פרויקט לא נמצא")

    if not p.calculation_result:
        raise HTTPException(status_code=400, detail="יש לחשב תמחור לפני האישור")

    # שינוי 2 — בדיקת override לפני אישור
    _check_override_reason(p)

    calc = p.calculation_result
    final_fee = calc.get("blended_total", 0)
    final_per_unit = calc.get("blended_per_unit", 0)
    flags = calc.get("flags", {})
    override_active = _is_override_active(p)

    # שינויים 1+4 — שמירת audit fields
    log = ApprovalLog(
        project_id=p.id,
        action="approved_proposal",
        final_fee=final_fee,
        final_fee_per_unit=final_per_unit,
        flags_at_approval=flags,
        notes=req.notes,
        user_id=_DEFAULT_USER_ID,
        override_active=override_active,
        override_reason=p.manual_override_reason if override_active else None,
    )
    db.add(log)

    p.status = "approved"
    db.commit()

    return {
        "message": "אושר בהצלחה",
        "project_id": p.id,
        "final_fee": final_fee,
        "final_fee_per_unit": final_per_unit,
    }

@router.post("/save-to-db", summary="שמירה לבסיס הנתונים — שלב נפרד")
def save_to_reference_db(req: SaveToDbRequest, db: Session = Depends(get_db)):

    p = db.query(Project).filter(Project.id == req.project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="פרויקט לא נמצא")

    if p.is_test:
        raise HTTPException(
            status_code=400,
            detail="לא ניתן לשמור פרויקט בדיקה לבסיס הנתונים"
        )

    ref, approved_fee = save_project_to_reference(
        db=db,
        project_id=req.project_id,
        source_label=req.source_label,
    )

    override_active = _is_override_active(p)

    log = ApprovalLog(
        project_id=p.id,
        action="saved_to_db",
        final_fee=approved_fee,
        final_fee_per_unit=approved_fee / p.num_units if p.num_units else None,
        notes=f"נשמר לבסיס הנתונים: {req.source_label}",
        user_id=_DEFAULT_USER_ID,
        override_active=override_active,
        override_reason=p.manual_override_reason if override_active else None,
    )

    db.add(log)

    p.status = "saved_to_db"
    db.commit()

    return {
        "message": "הפרויקט נשמר בבסיס הנתונים",
        "reference_id": ref.id,
        "approved_fee": approved_fee,
    }


@router.get("/log", summary="היסטוריית אישורים")
def get_approval_log(db: Session = Depends(get_db)):
    logs = db.query(ApprovalLog).order_by(ApprovalLog.approved_at.desc()).limit(50).all()
    return [
        {
            "id": l.id,
            "project_id": l.project_id,
            "action": l.action,
            "final_fee": l.final_fee,
            "final_fee_per_unit": l.final_fee_per_unit,
            "approved_at": str(l.approved_at),
            "notes": l.notes,
            "user_id": l.user_id,
            "override_active": l.override_active,
            "override_reason": l.override_reason,
        }
        for l in logs
    ]
