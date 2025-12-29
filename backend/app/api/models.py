from enum import Enum
from pydantic import BaseModel, Field

class StudyMaterial(BaseModel):
    study_material: str

class Topic(BaseModel):
    name: str
    description: str

class TopicRelationshipType(Enum):
    PRECEDES = "precedes"
    FOLLOWS = "follows"
    RELATED_TO = "related_to"

class TopicRelationship(BaseModel):
    from_topic: str
    relationship: TopicRelationshipType
    to_topic: str

class KnowledgeGraph(BaseModel):
    nodes: list[Topic] = Field(description="A list of topics extracted from the study material")
    edges: list[TopicRelationship] = Field(description="A list of edges representing relationships between topics")

class StudyMethod(str, Enum):
    READING = "reading"
    PRACTICE = "practice"
    FLASHCARDS = "flashcards"
    REVIEW = "review"

class StudySession(BaseModel):
    topic: Topic = Field(description="Topic covered in this session")
    information: str = Field(description="Detailed information about the topic")
    duration_minutes: int = Field(description="Planned duration in minutes")
    methods: list[StudyMethod] = Field(description="Recommended study methods")

class StudyPlan(BaseModel):
    overview: str = Field(description="High-level summary of the study plan")
    sessions: list[StudySession] = Field(description="Detailed study sessions")
    total_duration_hours: int = Field(description="Total planned study duration in hours")

class StudyPlanEvaluationAssesments(str, Enum):
    ACHIEVABLE = "achievable"
    NEEDS_IMPROVEMENT = "needs_improvement"
    UNACHIEVABLE = "unachievable"

class StudyPlanEvaluation(BaseModel):
    assessment: StudyPlanEvaluationAssesments = Field(description="Overall assessment of the study plan")
    justification: str = Field(description="Justification for the assessment")