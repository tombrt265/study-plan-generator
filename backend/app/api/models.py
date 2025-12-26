from pydantic import BaseModel

class KnowledgeGraphRequest(BaseModel):
    study_material: str

class KnowledgeGraphResponse(BaseModel):
    knowledge_graph: str