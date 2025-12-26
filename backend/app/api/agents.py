from pydantic_ai import Agent
from app.api.models import KnowledgeGraphRequest, KnowledgeGraphResponse
from dotenv import load_dotenv

load_dotenv()

knowledge_graph_agent = Agent(
  model="gpt-4o",
  deps_type=KnowledgeGraphRequest,
  output_type=KnowledgeGraphResponse,
  output_retries=3,
  system_prompt="""
You will receive study material in the user message.

Rules:
- Analyze ONLY the provided study material
- Do NOT use external knowledge
- Extract concept dependencies from the text
- Output concise dependency-focused text in the language of the input
"""
)

async def generate_knowledge_graph(request: KnowledgeGraphRequest) -> KnowledgeGraphResponse:
  result = await knowledge_graph_agent.run(
    deps=request,
    user_prompt=f"""
      Study material:
      {request.study_material}
      """
    )
  return result.output