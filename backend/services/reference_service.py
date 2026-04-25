"""
שירות ייעודי לכתיבה ל-ReferenceProject (מקור האמת).

כל INSERT לטבלת reference_projects חייב לעבור דרך פונקציה זו בלבד.
ה-approval route קורא לפונקציה זו — ואסור לקרוא ל-db.add(ReferenceProject(...))
מכל מקום אחר בקוד.

הערה ארכיטקטורית: השירות משתמש ב-HTTPException ישירות כי FastAPI
תופס אותה בכל מקום ב-call stack — זה מקובל ומכוון.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException
from db_models import Project, ReferenceProject


def save_project_to_reference(
    db: Session,
    project_id: str,
    source_label: str,
) -> tuple:
    """
    נקודת הכניסה היחידה לכתיבה ל-reference_projects.

    בודק:
    1. הפרויקט קיים
    2. סטטוסו approved או saved_to_db
    3. אינו פרויקט טסט
    4. קיימות תוצאות חישוב
    5. לא קיים כבר בבסיס

    שולף את הסכום מה-calculation_result בלבד — לא מקבל מהלקוח.
    מחזיר: (ref, approved_fee)
    """
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="פרויקט לא נמצא")

    if p.is_exception_pricing:
        raise HTTPException(
            status_code=400,
            detail="פרויקט חריג לא נשמר לבסיס הנתונים הייחוסי",
        )

    if p.status not in ("approved", "saved_to_db"):
        raise HTTPException(
            status_code=400,
            detail="ניתן לשמור לבסיס הנתונים רק לאחר אישור ההצעה",
        )

    # חסימת פרויקט טסט — הגנת backend, פועלת גם אם עוקפים את ה-frontend
    if p.is_test:
        raise HTTPException(
            status_code=400,
            detail=(
                "פרויקט טסט לא נשמר לבסיס הנתונים. "
                "ניתן לחשב, לאשר ולהפיק מסמך לבדיקה בלבד."
            ),
        )

    if not p.calculation_result:
        raise HTTPException(
            status_code=400,
            detail="חסרות תוצאות חישוב — יש לחשב מחדש לפני השמירה",
        )

    # שליפת הסכום מה-DB — לא מהלקוח
    calc = p.calculation_result
    approved_fee = calc.get("blended_total")
    if not approved_fee or approved_fee <= 0:
        raise HTTPException(
            status_code=400,
            detail="לא נמצא מחיר מאושר בתוצאות החישוב. יש לחשב מחדש.",
        )

    # מניעת כפילויות
    existing = db.query(ReferenceProject).filter(
        ReferenceProject.project_name == p.project_name
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"פרויקט '{p.project_name}' כבר קיים בבסיס הנתונים",
        )

    tier = calc.get("tier", "")
    schedule = calc.get("schedule", {})

    ref = ReferenceProject(
        project_name=p.project_name,
        location_city=p.location_city,
        project_type=p.project_type,
        num_units=p.num_units,
        num_floors_above=p.num_floors_above,
        num_floors_underground=p.num_floors_underground,
        execution_phases=p.execution_phases,
        total_fee=approved_fee,
        fee_per_unit=approved_fee / p.num_units if p.num_units else None,
        timeline_planning=schedule.get("planning"),
        timeline_excavation=schedule.get("excavation"),
        timeline_underground=schedule.get("underground"),
        timeline_above_ground=schedule.get("above_ground"),
        timeline_finishes=schedule.get("finishes"),
        timeline_handover=schedule.get("handover"),
        tier=tier,
        source_type=source_label,
    )
    db.add(ref)

    return ref, approved_fee
