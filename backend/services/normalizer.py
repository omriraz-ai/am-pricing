"""
שכבת Normalization — מיפוי מילים נרדפות לשדות.
מבוסס על גיליון 'יעדי נרמול' באקסל.
"""
from typing import Optional, Dict, Any

# מילון נרדפות — מבוסס על גיליון 'יעדי נרמול' באקסל
NORMALIZATION_DICT: Dict[str, list] = {
    "project_name": [
        "שם פרויקט", "פרויקט", "שם הפרויקט", "project name", "project",
    ],
    "client_name": [
        "שם לקוח", "לקוח", "חברה", "יזם", "מזמין", "client", "developer",
        "customer", "לכבוד", "לידי",
    ],
    "location_city": [
        "עיר", "מיקום", "city", "location", "עיר הפרויקט",
    ],
    "project_type": [
        "סוג פרויקט", "סוג", "project type", "type",
        "מגדל", "מגורים", "פינוי בינוי", "עירוב שימושים",
        "mixed use", "tower", "residential",
    ],
    "num_units": [
        "מספר יח\"ד", "יח\"ד", "יחידות דיור", "דירות", "מספר דירות",
        "units", "apartments", "dwellings", "דירות מגורים",
        "מס' יח\"ד", "מס' דירות", "מספר יחידות",
    ],
    "num_buildings": [
        "מספר מבנים", "מבנים", "buildings", "blocks", "מספר בניינים",
    ],
    "num_floors_above": [
        "קומות עיליות", "קומות", "מספר קומות", "קומות מעל הקרקע",
        "above ground floors", "storeys", "floors", "קומות בניין",
        "גובה בניין בקומות", "קומות עיל",
    ],
    "num_floors_underground": [
        "קומות מרתף", "מרתף", "מרתפים", "קומות מרתף", "תת קרקע",
        "תת-קרקע", "basement", "underground", "B1", "B2", "B3",
        "קומות שליליות",
    ],
    "execution_phases": [
        "שלבי ביצוע", "שלביות", "phases", "ביצוע בשני שלבים",
        "שלבים", "מספר שלבים",
    ],
    "plot_area_sqm": [
        "שטח מגרש", "שטח הקרקע", "שטח המגרש", "plot area", "site area",
        "lot size", "שטח בדונם", "מגרש בשטח", "שטח הנכס",
    ],
    "area_residential_sqm": [
        "שטח מגורים", "שטח עיקרי מגורים", "שטח דיור",
        "residential area", "living space", "עיקרי למגורים",
    ],
    "area_commercial_sqm": [
        "שטח מסחר", "שטח מסחרי", "מסחר", "חנויות", "קומת מסחר",
        "commercial", "retail", "שטח עיקרי מסחר",
    ],
    "area_employment_sqm": [
        "שטח תעסוקה", "תעסוקה", "משרדים", "employment", "office",
    ],
    "timeline_planning": [
        "תכנון ורישוי", "תכנון", "רישוי", "היתרים", "planning", "licensing",
        "שלב תכנון", "תכנון ורישוי (חודשים)",
    ],
    "timeline_excavation": [
        "חפירה ודיפון", "חפירה", "דיפון", "excavation", "shoring",
        "חפ\"ד", "חפירה ודיפון (חודשים)",
    ],
    "timeline_underground": [
        "שלד תת\"ק", "שלד תת קרקע", "מרתפים", "underground structure",
        "שלד תתק",
    ],
    "timeline_above_ground": [
        "שלד עילי", "שלד עליון", "above ground structure",
        "שלד", "שלד (חודשים)",
    ],
    "timeline_finishes": [
        "גמרים", "מעטפת", "מערכות", "גמרים ומערכות",
        "finishes", "envelope", "systems",
        "גמרים / מעטפת / מערכות",
    ],
    "timeline_handover": [
        "טופס 4", "מסירות", "handover", "form4",
        "מסירות / טופס 4", "טופס 4 ומסירות",
    ],
    "total_fee": [
        "שכ\"ט", "הצעת מחיר", "fee", "total proposal",
        "שכ\"ט משוער", "סה\"כ שכ\"ט", "מחיר כולל",
    ],
    "fee_per_unit": [
        "מחיר ליח\"ד", "₪ / יח\"ד", "fee per unit",
        "מחיר ליחידה", "שכ\"ט ליח\"ד",
    ],
    "index_type": [
        "מדד הצמדה", "סוג מדד", "מדד", "index", "תשומות בניה",
        "מדד צרכן", "index type",
    ],
    "includes_vat": [
        "כולל מע\"מ", "VAT", "מע\"מ", "includes vat",
    ],
}

