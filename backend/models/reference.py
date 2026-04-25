from pydantic import BaseModel
from typing import Optional


class ReferenceProjectResponse(BaseModel):
    """פרויקט מבסיס האמת."""
    id: str
    project_name: str
    location_city: str
    project_type: str
    num_units: int
    num_floors_above: Optional[int]
    num_floors_underground: Optional[float]
    execution_phases: int
    total_fee: Optional[float]
    fee_per_unit: Optional[float]
    timeline_planning: Optional[int]
    timeline_excavation: Optional[int]
    timeline_underground: Optional[int]
    timeline_above_ground: Optional[int]
    timeline_finishes: Optional[int]
    timeline_handover: Optional[int]
    tier: Optional[str]
    source_type: str
    notes: Optional[str]

    class Config:
        from_attributes = True


class SaveToDbRequest(BaseModel):
    """בקשת שמירה לבסיס הנתונים — שלב נפרד לאחר אישור ההצעה."""
    project_id: str
    approved_fee: float
    source_label: str = "הזנה ידנית מאושרת"


class ProposalRequest(BaseModel):
    """בקשת יצירת הצעת מחיר."""
    project_id: str
