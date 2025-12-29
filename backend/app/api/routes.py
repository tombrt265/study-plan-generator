from fastapi import APIRouter, UploadFile, File
from app.api.pdf_utils import extract_text_from_pdf
from app.api.models import StudyMaterial, StudyPlan
from app.api.agents import generate_study_plan
router = APIRouter()

@router.post("/extract-study-material")
async def extract_study_material(file: UploadFile = File(...)):
    content = await file.read()
    return {"text": extract_text_from_pdf(content)}

@router.post("/create-study-plan", response_model=StudyPlan)
async def create_study_plan(material: StudyMaterial) -> StudyPlan:
    language = "German"  # Example: specify the target language for translation
    plan = await generate_study_plan(material, language=language)
    return plan