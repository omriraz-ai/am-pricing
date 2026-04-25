from typing import List, Optional


TIER_ORDER = ["S", "M", "L", "XL"]


def normalize_floors_list(
    floors_list: Optional[List[int]],
    num_floors_above: Optional[int],
) -> List[int]:
    """
    מחזיר רשימת קומות תקינה עם תאימות לאחור.

    סדר עדיפות:
    1. אם התקבלה floors_list עם ערכים -> משתמשים בה
    2. אחרת, אם יש num_floors_above -> מחזירים אותו כרשימה עם איבר אחד
    3. אחרת -> רשימה ריקה
    """
    if floors_list:
        return [int(x) for x in floors_list if x is not None and int(x) > 0]

    if num_floors_above is not None and int(num_floors_above) > 0:
        return [int(num_floors_above)]

    return []


def calculate_effective_floors(floors_list: List[int]) -> float:
    """
    מחשב קומות אפקטיביות:
    70% מהמבנה הגבוה ביותר + 30% מממוצע הגבהים.
    """
    if not floors_list:
        return 0.0

    max_floors = max(floors_list)
    avg_floors = sum(floors_list) / len(floors_list)
    return 0.7 * max_floors + 0.3 * avg_floors


def calculate_height_penalty(max_floors: int) -> float:
    """
    מחשב קנס מורכבות מדורג לפי מספר הקומות המקסימלי.
    הקנס מיועד להשתלב במכפיל המורכבות בלבד.
    """
    if max_floors <= 25:
        return 1.0
    if max_floors <= 30:
        return 1.08

    extra = (max_floors - 30) * 0.015
    return min(1.08 + extra, 1.20)


def calculate_weighted_timeline_floors(effective_floors: float) -> float:
    """
    מחשב קומות משוקללות לצורך לו"ז.
    עד 25 קומות - ללא שינוי.
    מעל 25 קומות - האטה לוגיסטית.
    """
    if effective_floors <= 25:
        return effective_floors

    return 25 + (effective_floors - 25) * 1.5


def bump_tier_once(base_tier: str) -> str:
    """
    מעלה Tier בדרגה אחת בלבד.
    אם כבר נמצא בדרגה העליונה - מחזיר את אותו ערך.
    """
    if base_tier not in TIER_ORDER:
        return base_tier

    idx = TIER_ORDER.index(base_tier)
    if idx >= len(TIER_ORDER) - 1:
        return base_tier

    return TIER_ORDER[idx + 1]


def should_bump_tier(
    effective_floors: float,
    max_floors: int,
) -> bool:
    """
    קובע האם יש להעלות Tier בדרגה אחת לפי כלל הגובה.
    """
    return effective_floors > 25 or max_floors > 25


def build_height_metrics(
    floors_list: Optional[List[int]],
    num_floors_above: Optional[int],
) -> dict:
    """
    פונקציית מעטפת נוחה לשימוש ב-route:
    - מנרמלת קלט
    - מחשבת max / effective / penalty / weighted timeline
    """
    normalized = normalize_floors_list(floors_list, num_floors_above)
    max_floors = max(normalized) if normalized else 0
    effective_floors = calculate_effective_floors(normalized)
    height_penalty = calculate_height_penalty(max_floors)
    weighted_timeline_floors = calculate_weighted_timeline_floors(effective_floors)

    return {
        "floors_list": normalized,
        "max_floors": max_floors,
        "effective_floors": effective_floors,
        "height_penalty": height_penalty,
        "weighted_timeline_floors": weighted_timeline_floors,
        "should_bump_tier": should_bump_tier(effective_floors, max_floors),
    }