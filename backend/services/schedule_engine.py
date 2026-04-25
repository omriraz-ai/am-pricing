"""
מנוע לוח זמנים — 60% חוקי גודל + 40% בסיס נתונים.
לוגיקה מדויקת לפי גיליון 'חישוב' באקסל.
"""
from typing import Dict, List, Optional
from models.pricing import ScheduleResult, ComparableResult

# חוקי בסיס לפי Tier (חודשים) — מגיליון 'חישוב' באקסל
SCHEDULE_RULES: Dict[str, Dict[str, int]] = {
    "planning":     {"S": 10, "M": 12, "L": 17, "XL": 20},
    "excavation":   {"S": 5,  "M": 7,  "L": 10, "XL": 12},
    "underground":  {"S": 4,  "M": 5,  "L": 8,  "XL": 10},
    "above_ground": {"S": 6,  "M": 10, "L": 19, "XL": 24},
    "finishes":     {"S": 8,  "M": 10, "L": 14, "XL": 18},
    "handover":     {"S": 2,  "M": 2,  "L": 3,  "XL": 3},
}

WEIGHT_RULES = 0.6
WEIGHT_HISTORY = 0.4


def _get_historical_avg(phase_key: str, comparables: List[ComparableResult]) -> Optional[float]:
    """ממוצע היסטורי לשלב מפרויקטים דומים שיש להם לוז."""
    timeline_attr = {
        "planning": "timeline_planning",
        "excavation": "timeline_excavation",
        "underground": "timeline_underground",
        "above_ground": "timeline_above_ground",
        "finishes": "timeline_finishes",
        "handover": "timeline_handover",
    }
    # הפרויקטים הדומים הם ComparableResult — אין להם timeline ישיר
    # נשתמש בנתוני הבסיס שנטענו לנו (נועבר כ-reference_projects)
    return None


def calculate_schedule(
    tier: str,
    manual_timeline: Dict[str, Optional[int]],
    reference_projects: list,
    comparables: List[ComparableResult],
    override_timeline: bool = False,
) -> ScheduleResult:
    """
    חישוב לוח זמנים.
    אם override_timeline=True — השתמש בנתונים הידניים בלבד.
    """
    phase_keys = ["planning", "excavation", "underground", "above_ground", "finishes", "handover"]
    result = {}
    used_history = False

    # בניית מפת פרויקטים דומים עם לוז לפי שם פרויקט
    comparable_names = {c.project_name for c in comparables if c.similarity_score >= 60}
    ref_with_timeline = [
        r for r in reference_projects
        if r.project_name in comparable_names and r.timeline_planning is not None
    ]

    for phase_key in phase_keys:
        # בדוק אם יש ערך ידני
        manual_val = manual_timeline.get(phase_key)

        if override_timeline and manual_val:
            result[phase_key] = manual_val
            continue

        rule_val = SCHEDULE_RULES[phase_key].get(tier, 0)

        # ניסיון לממוצע היסטורי
        timeline_attr = f"timeline_{phase_key}" if phase_key != "above_ground" else "timeline_above_ground"
        hist_values = []
        for ref in ref_with_timeline:
            val = getattr(ref, timeline_attr, None)
            if val and val > 0:
                hist_values.append(val)

        if hist_values:
            hist_avg = sum(hist_values) / len(hist_values)
            recommended = round(WEIGHT_RULES * rule_val + WEIGHT_HISTORY * hist_avg)
            used_history = True
        else:
            # אם יש ערך ידני — השתמש בו
            if manual_val:
                recommended = manual_val
            else:
                recommended = rule_val

        result[phase_key] = max(1, recommended)

    total_months = sum(result.values())
    source_note = "60% חוקי גודל + 40% בסיס נתונים" if used_history else "חוקי גודל בלבד"

    return ScheduleResult(
        planning=result["planning"],
        excavation=result["excavation"],
        underground=result["underground"],
        above_ground=result["above_ground"],
        finishes=result["finishes"],
        handover=result["handover"],
        total_months=total_months,
        source_note=source_note,
    )