# מיפוי ערכי enum — ניסוח → ערך סטנדרטי
PROJECT_TYPE_ALIASES: Dict[str, str] = {
    "מגדל": "מגדל",
    "tower": "מגדל",
    "high rise": "מגדל",
    "מגורים": "מגורים",
    "residential": "מגורים",
    "apartments": "מגורים",
    "פינוי בינוי": "פינוי בינוי",
    "urban renewal": "פינוי בינוי",
    "pinuy binuy": "פינוי בינוי",
    "עירוב שימושים": "עירוב שימושים",
    "mixed use": "עירוב שימושים",
    "mixed-use": "עירוב שימושים",
    "הריסה ובנייה": "הריסה ובנייה",
    "demolish": "הריסה ובנייה",
    "demolish and rebuild": "הריסה ובנייה",
    "מסחרי": "מסחרי",
    "commercial": "מסחרי",
    "ציבורי": "ציבורי",
    "public": "ציבורי",
}

INDEX_TYPE_ALIASES: Dict[str, str] = {
    "תשומות בניה": "תשומות בניה",
    "construction index": "תשומות בניה",
    "צרכן": "צרכן",
    "consumer": "צרכן",
    "cpi": "צרכן",
    "ללא": "ללא",
    "none": "ללא",
    "no index": "ללא",
}


def normalize_field_name(raw_key: str) -> Optional[str]:
    """
    מחזיר את שם השדה הסטנדרטי לפי מפתח גולמי.
    לדוגמה: "יח\"ד" → "num_units"
    """
    raw_lower = raw_key.strip().lower()
    for field, synonyms in NORMALIZATION_DICT.items():
        for syn in synonyms:
            if syn.lower() == raw_lower:
                return field
    return None


def normalize_project_type(raw: str) -> Optional[str]:
    """נרמול ערך סוג פרויקט."""
    return PROJECT_TYPE_ALIASES.get(raw.strip(), None)


def normalize_index_type(raw: str) -> Optional[str]:
    """נרמול סוג מדד."""
    return INDEX_TYPE_ALIASES.get(raw.strip(), None)


def normalize_extracted_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    קבלת dict גולמי (כפי שחולץ מקובץ / Claude API)
    והמרתו לשדות סטנדרטיים.

    מחזיר dict עם:
    - field: שם שדה סטנדרטי
    - value: ערך
    - confidence: "exact" | "alias" | "unknown"
    - original_key: המפתח המקורי
    """
    result = {}

    for raw_key, value in raw_data.items():
        normalized = normalize_field_name(raw_key)

        if normalized:
            confidence = "exact" if raw_key in NORMALIZATION_DICT.get(normalized, []) else "alias"
            # נרמול ערכים לפי סוג שדה
            if normalized == "project_type" and isinstance(value, str):
                norm_val = normalize_project_type(value)
                result[normalized] = {
                    "value": norm_val or value,
                    "confidence": confidence if norm_val else "low",
                    "original_key": raw_key,
                }
            elif normalized == "index_type" and isinstance(value, str):
                norm_val = normalize_index_type(value)
                result[normalized] = {
                    "value": norm_val or value,
                    "confidence": confidence if norm_val else "low",
                    "original_key": raw_key,
                }
            else:
                result[normalized] = {
                    "value": value,
                    "confidence": confidence,
                    "original_key": raw_key,
                }
        else:
            # שדה לא זוהה
            result[f"unknown_{raw_key}"] = {
                "value": value,
                "confidence": "unknown",
                "original_key": raw_key,
            }

    return result


def get_missing_required_fields(data: Dict[str, Any]) -> list:
    """בדיקת שדות חובה חסרים."""
    required = [
        "project_name", "client_name", "location_city",
        "project_type", "num_units", "num_floors_above", "execution_phases",
    ]
    normalized_keys = set()
    for key in data:
        if not key.startswith("unknown_"):
            normalized_keys.add(key)

    return [f for f in required if f not in normalized_keys]
