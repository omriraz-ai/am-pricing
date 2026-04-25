"""
מנוע חוקים — 30% מהמחיר הסופי.
לוגיקה מדויקת לפי גיליון 'חישוב' ו'מקדמים' באקסל.
"""
from typing import Dict, List
from models.pricing import PhaseResult
from utils.helpers import get_tier, get_base_rate, PHASE_KEYS, PHASE_NAMES
from utils.region_mapper import region_to_multiplier_key


def get_project_type_multiplier_key(project_type: str) -> str:
    mapping = {
        "מגורים": "multiplier_residential",
        "עירוב שימושים": "multiplier_mixed_use",
        "מגדל": "multiplier_tower",
        "פינוי בינוי": "multiplier_urban_renewal",
        "הריסה ובנייה": "multiplier_demolish_rebuild",
        "מסחרי": "multiplier_residential",
        "ציבורי": "multiplier_residential",
    }
    return mapping.get(project_type, "multiplier_residential")


def get_phases_multiplier_key(execution_phases: int) -> str:
    if execution_phases == 1:
        return "multiplier_phases_1"
    elif execution_phases == 2:
        return "multiplier_phases_2"
    else:
        return "multiplier_phases_3"


def calculate_rules_engine(
    num_units: int,
    project_type: str,
    pricing_region: str,
    execution_phases: int,
    manual_multiplier: float,
    timeline: Dict[str, int],
    config: Dict[str, float],
    tier_override: str | None = None,
) -> Dict:
    """
    חישוב מנוע חוקים — 30%.
    מחזיר: tier, מכפילים, עלויות לפי שלב, סה"כ.
    """
    # שלב 1 — Tier
    base_tier = get_tier(num_units, config)
    tier = tier_override or base_tier

    # שלב 2-4 — מכפילים
    type_mult = config.get(get_project_type_multiplier_key(project_type), 1.0)
    region_mult = config.get(region_to_multiplier_key(pricing_region), 1.0)
    phases_mult = config.get(get_phases_multiplier_key(execution_phases), 1.0)
    manual_mult = manual_multiplier

    combined_mult = type_mult * region_mult * phases_mult * manual_mult

    # שלב 5 — עלות לכל שלב
    phase_costs: List[PhaseResult] = []
    rules_total = 0.0

    for phase_key in PHASE_KEYS:
        months = timeline.get(phase_key, 0)
        if months == 0:
            continue

        base_rate = get_base_rate(tier, phase_key, config)
        adjusted_rate = base_rate * combined_mult
        phase_total = adjusted_rate * months
        rules_total += phase_total

        phase_costs.append(PhaseResult(
            phase_name=PHASE_NAMES[phase_key],
            months=months,
            base_rate=base_rate,
            adjusted_rate=round(adjusted_rate, 2),
            phase_total=round(phase_total, 2),
        ))

    rules_per_unit = rules_total / num_units if num_units > 0 else 0

    return {
        "tier": tier,
        "multiplier_project_type": type_mult,
        "multiplier_region": region_mult,
        "multiplier_phases": phases_mult,
        "multiplier_manual": manual_mult,
        "phase_costs": phase_costs,
        "rules_engine_total": round(rules_total, 2),
        "rules_engine_per_unit": round(rules_per_unit, 2),
    }
