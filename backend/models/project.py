from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ProjectType(str, Enum):
    מגורים = "מגורים"
    עירוב_שימושים = "עירוב שימושים"
    מגדל = "מגדל"
    פינוי_בינוי = "פינוי בינוי"
    הריסה_ובנייה = "הריסה ובנייה"
    מסחרי = "מסחרי"
    ציבורי = "ציבורי"


class BusinessStatus(str, Enum):
    """סטטוס עסקי — מצב הפרויקט מול הלקוח."""
    בטיפול   = "בטיפול"
    הוגש     = "הוגש"
    זכינו    = "זכינו"
    לא_זכינו = "לא_זכינו"
    הסתיים   = "הסתיים"


class PricingMode(str, Enum):
    חודשי = "חודשי"
    פאושלי = "פאושלי"
    ליחד = "ליח\"ד"


class IndexType(str, Enum):
    תשומות_בניה = "תשומות בניה"
    צרכן = "צרכן"
    ללא = "ללא"


class PricingRegion(str, Enum):
    תל_אביב_ירושלים = "תל אביב / ירושלים"
    גוש_דן = "גוש דן"
    שפלה_צפון = "שפלה / צפון"


class ProjectCreate(BaseModel):
    """שדות ליצירת פרויקט חדש."""
    project_name: str = Field(..., description="שם פרויקט")
    client_name: str = Field(..., description="שם לקוח / חברה")
    location_city: str = Field(..., description="עיר")
    project_type: ProjectType = Field(..., description="סוג פרויקט")
    num_units: int = Field(..., gt=0, description="מספר יח\"ד")
    num_floors_above: int = Field(..., gt=0, description="קומות עיליות")
    execution_phases: int = Field(default=1, ge=1, le=3, description="שלבי ביצוע")
    is_exception_pricing: bool = False
    exception_pricing_override: Optional[dict] = None

    # תיקון קריטי: ברירת מחדל False — כל פרויקט חדש הוא אמיתי
    is_test: bool = False

    # שדות אופציונליים
    pricing_mode: PricingMode = PricingMode.חודשי
    num_buildings: Optional[int] = None
    num_floors_underground: Optional[float] = None
    plot_area_sqm: Optional[float] = None
    area_residential_sqm: Optional[float] = None
    area_commercial_sqm: Optional[float] = None
    area_employment_sqm: Optional[float] = None

    # לוח זמנים ידני (אופציונלי)
    timeline_planning: Optional[int] = None
    timeline_excavation: Optional[int] = None
    timeline_underground: Optional[int] = None
    timeline_above_ground: Optional[int] = None
    timeline_finishes: Optional[int] = None
    timeline_handover: Optional[int] = None

    # override ותנאים
    manual_complexity_multiplier: float = Field(default=1.0, ge=0.5, le=2.0)
    manual_override_reason: Optional[str] = None
    index_type: IndexType = IndexType.תשומות_בניה
    includes_vat: bool = False
    notes_pricing: Optional[str] = None

    # סטטוס עסקי וארכיון (פאזה 1)
    business_status: BusinessStatus = BusinessStatus.בטיפול
    is_archived: bool = False


class ProjectUpdate(BaseModel):
    """עדכון חלקי — כל השדות אופציונליים."""
    project_name: Optional[str] = None
    client_name: Optional[str] = None
    location_city: Optional[str] = None
    project_type: Optional[ProjectType] = None
    num_units: Optional[int] = None
    num_floors_above: Optional[int] = None
    execution_phases: Optional[int] = None
    is_test: Optional[bool] = None
    pricing_mode: Optional[PricingMode] = None
    num_buildings: Optional[int] = None
    num_floors_underground: Optional[float] = None
    plot_area_sqm: Optional[float] = None
    area_residential_sqm: Optional[float] = None
    area_commercial_sqm: Optional[float] = None
    area_employment_sqm: Optional[float] = None
    timeline_planning: Optional[int] = None
    timeline_excavation: Optional[int] = None
    timeline_underground: Optional[int] = None
    timeline_above_ground: Optional[int] = None
    timeline_finishes: Optional[int] = None
    timeline_handover: Optional[int] = None
    manual_complexity_multiplier: Optional[float] = None
    manual_override_reason: Optional[str] = None
    index_type: Optional[IndexType] = None
    includes_vat: Optional[bool] = None
    notes_pricing: Optional[str] = None
    business_status: Optional[BusinessStatus] = None
    is_archived: Optional[bool] = None
    manual_total_price: Optional[float] = None
    use_manual_pricing: Optional[bool] = None
    is_exception_pricing: Optional[bool] = None
    exception_pricing_override: Optional[dict] = None


class ProjectResponse(BaseModel):
    """תשובת API לפרויקט."""
    id: str
    status: str
    is_test: bool
    project_name: str
    client_name: str
    location_city: str
    project_type: str
    num_units: int
    num_floors_above: int
    execution_phases: int
    pricing_mode: Optional[str]
    num_buildings: Optional[int]
    num_floors_underground: Optional[float]
    plot_area_sqm: Optional[float]
    timeline_planning: Optional[int]
    timeline_excavation: Optional[int]
    timeline_underground: Optional[int]
    timeline_above_ground: Optional[int]
    timeline_finishes: Optional[int]
    timeline_handover: Optional[int]
    manual_complexity_multiplier: float
    manual_override_reason: Optional[str]
    manual_total_price: Optional[float]
    use_manual_pricing: bool
    index_type: Optional[str]
    includes_vat: bool
    notes_pricing: Optional[str]
    business_status: str
    is_archived: bool
    calculation_result: Optional[dict]
    created_at: Optional[str]
    updated_at: Optional[str]
    is_exception_pricing: bool
    exception_pricing_override: Optional[dict] = None

    class Config:
        from_attributes = True
