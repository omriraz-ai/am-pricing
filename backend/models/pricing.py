from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class PriceStatusCode(str, Enum):
    LOW = "LOW"
    OK = "OK"
    HIGH = "HIGH"


class PhaseResult(BaseModel):
    """תוצאת חישוב לשלב בודד."""
    phase_name: str          # שם השלב בעברית
    months: int
    base_rate: float
    adjusted_rate: float
    phase_total: float


class ScoreBreakdown(BaseModel):
    """פירוט ציון הדמיון לפי ממדים."""
    units: float
    project_type: float
    city: float
    floors: float
    phases: float


class ComparableResult(BaseModel):
    """פרויקט דומה."""
    project_name: str
    location_city: str
    project_type: str
    num_units: int
    num_floors_above: Optional[int]
    execution_phases: int
    fee_per_unit: float
    total_fee: Optional[float]
    tier: Optional[str]
    source_type: str
    similarity_score: float
    match_level: str           # דמיון גבוה / בינוני / נמוך
    score_breakdown: ScoreBreakdown


class ScheduleResult(BaseModel):
    """תוצאת חישוב לוח זמנים."""
    planning: int
    excavation: int
    underground: int
    above_ground: int
    finishes: int
    handover: int
    total_months: int
    source_note: str           # "60% חוקי גודל + 40% בסיס נתונים"


class PricingFlags(BaseModel):
    """דגלי חריגה ואזהרות."""
    price_status_code: PriceStatusCode
    price_status_label: str    # מחיר נמוך / בטווח הרגיל / מחיר גבוה יחסית
    recommendation: Optional[str]
    num_comparables: int
    low_comparables_warning: bool
    override_active: bool
    override_reason: Optional[str]
    missing_fields: List[str]


class CalculationResult(BaseModel):
    """תוצאה מלאה של מנוע החישוב — מקביל לגיליון 'חישוב'."""

    # פרמטרים
    tier: str
    multiplier_project_type: float
    multiplier_region: float
    multiplier_phases: float
    multiplier_manual: float

    # לוח זמנים
    schedule: ScheduleResult

    # עלויות לפי שלב
    phase_costs: List[PhaseResult]

    # מנוע חוקים (30%)
    rules_engine_total: float
    rules_engine_per_unit: float

    # פרויקטים דומים (70%)
    comparable_projects: List[ComparableResult]
    num_comparable_above_threshold: int
    reference_price_per_unit: Optional[float]

    # מחיר סופי משוקלל
    blended_total: float
    blended_per_unit: float
    price_range_low: float
    price_range_high: float

    # דגלים
    flags: PricingFlags


class CalculateRequest(BaseModel):
    """בקשת חישוב."""
    project_id: str
    override_timeline: bool = False
    floors_list: Optional[List[int]] = None
