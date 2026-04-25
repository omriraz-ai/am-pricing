"""
מנוע דמיון — מציאת פרויקטים דומים מבסיס הנתונים.
אלגוריתם ציון: 100 נקודות (יח"ד=30, סוג=25, עיר=20, קומות=15, שלביות=10).
"""
from typing import List, Optional
from models.pricing import ComparableResult, ScoreBreakdown


def _score_units(new_units: int, ref_units: int) -> float:
    """30 נקודות — קרבה במספר יח"ד."""
    if ref_units == 0:
        return 0.0
    delta = abs(new_units - ref_units) / max(new_units, ref_units)
    return round(30 * (1 - delta), 2)


def _score_project_type(new_type: str, ref_type: str) -> float:
    """25 נקודות — זהות סוג פרויקט."""
    return 25.0 if new_type == ref_type else 0.0


def _score_city(new_city: str, ref_city: str) -> float:
    """20 נקודות — אותה עיר."""
    return 20.0 if new_city.strip() == ref_city.strip() else 0.0


def _score_floors(new_floors: Optional[int], ref_floors: Optional[int]) -> float:
    """15 נקודות — קרבה במספר קומות."""
    if new_floors is None or ref_floors is None:
        return 5.0  # ברירת מחדל כשחסר
    delta = abs(new_floors - ref_floors)
    if delta == 0:
        return 15.0
    elif delta <= 3:
        return 10.0
    elif delta <= 7:
        return 5.0
    return 0.0


def _score_phases(new_phases: int, ref_phases: int) -> float:
    """10 נקודות — זהות שלביות."""
    return 10.0 if new_phases == ref_phases else 0.0


def _get_match_level(score: float) -> str:
    if score >= 80:
        return "דמיון גבוה"
    elif score >= 60:
        return "דמיון בינוני"
    return "דמיון נמוך"


def find_comparables(
    num_units: int,
    project_type: str,
    location_city: str,
    num_floors_above: Optional[int],
    execution_phases: int,
    reference_projects: list,
    threshold: float = 60.0,
    top_n: int = 3,
) -> List[ComparableResult]:
    """
    מחזיר Top N פרויקטים דומים מעל סף הדמיון.
    """
    scored = []

    for ref in reference_projects:
        breakdown = ScoreBreakdown(
            units=_score_units(num_units, ref.num_units or 0),
            project_type=_score_project_type(project_type, ref.project_type),
            city=_score_city(location_city, ref.location_city),
            floors=_score_floors(num_floors_above, ref.num_floors_above),
            phases=_score_phases(execution_phases, ref.execution_phases),
        )
        total_score = (
            breakdown.units
            + breakdown.project_type
            + breakdown.city
            + breakdown.floors
            + breakdown.phases
        )

        scored.append(ComparableResult(
            project_name=ref.project_name,
            location_city=ref.location_city,
            project_type=ref.project_type,
            num_units=ref.num_units,
            num_floors_above=ref.num_floors_above,
            execution_phases=ref.execution_phases,
            fee_per_unit=ref.fee_per_unit or 0,
            total_fee=ref.total_fee,
            tier=ref.tier,
            source_type=ref.source_type,
            similarity_score=round(total_score, 1),
            match_level=_get_match_level(total_score),
            score_breakdown=breakdown,
        ))

    # מיון יורד לפי ציון
    scored.sort(key=lambda x: x.similarity_score, reverse=True)

    # החזרת Top N (ללא סינון threshold — מוצגים הכל, threshold לכיול בלבד)
    return scored[:top_n]


def get_reference_per_unit(
    comparables: List[ComparableResult],
    threshold: float = 60.0,
) -> Optional[float]:
    """
    ממוצע fee_per_unit מפרויקטים שעברו את הסף.
    מחזיר None אם אין מספיק.
    """
    above = [c for c in comparables if c.similarity_score >= threshold and c.fee_per_unit > 0]
    if not above:
        return None
    return sum(c.fee_per_unit for c in above) / len(above)


def count_above_threshold(comparables: List[ComparableResult], threshold: float = 60.0) -> int:
    return sum(1 for c in comparables if c.similarity_score >= threshold)
