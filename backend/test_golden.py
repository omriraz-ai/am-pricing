"""
בדיקות Golden — ערכים מגיליון 'חישוב' באקסל.
מריץ ישירות ב-Python ללא framework.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.rules_engine import calculate_rules_engine
from services.comparables import find_comparables, get_reference_per_unit, count_above_threshold
from services.pricing_engine import calculate_final_price
from utils.helpers import get_tier


# ── נתוני קלט (FOREST ירושלים) ──────────────────────────────
INPUT_PROJECT = {
    "num_units": 261,
    "project_type": "מגדל",
    "pricing_region": "תל אביב / ירושלים",
    "execution_phases": 1,
    "manual_multiplier": 1.0,
    "timeline": {
        "planning": 15,
        "excavation": 11,
        "underground": 8,
        "above_ground": 19,
        "finishes": 13,
        "handover": 3,
    },
}

# ── ערכים צפויים (מהאקסל) ─────────────────────────────────────
EXPECTED = {
    "tier": "L",
    "multiplier_project_type": 1.35,
    "multiplier_region": 1.1,
    "multiplier_phases": 1.0,
    "total_months": 69,
    "rules_engine_total": 6927525.0,
    "rules_engine_per_unit": 26542.24,
    "reference_price_per_unit": 18390.80,
    "blended_total": 5438257.5,
    "blended_per_unit": 20836.24,
    "price_range_low": 18753,
    "price_range_high": 22920,
    "phase_costs": {
        "planning":     {"months": 15, "adjusted_rate": 51975.0,  "phase_total": 779625.0},
        "excavation":   {"months": 11, "adjusted_rate": 89100.0,  "phase_total": 980100.0},
        "underground":  {"months": 8,  "adjusted_rate": 111375.0, "phase_total": 891000.0},
        "above_ground": {"months": 19, "adjusted_rate": 111375.0, "phase_total": 2116125.0},
        "finishes":     {"months": 13, "adjusted_rate": 133650.0, "phase_total": 1737450.0},
        "handover":     {"months": 3,  "adjusted_rate": 141075.0, "phase_total": 423225.0},
    },
}

CONFIG = {
    "tier_S_max": 40, "tier_M_max": 120, "tier_L_max": 400, "tier_XL_max": 9999,
    "multiplier_residential": 1.0, "multiplier_mixed_use": 1.1,
    "multiplier_tower": 1.35, "multiplier_urban_renewal": 1.2,
    "multiplier_demolish_rebuild": 1.15,
    "multiplier_region_tlv_jlm": 1.1, "multiplier_region_gush_dan": 1.0,
    "multiplier_region_other": 0.95,
    "multiplier_phases_1": 1.0, "multiplier_phases_2": 1.15, "multiplier_phases_3": 1.25,
    "base_rate_planning_S": 18000, "base_rate_planning_M": 25000,
    "base_rate_planning_L": 35000, "base_rate_planning_XL": 40000,
    "base_rate_excavation_S": 35000, "base_rate_excavation_M": 45000,
    "base_rate_excavation_L": 60000, "base_rate_excavation_XL": 70000,
    "base_rate_underground_S": 45000, "base_rate_underground_M": 60000,
    "base_rate_underground_L": 75000, "base_rate_underground_XL": 100000,
    "base_rate_above_ground_S": 45000, "base_rate_above_ground_M": 60000,
    "base_rate_above_ground_L": 75000, "base_rate_above_ground_XL": 130000,
    "base_rate_finishes_S": 55000, "base_rate_finishes_M": 70000,
    "base_rate_finishes_L": 90000, "base_rate_finishes_XL": 150000,
    "base_rate_handover_S": 55000, "base_rate_handover_M": 70000,
    "base_rate_handover_L": 95000, "base_rate_handover_XL": 150000,
    "weight_rules_engine": 0.3, "weight_history": 0.7,
    "similarity_threshold": 60,
}


def approx_equal(a: float, b: float, tol: float = 1.0) -> bool:
    """שוויון בקירוב — סבלנות של ₪1."""
    return abs(a - b) <= tol


def test_tier():
    tier = get_tier(261, CONFIG)
    assert tier == "L", f"Tier שגוי: ציפינו L, קיבלנו {tier}"
    print("✅ Tier: L")


def test_rules_engine():
    result = calculate_rules_engine(
        num_units=INPUT_PROJECT["num_units"],
        project_type=INPUT_PROJECT["project_type"],
        pricing_region=INPUT_PROJECT["pricing_region"],
        execution_phases=INPUT_PROJECT["execution_phases"],
        manual_multiplier=INPUT_PROJECT["manual_multiplier"],
        timeline=INPUT_PROJECT["timeline"],
        config=CONFIG,
    )

    assert result["tier"] == EXPECTED["tier"]
    assert result["multiplier_project_type"] == EXPECTED["multiplier_project_type"]
    assert result["multiplier_region"] == EXPECTED["multiplier_region"]
    assert result["multiplier_phases"] == EXPECTED["multiplier_phases"]
    print(f"✅ מכפילים: {result['multiplier_project_type']} × {result['multiplier_region']} × {result['multiplier_phases']}")

    total_months = sum(INPUT_PROJECT["timeline"].values())
    assert total_months == EXPECTED["total_months"], f"סה\"כ חודשים: ציפינו {EXPECTED['total_months']}, קיבלנו {total_months}"
    print(f"✅ סה\"כ חודשים: {total_months}")

    assert approx_equal(result["rules_engine_total"], EXPECTED["rules_engine_total"]), \
        f"סה\"כ מנוע חוקים: ציפינו {EXPECTED['rules_engine_total']:,.0f}, קיבלנו {result['rules_engine_total']:,.0f}"
    print(f"✅ מנוע חוקים סה\"כ: {result['rules_engine_total']:,.0f} ₪")

    phase_key_map = {
        "תכנון ורישוי": "planning",
        "חפירה ודיפון": "excavation",
        'שלד תת"ק': "underground",
        "שלד עילי": "above_ground",
        "גמרים / מעטפת / מערכות": "finishes",
        "מסירות / טופס 4": "handover",
    }
    for pc in result["phase_costs"]:
        key = phase_key_map.get(pc.phase_name)
        if not key:
            continue
        exp = EXPECTED["phase_costs"][key]
        assert approx_equal(pc.adjusted_rate, exp["adjusted_rate"]), \
            f"{pc.phase_name} adjusted_rate: ציפינו {exp['adjusted_rate']}, קיבלנו {pc.adjusted_rate}"
        assert approx_equal(pc.phase_total, exp["phase_total"]), \
            f"{pc.phase_name} phase_total: ציפינו {exp['phase_total']}, קיבלנו {pc.phase_total}"
        print(f"  ✅ {pc.phase_name}: {pc.adjusted_rate:,.0f} × {pc.months} = {pc.phase_total:,.0f} ₪")

    return result


def test_final_price(rules_result):
    reference_per_unit = EXPECTED["reference_price_per_unit"]  # מהבסיס — FOREST עצמו
    final = calculate_final_price(
        rules_engine_total=rules_result["rules_engine_total"],
        rules_engine_per_unit=rules_result["rules_engine_per_unit"],
        reference_price_per_unit=reference_per_unit,
        num_units=261,
        config=CONFIG,
    )

    assert approx_equal(final["blended_total"], EXPECTED["blended_total"], tol=10), \
        f"blended_total: ציפינו {EXPECTED['blended_total']:,.0f}, קיבלנו {final['blended_total']:,.0f}"
    print(f"✅ הצעה סופית: {final['blended_total']:,.0f} ₪")

    assert approx_equal(final["blended_per_unit"], EXPECTED["blended_per_unit"], tol=5), \
        f"blended_per_unit: ציפינו {EXPECTED['blended_per_unit']:,.0f}, קיבלנו {final['blended_per_unit']:,.0f}"
    print(f"✅ מחיר ליח\"ד: {final['blended_per_unit']:,.0f} ₪")

    assert approx_equal(final["price_range_low"], EXPECTED["price_range_low"], tol=50), \
        f"price_range_low: ציפינו {EXPECTED['price_range_low']}, קיבלנו {final['price_range_low']}"
    assert approx_equal(final["price_range_high"], EXPECTED["price_range_high"], tol=50), \
        f"price_range_high: ציפינו {EXPECTED['price_range_high']}, קיבלנו {final['price_range_high']}"
    print(f"✅ טווח: {final['price_range_low']:,.0f} – {final['price_range_high']:,.0f} ₪")


def run_all():
    print("\n" + "="*50)
    print("בדיקות Golden — FOREST ירושלים")
    print("="*50 + "\n")
    try:
        test_tier()
        rules_result = test_rules_engine()
        test_final_price(rules_result)
        print("\n" + "="*50)
        print("✅ כל הבדיקות עברו בהצלחה!")
        print("="*50)
    except AssertionError as e:
        print(f"\n❌ בדיקה נכשלה: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_all()
