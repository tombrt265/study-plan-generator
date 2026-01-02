from pydantic_ai import Agent
from app.api.models import Evaluation, Quality, StudyMaterial, KnowledgeGraph, StudyPlan, StudyMethod, StudyPlanEvaluation, StudyPlanAchievability
from dotenv import load_dotenv
from datetime import datetime
from app.api.logger import logger

load_dotenv()

knowledge_graph_agent = Agent(
  model="gpt-4o",
  deps_type=StudyMaterial,
  output_type=KnowledgeGraph,
  output_retries=1,
  system_prompt="""
  You are an AI tasked with constructing a KnowledgeGraph.

  Rules:

  1. Nodes
  - Extract key topics from the study material.
  - Each topic must have:
    - a short, precise name
    - a concise description derived from the study material (max 50 words)

  2. Relationships (Edges)
  - Create relationships ONLY between extracted topics.
  - Allowed types:
    - PRECEDES: topic A is introduced before or is a prerequisite for topic B
    - FOLLOWS: topic A builds upon or comes after topic B
    - RELATED_TO: topics are conceptually related without clear ordering
  - Use consistent topic names exactly as in the nodes list.

  3. Output format
  - strictly return
    KnowledgeGraph {
      nodes: [Topic, ...],
      edges: [(Topic.name, TopicRelationship, Topic.name), ...]
    }

  Constraints:
  - If unsure about a topic, omit it.
  - Do not duplicate topics.
  - Do not include explanations or commentary.
  """
)

graph_critic_agent = Agent(
  model="gpt-4o-mini",
  deps_type=[StudyMaterial, KnowledgeGraph],
  output_type=Evaluation,
  output_retries=1,
  system_prompt=f"""
  You are a knowledge graph critic. 
  Your task:
  - Evaluate a KnowledgeGraph based on the provided study material.
  - Focus on three dimensions:
    1. Completeness: Are all key topics from the material included?
    2. Accuracy: Are the relationships between topics correct?
    3. Clarity: Is the graph easy to understand and navigate?

  Output:
  - Return a structured Evaluation with:
    - quality: one of {', '.join([q.value for q in Quality])}
    - justification: a concise explanation for your rating
  - Avoid commentary outside of the structured output.
  - Use only the provided study material for your evaluation.
  """
)

scheduling_agent = Agent(
  model="gpt-4o",
  deps_type=[StudyMaterial, KnowledgeGraph],
  output_type=StudyPlan,
  output_retries=1,
  system_prompt=f"""
  You are an AI that creates structured StudyPlans from a KnowledgeGraph and study material.

  Rules:

  1. Overview
  - Provide a concise summary of the study strategy.
  - Do not repeat the study material verbatim.

  2. Study Sessions
  - Each StudySession MUST include a date in YYYY-MM-DD format.
  - ALL dates MUST satisfy ALL of the following:
    - date >= provided earliest date
    - date <= provided latest date
    - NO date may be before the earliest date
    - NO date may be after the latest date
  - Dates outside this range are INVALID and must NOT be generated.
  - If unsure, choose a date within the valid range.
  - Each StudySession must cover exactly one Topic from the KnowledgeGraph.
  - Reference the Topic object consistently by its name.
  - Include a short explanation of what to learn about the topic.
  - Specify a duration in minutes (30-180).
  - Choose one or more StudyMethod values from {', '.join([m.value for m in StudyMethod])}.

  3. Ordering
  - Use the KnowledgeGraph relationships to determine session order:
    - PRECEDES → earlier session
    - FOLLOWS → later session
    - RELATED_TO → may be placed adjacently

  4. Coverage
  - Every Topic in the KnowledgeGraph must appear in exactly one StudySession.
  - Do not invent or omit topics.

  5. Total Duration
  - Set total_duration_hours to the sum of all session durations (rounded to whole hours).
  
  Output Constraints:
  - Return only a valid StudyPlan object conforming to the schema.
  - Do not use Markdown, headings, bullet points, or explanatory text outside the schema.
  """
)

schedule_critic_agent = Agent(
  model="gpt-4o-mini",
  deps_type=[StudyMaterial, StudyPlan],
  output_type=StudyPlanEvaluation,
  output_retries=1,
  system_prompt=f"""
  You are an AI that evaluates StudyPlans based on provided study material, a knowledge graph and a due date.

  Evaluation Criteria:
  1. Time Management
  - Are session durations realistic and achievable?

  2. Topic Coverage
  - Are all topics from the study material adequately covered?

  3. Study Methods
  - Are the recommended study methods effective for learning the material?

  4. Date Compliance
  - Do all StudySession dates fall within the allowed date range? 
  - if not, the plan is UNACHIEVABLE.

  Output:
  - Return a structured StudyPlanEvaluation with:
    - achievability: one of {', '.join([e.value for e in StudyPlanAchievability])}
    - justification: a concise explanation for your rating
  - Avoid commentary outside of the structured output.
  - Base your evaluation strictly on the provided study material.
  """
)

translation_agent = Agent(
  model="gpt-4o-mini",
  deps_type=StudyPlan,
  output_type=StudyPlan,
  output_retries=1,
  system_prompt=f"""
  You are an AI that translates StudyPlans into a specified language.

  Rules:
  - Maintain the exact structure and content of the original StudyPlan.
  - Translate only text fields (overview, session information, topic names if needed).
  - Do not modify durations, session ordering, or methods.
  - Return a valid StudyPlan object.
  - Avoid commentary, formatting changes, or additional text outside the schema.  
  """
)

