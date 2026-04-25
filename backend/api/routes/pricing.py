from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from db_models import Project, PricingConfig, ReferenceProject
from models.pricing import CalculateRequest, CalculationResult
from services.rules_engine import calculate_rules_engine
from services.comparables import find_comparables, get_reference_per_unit, count_above_threshold
from services.schedule_engine import calculate_schedule
from services.pricing_engine import calculate_final_price, build_flags, get_special_conditions
from services.height_complexity import build_height_metrics
from services.height_complexity import bump_tier_once
from utils.helpers import get_tier

router = APIRouter(prefix="/pricing", tags=["תמחור"])


def _load_config(db: Session) -> dict:
    """טעינת כל המקדמים מה-DB."""
    rows = db.query(PricingConfig).all()
    return {r.config_key: r.config_value for r in rows}


def _load_reference_projects(db: Session) -> list:
    return db.query(ReferenceProject).all()


@router.post("/calculate", summary="חישוב מלא — Tier + לוז + תמחור + דמיון")
def calculate(req: CalculateRequest, db: Session = Depends(get_db)):
    p = db.query(Project).filter(Project.id == req.project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="פרויקט לא נמצא")

    config = _load_config(db)
    reference_projects = _load_reference_projects(db)
    # ── Height Complexity (שלב 1) ─────────────────────────────

    # ── Height Complexity (שלב 1) ─────────────────────────────
    height_metrics = build_height_metrics(
        floors_list=req.floors_list,
        num_floors_above=p.num_floors_above,
    )

    height_penalty = height_metrics["height_penalty"]

    base_multiplier = p.manual_complexity_multiplier or 1.0
    final_multiplier = base_multiplier * height_penalty

    # לוח זמנים ידני
    manual_timeline = {
        "planning": p.timeline_planning,
        "excavation": p.timeline_excavation,
        "underground": p.timeline_underground,
        "above_ground": p.timeline_above_ground,
        "finishes": p.timeline_finishes,
        "handover": p.timeline_handover,
    }

    # שלב 1 — פרויקטים דומים
    comparables = find_comparables(
        num_units=p.num_units,
        project_type=p.project_type,
        location_city=p.location_city,
        num_floors_above=p.num_floors_above,
        execution_phases=p.execution_phases,
        reference_projects=reference_projects,
        threshold=config.get("similarity_threshold", 60),
    )

    # שלב 2 — לוח זמנים
    # שלב 2 — לוח זמנים
    base_tier_for_schedule = get_tier(p.num_units, config)

    if height_metrics["should_bump_tier"]:
        tier_for_schedule = bump_tier_once(base_tier_for_schedule)
    else:
        tier_for_schedule = base_tier_for_schedule

    schedule = calculate_schedule(
        tier=tier_for_schedule,
        manual_timeline=manual_timeline,
        reference_projects=reference_projects,
        comparables=comparables,
        override_timeline=req.override_timeline,
    )

    timeline_for_rules = {
        "planning": schedule.planning,
        "excavation": schedule.excavation,
        "underground": schedule.underground,
        "above_ground": schedule.above_ground,
        "finishes": schedule.finishes,
        "handover": schedule.handover,
    }

    # ── Tier Adjustment לפי גובה ─────────────────────────────
    base_tier = get_tier(p.num_units, config)

    tier_override = None
    if height_metrics["should_bump_tier"]:
        tier_override = bump_tier_once(base_tier)

    # שלב 3 — מנוע חוקים (30%)
    rules = calculate_rules_engine(
    num_units=p.num_units,
    project_type=p.project_type,
    pricing_region=p.pricing_region or "גוש דן",
    execution_phases=p.execution_phases,
    manual_multiplier=final_multiplier,
    timeline=timeline_for_rules,
    config=config,
    tier_override=tier_override,
)

    # שלב 4 — ממוצע היסטורי (70%)
    reference_per_unit = get_reference_per_unit(
        comparables,
        threshold=config.get("similarity_threshold", 60),
    )
    num_above = count_above_threshold(comparables, config.get("similarity_threshold", 60))

    # שלב 5 — כיול סופי
    final = calculate_final_price(
        rules_engine_total=rules["rules_engine_total"],
        rules_engine_per_unit=rules["rules_engine_per_unit"],
        reference_price_per_unit=reference_per_unit,
        num_units=p.num_units,
        config=config,
    )

    # שלב 6 — דגלים
    missing = []
    if not p.plot_area_sqm:
        missing.append("שטח מגרש")
    if not p.num_buildings:
        missing.append("מספר מבנים")

    flags = build_flags(
        blended_per_unit=final["blended_per_unit"],
        price_range_low=final["price_range_low"],
        price_range_high=final["price_range_high"],
        num_comparables_above_threshold=num_above,
        override_active=(p.manual_complexity_multiplier or 1.0) != 1.0,
        override_reason=p.manual_override_reason,
        missing_fields=missing,
        project_type=p.project_type,
        num_floors_above=p.num_floors_above or 0,
    )

    result = {
        "tier": rules["tier"],
        "multiplier_project_type": rules["multiplier_project_type"],
        "multiplier_region": rules["multiplier_region"],
        "multiplier_phases": rules["multiplier_phases"],
        "multiplier_manual": rules["multiplier_manual"],
        "schedule": schedule.dict(),
        "phase_costs": [pc.dict() for pc in rules["phase_costs"]],
        "rules_engine_total": rules["rules_engine_total"],
        "rules_engine_per_unit": rules["rules_engine_per_unit"],
        "comparable_projects": [c.dict() for c in comparables],
        "num_comparable_above_threshold": num_above,
        "reference_price_per_unit": reference_per_unit,
        "blended_total": final["blended_total"],
        "blended_per_unit": final["blended_per_unit"],
        "price_range_low": final["price_range_low"],
        "price_range_high": final["price_range_high"],
        "flags": flags.dict(),
    }

    # ── Manual Pricing Override ─────────────────────────────
    if p.use_manual_pricing and p.manual_total_price:
        result["blended_total"] = p.manual_total_price

        if p.num_units and p.num_units > 0:
            result["blended_per_unit"] = round(p.manual_total_price / p.num_units, 2)

       # ── Exception Pricing Override ──────────────────────────
    if p.is_exception_pricing and p.exception_pricing_override:
        override = p.exception_pricing_override

        if isinstance(override, dict):
            if "schedule" in override and isinstance(override["schedule"], dict):
                result["schedule"].update(override["schedule"])

            if "blended_total" in override:
                result["blended_total"] = override["blended_total"]

            if "blended_per_unit" in override:
                result["blended_per_unit"] = override["blended_per_unit"]

    # שמירת תוצאה בפרויקט
    p.calculation_result = result
    p.status = "calculated"
    db.commit()

    return result


@router.post("/comparables", summary="פרויקטים דומים בלבד")
def get_comparables(req: CalculateRequest, db: Session = Depends(get_db)):
    p = db.query(Project).filter(Project.id == req.project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="פרויקט לא נמצא")

    config = _load_config(db)
    reference_projects = _load_reference_projects(db)

    comparables = find_comparables(
        num_units=p.num_units,
        project_type=p.project_type,
        location_city=p.location_city,
        num_floors_above=p.num_floors_above,
        execution_phases=p.execution_phases,
        reference_projects=reference_projects,
        threshold=config.get("similarity_threshold", 60),
    )
    return [c.dict() for c in comparables]
