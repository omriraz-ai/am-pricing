"""
טעינת נתוני בסיס — 8 פרויקטים + מקדמים מהאקסל.
מריץ פעם אחת בהפעלה הראשונה.
"""
from sqlalchemy.orm import Session
from db_models import ReferenceProject, PricingConfig


REFERENCE_PROJECTS = [
    {
        "project_name": "FOREST ירושלים",
        "location_city": "ירושלים",
        "project_type": "מגדל",
        "num_units": 261,
        "num_floors_above": 30,
        "num_floors_underground": 5,
        "execution_phases": 1,
        "total_fee": 4800000,
        "fee_per_unit": 18390.80,
        "timeline_planning": 12,
        "timeline_excavation": 12,
        "timeline_underground": 7,
        "timeline_above_ground": 20,
        "timeline_finishes": 12,
        "timeline_handover": 3,
        "tier": "L",
        "source_type": "הצעה אמיתית",
    },
    {
        "project_name": "מכבי יפו",
        "location_city": "תל אביב",
        "project_type": "פינוי בינוי",
        "num_units": 412,
        "num_floors_above": 13,
        "num_floors_underground": 4,
        "execution_phases": 2,
        "total_fee": 5438400,
        "fee_per_unit": 13200,
        "tier": "XL",
        "source_type": "הצעה אמיתית",
    },
    {
        "project_name": "השיטה חולון",
        "location_city": "חולון",
        "project_type": "פינוי בינוי",
        "num_units": 472,
        "num_floors_above": 36,
        "num_floors_underground": 2,
        "execution_phases": 1,
        "total_fee": 6372000,
        "fee_per_unit": 13500,
        "tier": "XL",
        "source_type": "מצגת/השוואה מאומתת",
    },
    {
        "project_name": "הטייסים ההסתדרות",
        "location_city": "נס ציונה",
        "project_type": "מגורים",
        "num_units": 700,
        "num_floors_above": 14,
        "num_floors_underground": 2,
        "execution_phases": 1,
        "total_fee": 9450000,
        "fee_per_unit": 13500,
        "tier": "XL",
        "source_type": "הצעה אמיתית",
    },
    {
        "project_name": "ארלוזורוב ארבע הארצות",
        "location_city": "תל אביב",
        "project_type": "הריסה ובנייה",
        "num_units": 96,
        "num_floors_above": 8,
        "num_floors_underground": 2,
        "execution_phases": 1,
        "total_fee": 2375000,
        "fee_per_unit": 24739.58,
        "tier": "M",
        "source_type": "RFP/הצעה אמיתית",
    },
    {
        "project_name": "לב הבקעה מגרש 13",
        "location_city": "גני תקווה",
        "project_type": "עירוב שימושים",
        "num_units": 95,
        "num_floors_above": 10,
        "num_floors_underground": 2,
        "execution_phases": 1,
        "total_fee": 1650000,
        "fee_per_unit": 17368.42,
        "timeline_planning": 24,
        "timeline_excavation": 8,
        "timeline_underground": 6,
        "timeline_above_ground": 8,
        "timeline_finishes": 12,
        "timeline_handover": 3,
        "tier": "M",
        "source_type": "הצעה אמיתית",
    },
    {
        "project_name": "מגרש 102 קרית אונו",
        "location_city": "קרית אונו",
        "project_type": "עירוב שימושים",
        "num_units": 60,
        "num_floors_above": 12,
        "num_floors_underground": 2,
        "execution_phases": 1,
        "total_fee": 1250000,
        "fee_per_unit": 20833.33,
        "tier": "M",
        "source_type": "הצעה אמיתית",
    },
    {
        "project_name": "הרצליה מגורים",
        "location_city": "הרצליה",
        "project_type": "מגורים",
        "num_units": 33,
        "num_floors_above": 8,
        "num_floors_underground": 3.5,
        "execution_phases": 1,
        "total_fee": 780000,
        "fee_per_unit": 23636.36,
        "timeline_planning": 10,
        "timeline_excavation": 6,
        "timeline_underground": 4,
        "timeline_above_ground": 8,
        "timeline_finishes": 10,
        "timeline_handover": 2,
        "tier": "S",
        "source_type": "הצעה אמיתית",
    },
]

