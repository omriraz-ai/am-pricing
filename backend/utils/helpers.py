from typing import Dict


def format_currency(amount: float) -> str:
    """פורמט מטבע ישראלי: 1,234,567 ₪"""
    return f"{amount:,.0f} ₪"


def format_currency_per_unit(amount: float) -> str:
    """פורמט מחיר ליח\"ד."""
    return f"{amount:,.0f} ₪/יח\"ד"


def get_config_value(config: Dict[str, float], key: str, default: float = 0.0) -> float:
    """שליפת ערך מתוך מפתח config."""
    return config.get(key, default)


def get_tier(num_units: int, config: Dict[str, float]) -> str:
    """קביעת Tier לפי מספר יח\"ד — בדיוק כמו האקסל."""
    if num_units <= config.get("tier_S_max", 40):
        return "S"
    elif num_units <= config.get("tier_M_max", 120):
        return "M"
    elif num_units <= config.get("tier_L_max", 400):
        return "L"
    else:
        return "XL"


def get_base_rate(tier: str, phase_key: str, config: Dict[str, float]) -> float:
    """שליפת תעריף בסיס לפי Tier ושלב."""
    key = f"base_rate_{phase_key}_{tier}"
    return config.get(key, 0.0)


PHASE_NAMES = {
    "planning": "תכנון ורישוי",
    "excavation": "חפירה ודיפון",
    "underground": "שלד תת\"ק",
    "above_ground": "שלד עילי",
    "finishes": "גמרים / מעטפת / מערכות",
    "handover": "מסירות / טופס 4",
}

PHASE_KEYS = list(PHASE_NAMES.keys())
