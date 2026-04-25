import re
from io import BytesIO

import pandas as pd
from fastapi import APIRouter, UploadFile, File

from sqlalchemy.orm import Session
from fastapi import Depends
from db_models import Project
from database import get_db
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import os
import json
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


router = APIRouter(
    prefix="/import",
    tags=["Import Preview"],
)


def get_first_value(row, possible_columns):
    # התאמה מדויקת
    for column in possible_columns:
        if column in row and pd.notna(row[column]):
            return row[column]

    # התאמה חלקית
    for key in row.keys():
        for column in possible_columns:
            if column.lower().replace(" ", "") in str(key).lower().replace(" ", ""):
                value = row[key]
                if pd.notna(value):
                    return value

    return None


def get_first_source(row, possible_columns):
    # התאמה מדויקת
    for column in possible_columns:
        if column in row and pd.notna(row[column]):
            return column

    # התאמה חלקית
    for key in row.keys():
        for column in possible_columns:
            if column.lower().replace(" ", "") in str(key).lower().replace(" ", ""):
                value = row[key]
                if pd.notna(value):
                    return key

    return None


def get_confidence(row, possible_columns):
    # התאמה מדויקת
    for column in possible_columns:
        if column in row and pd.notna(row[column]):
            return 1.0

    # התאמה חלקית
    for key in row.keys():
        for column in possible_columns:
            if column.lower().replace(" ", "") in str(key).lower().replace(" ", ""):
                value = row[key]
                if pd.notna(value):
                    return 0.7

    return 0


def build_warnings(detected_fields):
    warnings = []

    if detected_fields.get("units") is None:
        warnings.append("לא זוהה מספר יחידות")

    if detected_fields.get("floors") is None:
        warnings.append("לא זוהה מספר קומות")

    if detected_fields.get("area") is None:
        warnings.append("לא זוהה שטח")

    return warnings


def normalize_number(value):
    try:
        if value is None:
            return None

        text = str(value).replace(",", "").replace(" ", "")

        match = re.search(r"\d+(\.\d+)?", text)

        if not match:
            return None

        return float(match.group())

    except Exception:
        return None