async def generate_knowledge_graph(material: StudyMaterial) -> KnowledgeGraph:
  result = await knowledge_graph_agent.run(
    deps=material,
    user_prompt=f"""
    Use the following study material to construct the KnowledgeGraph. 
    This is the only source of information; do NOT use prior knowledge or assumptions.

    <<STUDY MATERIAL>>
    {material.study_material}
    <<END STUDY MATERIAL>>
    """,
  )
  return result.output

async def evaluate_knowledge_graph(material: StudyMaterial, graph: KnowledgeGraph) -> Evaluation:
  prompt = f"""
  Evaluate the following knowledge graph using only the provided study material.

  Knowledge Graph:
  Nodes:
  {', '.join([f'{node.name}: {node.description}' for node in graph.nodes])}

  Edges:
  {', '.join([f'({edge.from_topic} {edge.relationship.value} {edge.to_topic})' for edge in graph.edges])}

  <<STUDY MATERIAL>>
  {material.study_material}
  <<END STUDY MATERIAL>>
  """
  result = await graph_critic_agent.run(
    deps=[material, graph],
    user_prompt=prompt
  )
  return result.output

async def schedule_study_plan(material: StudyMaterial, graph: KnowledgeGraph, date: str) -> StudyPlan:
  current_date = datetime.now().date().isoformat()

  prompt = f"""
  Generate a StudyPlan based on the following inputs:

  IMPORTANT DATE CONSTRAINTS (MANDATORY):
  - Earliest Allowed Date: {current_date}
  - Latest Allowed Date: {date}
  - All StudySession dates MUST fall within this range.
  - Dates outside this range are invalid.

  <<STUDY MATERIAL>>
  {material.study_material}
  <<END STUDY MATERIAL>>

  Knowledge Graph:
  Nodes:
  {', '.join([f'{node.name}: {node.description}' for node in graph.nodes])}

  Edges:
  {', '.join([f'({edge.from_topic} {edge.relationship.value} {edge.to_topic})' for edge in graph.edges])}
  """

  result = await scheduling_agent.run(
    deps=[material, graph],
    user_prompt=prompt
  )
  return result.output

async def evaluate_study_plan(material: StudyMaterial, plan: StudyPlan, date: str) -> StudyPlanEvaluation:
  current_date = datetime.now().date().isoformat()
  
  prompt = f"""
  Evaluate the achievability of the following StudyPlan based only on the provided study material:

  <<STUDY MATERIAL>>
  {material.study_material}
  <<END STUDY MATERIAL>>
  
  <<STUDY PLAN>>
  Overview:
  {plan.overview}
  Study Sessions:
  {', '.join([f'Topic: {session.topic.name}, Information: {session.information}, Duration: {session.duration_minutes}, Methods: {", ".join([method.value for method in session.methods])}' for session in plan.sessions])}
  Total Duration Hours: {plan.total_duration_hours}
  <<END STUDY PLAN>>

  The earliest allowed date is {current_date}.
  The latest allowed date is {date}.
  All StudySession dates MUST fall within this range.
  """
  result = await schedule_critic_agent.run(
    deps=[material, plan],
    user_prompt=prompt
  )
  return result.output

async def translate_study_plan(plan: StudyPlan, language: str) -> StudyPlan:
  result = await translation_agent.run(
    deps=plan,
    user_prompt=f"""
    Translate the following StudyPlan into {language}:

    Study Plan:
    Overview:
    {plan.overview}

    Study Sessions:
    {', '.join([f'Topic: {session.topic.name}, Information: {session.information}, Duration: {session.duration_minutes}, Methods: {", ".join([method.value for method in session.methods])}' for session in plan.sessions])}

    Total Duration Hours: {plan.total_duration_hours}
    """
  )
  return result.output

async def generate_study_plan(material: StudyMaterial, language: str, date: str) -> StudyPlan:
    current_date = datetime.now().date().isoformat()
    logger.info("Starting study plan generation pipeline")
    logger.info("Target language: %s | Current Date: %s | Due Date: %s", language, current_date, date)

    # --- Knowledge Graph Phase ---
    knowledge_graph_quality = Quality.BAD
    attempts = 0

    while knowledge_graph_quality != Quality.GOOD and attempts < 2:
        attempts += 1
        logger.info("Knowledge graph generation attempt %d", attempts)

        graph = await generate_knowledge_graph(material)

        evaluation = await evaluate_knowledge_graph(material, graph)
        knowledge_graph_quality = evaluation.quality

        logger.info("Knowledge graph evaluation result: %s", knowledge_graph_quality)

    if knowledge_graph_quality != Quality.GOOD:
        logger.warning(
            "Proceeding with knowledge graph of quality %s after %d attempts",
            knowledge_graph_quality,
            attempts,
        )

    # --- Study Plan Scheduling Phase ---
    study_plan = StudyPlan(overview="", sessions=[], total_duration_hours=0)
    study_plan_achievability = StudyPlanAchievability.UNACHIEVABLE
    attempts = 0

    while (
        study_plan_achievability != StudyPlanAchievability.ACHIEVABLE
        and attempts < 2
    ):
        attempts += 1
        logger.info("Study plan scheduling attempt %d", attempts)

        study_plan = await schedule_study_plan(material, graph, date)

        plan_evaluation = await evaluate_study_plan(material, study_plan, date)
        study_plan_achievability = plan_evaluation.achievability

        logger.info("Study plan evaluation result: %s", plan_evaluation.achievability)

    if study_plan_achievability != StudyPlanAchievability.ACHIEVABLE:
        logger.warning(
            "Proceeding with study plan of achievability %s after %d attempts",
            study_plan_achievability,
            attempts,
        )

    # --- Translation Phase ---
    logger.info("Translating study plan into: %s", language)
    study_plan = await translate_study_plan(study_plan, language=language)

    logger.info("Study plan generation pipeline completed successfully")

    return study_plan

