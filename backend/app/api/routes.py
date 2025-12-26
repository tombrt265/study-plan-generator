from fastapi import APIRouter, UploadFile, File
from app.api.pdf_utils import extract_text_from_pdf
from app.api.models import KnowledgeGraphRequest
from app.api.agents import generate_knowledge_graph

router = APIRouter()

@router.post("/extract-study-material")
async def extract_study_material(file: UploadFile = File(...)):
    content = await file.read()
    return {"text": extract_text_from_pdf(content)}

@router.post("/create-knowledge-graph")
async def create_knowledge_graph(request: KnowledgeGraphRequest):
    graph = await generate_knowledge_graph(request)
    return {"text": graph.knowledge_graph}