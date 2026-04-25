"""מיפוי עיר → אזור תמחור."""

TLV_JLM_CITIES = {
    "תל אביב", "תל אביב-יפו", "ירושלים", "יפו",
    "רמת גן", "גבעתיים", "בני ברק",
}

GUSH_DAN_CITIES = {
    "פתח תקווה", "ראשון לציון", "חולון", "בת ים", "אור יהודה",
    "יהוד", "אלעד", "קרית אונו", "גבעת שמואל", "רמת השרון",
    "הרצליה", "כפר סבא", "רעננה", "הוד השרון", "נס ציונה",
    "ראש העין", "לוד", "רמלה", "מודיעין",
}


def city_to_region(city: str) -> str:
    """המרת שם עיר לאזור תמחור."""
    city_clean = city.strip()

    if city_clean in TLV_JLM_CITIES:
        return "תל אביב / ירושלים"

    if city_clean in GUSH_DAN_CITIES:
        return "גוש דן"

    # ברירת מחדל — שפלה / צפון
    return "שפלה / צפון"


def region_to_multiplier_key(region: str) -> str:
    """המרת אזור למפתח config."""
    mapping = {
        "תל אביב / ירושלים": "multiplier_region_tlv_jlm",
        "גוש דן": "multiplier_region_gush_dan",
        "שפלה / צפון": "multiplier_region_other",
    }
    return mapping.get(region, "multiplier_region_other")
