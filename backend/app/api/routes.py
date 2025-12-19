from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class Answers(BaseModel):
    answers: list[str]

@router.post("/submit-form")
async def submit_form(answers: Answers):
    return {"answers": answers.answers}