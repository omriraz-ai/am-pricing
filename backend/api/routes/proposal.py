from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from sqlalchemy.orm import Session
from urllib.parse import quote
import io
import re

from database import get_db
from db_models import Project
from models.reference import ProposalRequest
from services.proposal_generator import generate_proposal_docx
from services.pricing_engine import get_special_conditions

router = APIRouter(prefix="/proposal", tags=["הצעת מחיר"])


def safe_ascii_filename(project_name: str, project_id: str) -> str:
    """
    יוצר שם קובץ בטוח ל-header:
    רק אנגלית / מספרים / קו תחתון / מקף / נקודה
    """
    base_name = f"proposal_{project_name}_{project_id}"

    # החלפת רווחים בקו תחתון
    base_name = base_name.replace(" ", "_")

    # הסרת תווים לא בטוחים ל-header
    base_name = re.sub(r"[^A-Za-z0-9_.-]", "_", base_name)

    # מניעת שמות ארוכים/מכוערים מדי
    base_name = re.sub(r"_+", "_", base_name).strip("_")

    if not base_name:
        base_name = f"proposal_{project_id}"

    return f"{base_name}.docx"


@router.post("/generate", summary="יצירת הצעת מחיר DOCX")
def generate_proposal(req: ProposalRequest, db: Session = Depends(get_db)):
    p = db.query(Project).filter(Project.id == req.project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="פרויקט לא נמצא")

    if not p.calculation_result:
        raise HTTPException(status_code=400, detail="יש לחשב תמחור לפני יצירת ההצעה")

    if p.status not in ("approved", "saved_to_db"):
        raise HTTPException(status_code=400, detail="יש לאשר את הפרויקט לפני יצירת ההצעה")

    calc = p.calculation_result
    schedule = calc.get("schedule", {})

    special_conditions = get_special_conditions(
        execution_phases=p.execution_phases,
        project_type=p.project_type,
        num_floors_above=p.num_floors_above or 0,
        timeline_planning=schedule.get("planning", 0),
    )

    try:
        docx_bytes = generate_proposal_docx(
            project=p,
            calc_result=calc,
            special_conditions=special_conditions,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"שגיאה ביצירת מסמך DOCX: {str(e)}")

    # שם קובץ בטוח באנגלית בלבד ל-header
    download_filename = safe_ascii_filename(
        project_name=p.project_name or "project",
        project_id=p.id,
    )

    # Header בטוח לדפדפנים
    content_disposition = f'attachment; filename="{download_filename}"; filename*=UTF-8\'\'{quote(download_filename)}'

    return StreamingResponse(
        io.BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": content_disposition
        },
    )


@router.get("/{project_id}/preview", summary="תצוגה מקדימה HTML")
def preview_proposal(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="פרויקט לא נמצא")

    if not p.calculation_result:
        raise HTTPException(status_code=400, detail="אין תוצאות חישוב לפרויקט זה")

    calc = p.calculation_result
    schedule = calc.get("schedule", {})
    phase_costs = calc.get("phase_costs", [])
    blended_total = calc.get("blended_total", 0)
    blended_per_unit = calc.get("blended_per_unit", 0)
    price_range_low = calc.get("price_range_low", 0)
    price_range_high = calc.get("price_range_high", 0)
    flags = calc.get("flags", {})

    schedule_rows = ""
    phase_map = {
        "planning": "תכנון ורישוי",
        "excavation": "חפירה ודיפון",
        "underground": "שלד תת\"ק",
        "above_ground": "שלד עילי",
        "finishes": "גמרים / מעטפת / מערכות",
        "handover": "מסירות / טופס 4",
    }

    for key, name in phase_map.items():
        months = schedule.get(key, 0)
        if months:
            schedule_rows += f"<tr><td>{name}</td><td>{months}</td></tr>"

    pricing_rows = ""
    for pc in phase_costs:
        pricing_rows += f"""<tr>
            <td>{pc['phase_name']}</td>
            <td>{pc['months']}</td>
            <td>{pc['adjusted_rate']:,.0f} ₪</td>
            <td>{pc['phase_total']:,.0f} ₪</td>
        </tr>"""

    status_color = {
        "OK": "green",
        "HIGH": "orange",
        "LOW": "red"
    }.get(flags.get("price_status_code", "OK"), "gray")

    html = f"""<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: Arial, sans-serif; direction: rtl; padding: 20px; }}
  h1 {{ color: #1F3864; }}
  h2 {{ color: #2E75B6; border-bottom: 1px solid #ccc; padding-bottom: 5px; }}
  table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
  th, td {{ border: 1px solid #ddd; padding: 8px; text-align: right; }}
  th {{ background: #1F3864; color: white; }}
  .flag {{ padding: 8px; border-radius: 4px; margin: 5px 0; }}
  .summary-box {{ background: #f0f4ff; padding: 15px; border-radius: 8px; margin: 10px 0; }}
</style>
</head>
<body>
<h1>AM הנדסה — הצעת מחיר</h1>
<h2>פרטי הפרויקט</h2>
<p><b>פרויקט:</b> {p.project_name} | <b>לקוח:</b> {p.client_name} | <b>עיר:</b> {p.location_city}</p>
<p><b>סוג:</b> {p.project_type} | <b>יח"ד:</b> {p.num_units:,} | <b>קומות:</b> {p.num_floors_above}</p>

<h2>לוח זמנים</h2>
<table><tr><th>שלב</th><th>חודשים</th></tr>{schedule_rows}</table>
<p><b>סה"כ:</b> {schedule.get('total_months', 0)} חודשים</p>

<h2>תמחור לפי שלבים</h2>
<table>
  <tr><th>שלב</th><th>חודשים</th><th>תעריף חודשי</th><th>עלות שלב</th></tr>
  {pricing_rows}
</table>

<div class="summary-box">
  <h2>סיכום כלכלי</h2>
  <p><b>הצעה כוללת מומלצת:</b> {blended_total:,.0f} ₪</p>
  <p><b>מחיר ליח"ד:</b> {blended_per_unit:,.0f} ₪</p>
  <p><b>טווח מומלץ:</b> {price_range_low:,.0f} – {price_range_high:,.0f} ₪/יח"ד</p>
  <div class="flag" style="background: {status_color}20; border-right: 4px solid {status_color}">
    <b>סטטוס:</b> {flags.get('price_status_label', '')}
    {f" | <b>המלצה:</b> {flags.get('recommendation', '')}" if flags.get('recommendation') else ""}
  </div>
  {"<div class='flag' style='background: #fff4e5; border-right: 4px solid orange'>⚠️ אין מספיק פרויקטים דומים לביסוס חזק</div>" if flags.get('low_comparables_warning') else ""}
</div>
</body></html>"""

    return HTMLResponse(content=html)