@router.post("/excel-preview")
async def excel_preview(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        api_key = os.getenv("OPENAI_API_KEY")
        print("OPENAI KEY EXISTS:", bool(api_key))

        df = pd.read_excel(BytesIO(contents))

        preview = {
            "columns": list(df.columns),
            "rows_count": len(df),
            "sample_rows": df.head(5).to_dict(orient="records"),
        }

        first_row = df.iloc[0].to_dict() if len(df) > 0 else {}

        detected_fields = {
            "project_name": get_first_value(first_row, [
                "Project Name", "project_name", "שם פרויקט", "שם הפרויקט", "פרויקט"
            ]),
            "client_name": get_first_value(first_row, [
                "Client Name", "Client", "client_name", "שם לקוח", "שם הלקוח", "לקוח", "יזם"
            ]),
            "city": get_first_value(first_row, [
                "City", "city", "עיר", "מיקום", "יישוב", "ישוב"
            ]),
            "units": normalize_number(get_first_value(first_row, [
                "Units", "Unit", "Unit Count", "units", "מספר יחידות", "יחידות",
                "יח\"ד", "יח״ד", "דירות", "מספר דירות"
            ])),
            "floors": normalize_number(get_first_value(first_row, [
                "Floors", "floors", "קומות", "מספר קומות", "קומות מעל הקרקע",
                "מס׳ קומות", "מספר קומות מעל הקרקע"
            ])),
            "area": normalize_number(get_first_value(first_row, [
                "Area", "area", "TOTAL AREA", "שטח", "מ״ר", "מ\"ר",
                "שטח בנוי", "שטח עילי", "סה\"כ שטח", "סה״כ שטח"
            ])),
        }

        detected_sources = {
            "project_name": get_first_source(first_row, [
                "Project Name", "project_name", "שם פרויקט", "שם הפרויקט", "פרויקט"
            ]),
            "client_name": get_first_source(first_row, [
                "Client Name", "Client", "client_name", "שם לקוח", "שם הלקוח", "לקוח", "יזם"
            ]),
            "city": get_first_source(first_row, [
                "City", "city", "עיר", "מיקום", "יישוב", "ישוב"
            ]),
            "units": get_first_source(first_row, [
                "Units", "Unit", "Unit Count", "units", "מספר יחידות", "יחידות",
                "יח\"ד", "יח״ד", "דירות", "מספר דירות"
            ]),
            "floors": get_first_source(first_row, [
                "Floors", "floors", "קומות", "מספר קומות", "קומות מעל הקרקע",
                "מס׳ קומות", "מספר קומות מעל הקרקע"
            ]),
            "area": get_first_source(first_row, [
                "Area", "area", "TOTAL AREA", "שטח", "מ״ר", "מ\"ר",
                "שטח בנוי", "שטח עילי", "סה\"כ שטח", "סה״כ שטח"
            ]),
        }

        confidence = {
            "project_name": get_confidence(first_row, [
                "Project Name", "project_name", "שם פרויקט", "שם הפרויקט", "פרויקט"
            ]),
            "client_name": get_confidence(first_row, [
                "Client Name", "Client", "client_name", "שם לקוח", "שם הלקוח", "לקוח", "יזם"
            ]),
            "city": get_confidence(first_row, [
                "City", "city", "עיר", "מיקום", "יישוב", "ישוב"
            ]),
            "units": get_confidence(first_row, [
                "Units", "Unit", "Unit Count", "units", "מספר יחידות", "יחידות",
                "יח\"ד", "יח״ד", "דירות", "מספר דירות"
            ]),
            "floors": get_confidence(first_row, [
                "Floors", "floors", "קומות", "מספר קומות", "קומות מעל הקרקע",
                "מס׳ קומות", "מספר קומות מעל הקרקע"
            ]),
            "area": get_confidence(first_row, [
                "Area", "area", "TOTAL AREA", "שטח", "מ״ר", "מ\"ר",
                "שטח בנוי", "שטח עילי", "סה\"כ שטח", "סה״כ שטח"
            ]),
        }

        warnings = build_warnings(detected_fields)

        return {
            "status": "preview_only",
            "file_name": file.filename,
            "preview": preview,
            "detected_fields": detected_fields,
            "detected_sources": detected_sources,
            "confidence": confidence,
            "warnings": warnings,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }

@router.post("/create-project")
def create_project_from_import(data: dict, db: Session = Depends(get_db)):
    try:
        fields = data.get("detected_fields", {})
        overrides = data.get("overrides", {})



        project = Project(
            project_name=final_fields.get("project_name"),
            client_name=final_fields.get("client_name"),
            location_city=final_fields.get("city"),
            num_units=final_fields.get("units"),
            num_floors_above=final_fields.get("floors"),
            plot_area_sqm=final_fields.get("area"),
            status="draft",
            is_test=False,
        )

        db.add(project)
        db.commit()
        db.refresh(project)

        return {
            "status": "created",
            "project_id": project.id,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }
@router.post("/confirm-create")
def confirm_create_project_from_import(data: dict, db: Session = Depends(get_db)):
    try:
        fields = data.get("detected_fields", {})
        warnings = data.get("warnings", [])
        confidence = data.get("confidence", {})
        overrides = data.get("overrides", {})

        final_fields = {
            **fields,
            **{key: value for key, value in overrides.items() if value is not None}
        }

        project = Project(
            project_name=final_fields.get("project_name"),
            client_name=final_fields.get("client_name"),
            location_city=final_fields.get("city"),
            project_type="residential",
            num_units=final_fields.get("units"),
            num_floors_above=final_fields.get("floors"),
            plot_area_sqm=final_fields.get("area"),
            status="draft",
            is_test=False,
        )

        db.add(project)
        db.commit()
        db.refresh(project)

        return {
            "status": "created",
            "project_id": project.id,
            "created_from": "import_confirm",
            "detected_fields": fields,
            "overrides": overrides,
            "final_fields": final_fields,
            "warnings": warnings,
            "confidence": confidence,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }

def extract_project_fields_with_gemini(text: str):
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""
Extract project data from the following text.

Return ONLY valid JSON, without markdown, without explanation.

Use these exact keys:
project_name, client_name, city, units, floors, area

Rules:
- If a value is missing, use null
- units, floors, area must be numbers or null
- Text may be Hebrew or English
- project_name can be the project name after the word פרויקט
- client_name can be the name after לכבוד
- city can be a city name mentioned near the project name

TEXT:
{text[:6000]}
"""

    response = model.generate_content(prompt)
    raw = response.text.strip()

    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(raw)
    except Exception:
        return {
            "project_name": None,
            "client_name": None,
            "city": None,
            "units": None,
            "floors": None,
            "area": None,
            "raw_ai_response": raw,
        }
def extract_units_from_text(text: str):
    patterns = [
        r"(\d+)\s*(יח\"ד|יח״ד)",
        r"(\d+)\s*יחידות\s*דיור",
        r"(\d+)\s*דירות",
        r"כ[-\s]*(\d+)\s*(יח\"ד|יח״ד|יחידות\s*דיור|דירות)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))

    return None

@router.post("/pdf-preview")
async def pdf_preview(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        reader = PdfReader(BytesIO(contents))

        text = ""
        for page in reader.pages[:5]:
            text += page.extract_text() or ""

        try:
            detected_fields = extract_project_fields_with_gemini(text)
        except Exception:
            detected_fields = {
                "project_name": None,
                "client_name": None,
                "city": None,
                "units": None,
                "floors": None,
                "area": None,
            }

        if detected_fields.get("units") is None:
            detected_fields["units"] = extract_units_from_text(text)

        if detected_fields.get("project_name") is None:
            match = re.search(r"פרויקט\s+([A-Za-z0-9\u0590-\u05FF]+)", text)
            if match:
                detected_fields["project_name"] = match.group(1)

        if detected_fields.get("client_name") is None:
            match = re.search(r"לכבוד\s+([^\n\r]+)", text)
            if match:
                detected_fields["client_name"] = match.group(1).strip()

        if detected_fields.get("city") is None:
            match = re.search(r"(ירושלים|תל אביב|חיפה|פתח תקווה|נתניה|חדרה|הרצליה|רמת גן)", text)
            if match:
                detected_fields["city"] = match.group(1)

        if detected_fields.get("floors") is None:
            match = re.search(r"(\d+)\s*קומות", text)
            if match:
                detected_fields["floors"] = int(match.group(1))

        return {
            "status": "pdf_text_extracted",
            "file_name": file.filename,
            "text_preview": text[:1000],
            "text_length": len(text),
            "detected_fields": detected_fields,
            "warnings": [],
            "confidence": {},
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }