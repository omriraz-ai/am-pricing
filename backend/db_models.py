from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, JSON, Numeric, ForeignKey
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.sql import func
import uuid
from database import Base


def gen_uuid():
    return str(uuid.uuid4())


class ReferenceProject(Base):
    """בסיס הנתונים — מקור האמת. נכתב רק לאחר אישור מפורש."""
    __tablename__ = "reference_projects"

    id = Column(String, primary_key=True, default=gen_uuid)
    project_name = Column(String, nullable=False)
    location_city = Column(String, nullable=False)
    project_type = Column(String, nullable=False)
    num_units = Column(Integer, nullable=False)
    num_floors_above = Column(Integer)
    num_floors_underground = Column(Float)
    execution_phases = Column(Integer, nullable=False)
    total_fee = Column(Float)
    fee_per_unit = Column(Float)
    timeline_planning = Column(Integer)
    timeline_excavation = Column(Integer)
    timeline_underground = Column(Integer)
    timeline_above_ground = Column(Integer)
    timeline_finishes = Column(Integer)
    timeline_handover = Column(Integer)
    tier = Column(String)
    source_type = Column(String, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


class PricingConfig(Base):
    """מקדמים וטבלאות תמחור — מקביל לגיליון 'מקדמים'."""
    __tablename__ = "pricing_config"

    id = Column(String, primary_key=True, default=gen_uuid)
    config_key = Column(String, unique=True, nullable=False)
    config_value = Column(Float, nullable=False)
    description = Column(Text)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Project(Base):
    """פרויקטים בעבודה — לא בסיס אמת. נמחקים/מתעדכנים חופשי."""
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=gen_uuid)
    status = Column(String, default="draft")  # draft/calculated/approved/saved_to_db

    # פרויקט טסט — לעולם לא נשמר ל-reference_projects
    is_test = Column(Boolean, default=False, nullable=False)

    is_exception_pricing = Column(Boolean, default=False, nullable=False)

    # סטטוס עסקי — מצב מול הלקוח, נפרד מ-status הטכני
    business_status = Column(String, default="בטיפול", nullable=False)

    # ארכיון — כאשר True הפרויקט לא מוצג ברשימה הפעילה
    is_archived = Column(Boolean, default=False, nullable=False)

    # קלט פרויקט
    project_name = Column(String, nullable=False)
    client_name = Column(String, nullable=False)
    location_city = Column(String, nullable=False)
    pricing_region = Column(String)
    project_type = Column(String, nullable=False)
    pricing_mode = Column(String, default="חודשי")
    num_units = Column(Integer, nullable=False)
    num_buildings = Column(Integer)
    num_floors_above = Column(Integer, nullable=False)
    num_floors_underground = Column(Float)
    execution_phases = Column(Integer, nullable=False, default=1)
    plot_area_sqm = Column(Float)
    area_residential_sqm = Column(Float)
    area_commercial_sqm = Column(Float)
    area_employment_sqm = Column(Float)

    # לוח זמנים
    timeline_planning = Column(Integer)
    timeline_excavation = Column(Integer)
    timeline_underground = Column(Integer)
    timeline_above_ground = Column(Integer)
    timeline_finishes = Column(Integer)
    timeline_handover = Column(Integer)
    timeline_source = Column(String, default="אוטומטי")

    # override
    manual_complexity_multiplier = Column(Float, default=1.0)
    manual_override_reason = Column(Text)
    # override מחיר ידני
    manual_total_price = Column(Float)
    use_manual_pricing = Column(Boolean, default=False, nullable=False)

    # תנאים
    index_type = Column(String, default="תשומות בניה")
    includes_vat = Column(Boolean, default=False)
    notes_pricing = Column(Text)

    # תוצאות חישוב (JSON — לא שכבת אמת)
    calculation_result = Column(JSON)

    # override לפרויקט חריג (לו"ז + תמחור ידני)
    exception_pricing_override = Column(JSON)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ApprovalLog(Base):
    """תיעוד אישורים — audit trail."""
    __tablename__ = "approval_log"

    id = Column(String, primary_key=True, default=gen_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    action = Column(String, nullable=False)  # approved_proposal / saved_to_db / rejected
    final_fee = Column(Float)
    final_fee_per_unit = Column(Float)
    flags_at_approval = Column(JSON)
    approved_at = Column(DateTime, server_default=func.now())
    notes = Column(Text)

    # זיהוי מאשר (placeholder עד שתוטמע מערכת משתמשים)
    user_id = Column(String, nullable=False, default="משתמש_ידני")

    # audit trail: פרטי override
    override_active = Column(Boolean, nullable=False, default=False)
    override_reason = Column(Text, nullable=True)
