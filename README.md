# AM הנדסה — מערכת הצעות מחיר

מערכת אוטומטית לחישוב תמחור ויצירת הצעות מחיר לפרויקטי בנייה.

---

## מבנה המערכת

```
am-pricing/
├── backend/          ← FastAPI + Python
└── frontend/         ← Next.js + TypeScript
```

---

## הפעלה מהירה

### דרישות מוקדמות
- Python 3.10+
- Node.js 18+

### Backend

```bash
cd backend

# התקנת תלויות
pip install fastapi uvicorn sqlalchemy pydantic python-docx python-dotenv

# הפעלה (יוצר DB ומעמיס נתונים אוטומטית)
uvicorn main:app --reload --port 8000
```

המערכת תעמיס אוטומטית:
- 8 פרויקטים היסטוריים לבסיס הנתונים
- 44 מקדמי תמחור מהאקסל

**תיעוד API:** http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

הממשק זמין ב: http://localhost:3000

---

## זרימת עבודה

```
1. צור פרויקט חדש  →  /projects/new
2. מלא שדות חובה   →  שם, לקוח, עיר, סוג, יח"ד, קומות
3. לחץ "חשב תמחור" →  POST /api/v1/pricing/calculate
4. בדוק תוצאות     →  Tier, לוז, תמחור לפי שלב, פרויקטים דומים, דגלים
5. לחץ "✓ אשר ויצר הצעה"  →  POST /api/v1/approval/confirm
6. הורד DOCX        →  POST /api/v1/proposal/generate
7. שמור לבסיס נתונים (אופציונלי) → POST /api/v1/approval/save-to-db
```

---

## מבנה API

### פרויקטים
| Method | URL | תיאור |
|--------|-----|--------|
| POST | /api/v1/projects | יצירת פרויקט |
| GET  | /api/v1/projects | רשימת פרויקטים |
| GET  | /api/v1/projects/{id} | פרויקט בודד |
| PATCH | /api/v1/projects/{id} | עדכון |
| DELETE | /api/v1/projects/{id} | מחיקת טיוטה |

### תמחור
| Method | URL | תיאור |
|--------|-----|--------|
| POST | /api/v1/pricing/calculate | חישוב מלא |
| POST | /api/v1/pricing/comparables | פרויקטים דומים בלבד |

### אישור ושמירה
| Method | URL | תיאור |
|--------|-----|--------|
| POST | /api/v1/approval/confirm | אישור הצעה |
| POST | /api/v1/approval/save-to-db | שמירה לבסיס האמת |
| GET  | /api/v1/approval/log | היסטוריית אישורים |

### הצעת מחיר
| Method | URL | תיאור |
|--------|-----|--------|
| POST | /api/v1/proposal/generate | הורדת DOCX |
| GET  | /api/v1/proposal/{id}/preview | תצוגה HTML |

### בסיס נתונים (קריאה בלבד)
| Method | URL | תיאור |
|--------|-----|--------|
| GET | /api/v1/reference/projects | כל הפרויקטים |

---

## לוגיקת תמחור (מבוסס אקסל)

### Tier לפי יח"ד
| Tier | טווח |
|------|------|
| S | 0–40 |
| M | 41–120 |
| L | 121–400 |
| XL | 401+ |

### מכפילים
| גורם | ערך |
|------|-----|
| מגדל | ×1.35 |
| פינוי בינוי | ×1.20 |
| הריסה ובנייה | ×1.15 |
| עירוב שימושים | ×1.10 |
| מגורים | ×1.00 |
| תל אביב / ירושלים | ×1.10 |
| גוש דן | ×1.00 |
| שפלה / צפון | ×0.95 |
| 2 שלבים | ×1.15 |

### כיול מחיר סופי
```
30% מנוע חוקים + 70% ממוצע פרויקטים דומים
```

---

## הרצת בדיקות

```bash
cd backend
python3 test_golden.py
```

הבדיקות מאמתות שכל חישובי הליבה תואמים את ערכי האקסל (FOREST ירושלים).

---

## הגדרת סביבה (אופציונלי)

```bash
# backend/.env
DATABASE_URL=postgresql://user:pass@localhost:5432/am_pricing  # ברירת מחדל: SQLite

# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## הוספת פרויקט לבסיס הנתונים

הכתיבה לבסיס האמת מוגנת בשני שלבים:
1. אישור ההצעה (`/approval/confirm`)
2. אישור נפרד לשמירה (`/approval/save-to-db`)

לא ניתן לכתוב לבסיס ישירות ללא שני האישורים.

---

## מבנה קבצים מלא

```
backend/
├── main.py                    ← FastAPI app
├── database.py                ← SQLAlchemy
├── db_models.py               ← טבלאות DB
├── seed_data.py               ← 8 פרויקטים + 44 מקדמים
├── test_golden.py             ← בדיקות מול האקסל
├── models/
│   ├── project.py
│   ├── pricing.py
│   └── reference.py
├── services/
│   ├── rules_engine.py        ← 30% מנוע חוקים
│   ├── comparables.py         ← אלגוריתם דמיון
│   ├── schedule_engine.py     ← לוח זמנים 60/40
│   ├── pricing_engine.py      ← כיול 30/70 + דגלים
│   ├── proposal_generator.py  ← DOCX RTL
│   └── normalizer.py          ← מיפוי מילים נרדפות
├── api/routes/
│   ├── projects.py
│   ├── pricing.py
│   ├── approval.py
│   ├── proposal.py
│   └── reference.py
└── utils/
    ├── helpers.py
    ├── region_mapper.py
    └── template_blocks.py

frontend/src/
├── services/api.ts
├── styles/globals.css
└── app/
    ├── layout.tsx
    ├── page.tsx                ← לוח בקרה
    └── projects/
        ├── new/page.tsx        ← טופס חדש
        └── [id]/page.tsx       ← פרטים + חישוב + אישור
```