PRICING_CONFIG = {
    # Tier bounds
    "tier_S_min": 0, "tier_S_max": 40,
    "tier_M_min": 41, "tier_M_max": 120,
    "tier_L_min": 121, "tier_L_max": 400,
    "tier_XL_min": 401, "tier_XL_max": 9999,
    # מכפילי סוג פרויקט
    "multiplier_residential": 1.0,
    "multiplier_mixed_use": 1.1,
    "multiplier_tower": 1.35,
    "multiplier_urban_renewal": 1.2,
    "multiplier_demolish_rebuild": 1.15,
    # מכפילי אזור
    "multiplier_region_tlv_jlm": 1.1,
    "multiplier_region_gush_dan": 1.0,
    "multiplier_region_other": 0.95,
    # מכפילי שלביות
    "multiplier_phases_1": 1.0,
    "multiplier_phases_2": 1.15,
    "multiplier_phases_3": 1.25,
    # משקלי מודל (30/70)
    "weight_rules_engine": 0.3,
    "weight_history": 0.7,
    "similarity_threshold": 60,
    # תעריפי בסיס — תכנון
    "base_rate_planning_S": 18000, "base_rate_planning_M": 25000,
    "base_rate_planning_L": 35000, "base_rate_planning_XL": 40000,
    # חפירה
    "base_rate_excavation_S": 35000, "base_rate_excavation_M": 45000,
    "base_rate_excavation_L": 60000, "base_rate_excavation_XL": 70000,
    # שלד תת"ק
    "base_rate_underground_S": 45000, "base_rate_underground_M": 60000,
    "base_rate_underground_L": 75000, "base_rate_underground_XL": 100000,
    # שלד עילי
    "base_rate_above_ground_S": 45000, "base_rate_above_ground_M": 60000,
    "base_rate_above_ground_L": 75000, "base_rate_above_ground_XL": 130000,
    # גמרים
    "base_rate_finishes_S": 55000, "base_rate_finishes_M": 70000,
    "base_rate_finishes_L": 90000, "base_rate_finishes_XL": 150000,
    # מסירות
    "base_rate_handover_S": 55000, "base_rate_handover_M": 70000,
    "base_rate_handover_L": 95000, "base_rate_handover_XL": 150000,
}

CONFIG_DESCRIPTIONS = {
    "weight_rules_engine": "משקל מנוע חוקים (0.3 = 30%)",
    "weight_history": "משקל היסטוריית פרויקטים (0.7 = 70%)",
    "similarity_threshold": "סף דמיון מינימלי לכיול (60)",
    "multiplier_tower": "מכפיל מגדל",
    "multiplier_urban_renewal": "מכפיל פינוי-בינוי",
    "multiplier_region_tlv_jlm": "מכפיל תל אביב / ירושלים",
}


def seed_database(db: Session) -> None:
    """טעינת נתוני בסיס אם הטבלאות ריקות."""

    # בדיקה שבסיס הנתונים עדיין ריק
    if db.query(ReferenceProject).count() > 0:
        print("בסיס הנתונים כבר מכיל נתונים — דילוג על seed")
        return

    print("טוען נתוני בסיס...")

    # טעינת פרויקטים
    for proj_data in REFERENCE_PROJECTS:
        proj = ReferenceProject(**proj_data)
        db.add(proj)

    # טעינת config
    for key, value in PRICING_CONFIG.items():
        cfg = PricingConfig(
            config_key=key,
            config_value=value,
            description=CONFIG_DESCRIPTIONS.get(key, ""),
        )
        db.add(cfg)

    db.commit()
    print(f"נטענו {len(REFERENCE_PROJECTS)} פרויקטים ו-{len(PRICING_CONFIG)} מקדמים")
