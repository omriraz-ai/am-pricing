"""
מנוע תמחור סופי — כיול 30/70 + טווח + דגלים.
לוגיקה מדויקת לפי גיליון 'חישוב' באקסל.
"""
from typing import List, Optional, Dict
from models.pricing import PricingFlags, PriceStatusCode, CalculationResult, ComparableResult, ScheduleResult, PhaseResult


RANGE_MARGIN = 0.1  # ±10% לטווח המומלץ


def calculate_final_price(
    rules_engine_total: float,
    rules_engine_per_unit: float,
    reference_price_per_unit: Optional[float],
    num_units: int,
    config: Dict[str, float],
) -> Dict:
    """
    כיול סופי: 30% חוקים + 70% היסטוריה.
    אם אין פרויקטים דומים — 100% חוקים.
    """
    weight_rules = config.get("weight_rules_engine", 0.3)
    weight_history = config.get("weight_history", 0.7)

    if reference_price_per_unit and reference_price_per_unit > 0:
        blended_per_unit = (
            weight_rules * rules_engine_per_unit
            + weight_history * reference_price_per_unit
        )
        blended_total = blended_per_unit * num_units
    else:
        # אין פרויקטים דומים — שימוש ב-100% מנוע חוקים
        blended_per_unit = rules_engine_per_unit
        blended_total = rules_engine_total

    price_range_low = round(blended_per_unit * (1 - RANGE_MARGIN))
    price_range_high = round(blended_per_unit * (1 + RANGE_MARGIN))

    return {
        "blended_total": round(blended_total, 2),
        "blended_per_unit": round(blended_per_unit, 2),
        "price_range_low": price_range_low,
        "price_range_high": price_range_high,
    }


def build_flags(
    blended_per_unit: float,
    price_range_low: float,
    price_range_high: float,
    num_comparables_above_threshold: int,
    override_active: bool,
    override_reason: Optional[str],
    missing_fields: List[str],
    project_type: str,
    num_floors_above: int,
) -> PricingFlags:
    """בניית דגלי חריגה — מקביל לגיליון 'חישוב' קטע 'דגלי חריגה'."""

    # סטטוס מחיר
    if blended_per_unit < price_range_low:
        status_code = PriceStatusCode.LOW
        status_label = "מחיר נמוך מהרגיל"
    elif blended_per_unit > price_range_high:
        status_code = PriceStatusCode.HIGH
        status_label = "מחיר גבוה יחסית"
    else:
        status_code = PriceStatusCode.OK
        status_label = "בטווח הרגיל"

    # המלצה
    recommendation = None
    if status_code == PriceStatusCode.HIGH:
        reasons = []
        if project_type == "מגדל":
            reasons.append("מגדל")
        if num_floors_above and num_floors_above > 20:
            reasons.append("מורכבות תת קרקע")
        if reasons:
            recommendation = f"מומלץ לנמק: {' / '.join(reasons)}"
        else:
            recommendation = "מומלץ לנמק את המחיר הגבוה"

    return PricingFlags(
        price_status_code=status_code,
        price_status_label=status_label,
        recommendation=recommendation,
        num_comparables=num_comparables_above_threshold,
        low_comparables_warning=num_comparables_above_threshold < 2,
        override_active=override_active,
        override_reason=override_reason,
        missing_fields=missing_fields,
    )


def get_special_conditions(
    execution_phases: int,
    project_type: str,
    num_floors_above: int,
    timeline_planning: int,
) -> List[str]:
    """זיהוי בלוקי תנאים מיוחדים שיופיעו בהצעה."""
    conditions = []
    if execution_phases > 1:
        conditions.append("TM01_phases")
    if project_type in ("פינוי בינוי", "הריסה ובנייה"):
        conditions.append("TM02_delays")
    if num_floors_above and num_floors_above > 20:
        conditions.append("TM03_warranty")
    if timeline_planning and timeline_planning > 18:
        conditions.append("TM04_planning_cap")
    return conditions
