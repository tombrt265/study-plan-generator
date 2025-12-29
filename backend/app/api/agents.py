from pydantic_ai import Agent, RunContext
from app.api.models import Evaluation, Quality, StudyMaterial, KnowledgeGraph, StudyPlan, StudyMethod, StudyPlanEvaluation, StudyPlanAchievability
from dotenv import load_dotenv

load_dotenv()

knowledge_graph_agent = Agent(
  model="gpt-4o",
  deps_type=StudyMaterial,
  output_type=KnowledgeGraph,
  output_retries=1,
  system_prompt="""
  With study material as input, your task is to construct a knowledge graph.

  Do NOT use external knowledge.

  Graph construction rules:

  1. Nodes
  - Extract key topics from the study material.
  - Each topic must have:
    - a short, precise name
    - a concise description derived from the study material

  2. Relationships (Edges)
  - Create relationships ONLY between extracted topics.
  - Each relationship must be one of:
    - PRECEDES: topic A is introduced before or is a prerequisite for topic B
    - FOLLOWS: topic A builds upon or comes after topic B
    - RELATED_TO: topics are conceptually related without clear ordering
  - Relationships must be justified by the study material.

  3. Output format
  - Return the result strictly in the following structured format:
    KnowledgeGraph {
      nodes: [Topic, ...],
      edges: [(Topic name, TopicRelationship, Topic name), ...]
    }

  Constraints:
  - Use consistent topic names across nodes and edges.
  - Do not duplicate topics.
  - Do not include explanations or commentary outside the structured output.
  """
)

graph_critic_agent = Agent(
  model="gpt-4o-mini",
  deps_type=[StudyMaterial, KnowledgeGraph],
  output_type=Evaluation,
  output_retries=1,
  system_prompt="You are a knowledge graph critic. Evaluate the quality of the provided knowledge graph based on the study material."
)

scheduling_agent = Agent(
  model="gpt-4o",
  deps_type=[StudyMaterial, KnowledgeGraph],
  output_type=StudyPlan,
  output_retries=1,
  system_prompt="Create a detailed study plan based on the provided knowledge graph and the study material."
)

schedule_critic_agent = Agent(
  model="gpt-4o-mini",
  deps_type=[StudyMaterial, StudyPlan],
  output_type=StudyPlanEvaluation,
  output_retries=1,
  system_prompt="Evaluate the achievability of the provided study plan based on the study material."
)

translation_agent = Agent(
  model="gpt-4o-mini",
  deps_type=StudyPlan,
  output_type=StudyPlan,
  output_retries=1,
  system_prompt="Translate the study plan into a different language if necessary. Maintain the original structure and content of the study plan."
)

async def generate_knowledge_graph(material: StudyMaterial) -> KnowledgeGraph:
  result = await knowledge_graph_agent.run(
    deps=material,
    user_prompt=f"""
    IMPORTANT:
    The following study material is the ONLY source of information.
    Do NOT use prior knowledge, assumptions, or general educational structures.
    If something is not explicitly present, omit it.

    Use the provided study material to construct a knowledge graph:

    Study Material:
    {material.study_material}
    """,
  )
  return result.output

async def evaluate_knowledge_graph(material: StudyMaterial, graph: KnowledgeGraph) -> Evaluation:
  prompt = f"""
  Given the following knowledge graph and study material:

  Knowledge Graph:
  Nodes:
  {', '.join([f'{node.name}: {node.description}' for node in graph.nodes])}

  Edges:
  {', '.join([f'({edge.from_topic} {edge.relationship.value} {edge.to_topic})' for edge in graph.edges])}

  Study Material:
  {material.study_material}

  Evaluate the quality of this knowledge graph based on:
  - Completeness: Are all key topics from the study material included?
  - Accuracy: Are the relationships between topics correctly represented?
  - Clarity: Is the graph easy to understand and navigate?

  Return an Evaluation:
  1. Choose a quality out of {', '.join([q.value for q in Quality])}
  2. Provide a brief justification.
  """
  result = await graph_critic_agent.run(
    deps=[material, graph],
    user_prompt=prompt
  )
  return result.output

async def schedule_study_plan(material: StudyMaterial, graph: KnowledgeGraph) -> StudyPlan:
  prompt = f"""
  You are generating a structured StudyPlan object.

  Input:
  - Study material
  - A validated KnowledgeGraph with topics and relationships

  Study Material:
  {material.study_material}

  Knowledge Graph:
  Nodes:
  {', '.join([f'{node.name}: {node.description}' for node in graph.nodes])}

  Edges:
  {', '.join([f'({edge.from_topic} {edge.relationship.value} {edge.to_topic})' for edge in graph.edges])}

  Your task:
  Create a StudyPlan that strictly conforms to the StudyPlan schema.

  Rules:

  1. Overview
  - Provide a concise summary of the overall study strategy.
  - Do not repeat the study material verbatim.

  2. Study Sessions
  - Create a list of StudySession objects.
  - Each StudySession MUST:
    - Cover exactly ONE Topic from the knowledge graph.
    - Reference the Topic object consistently (same name as in the graph).
    - Include a short but precise explanation of what the student should learn about this topic.
    - Specify a realistic duration in minutes (between 30 and 180).
    - Include one or more StudyMethod values chosen ONLY from:
      {', '.join([m.value for m in StudyMethod])}

  3. Ordering
  - Order the sessions logically using the knowledge graph relationships:
    - PRECEDES → earlier session
    - FOLLOWS → later session
  - RELATED_TO topics may be placed adjacently.

  4. Coverage
  - Every Topic in the knowledge graph MUST appear in exactly one StudySession.
  - Do NOT invent new topics.
  - Do NOT omit any topic.

  5. Total Duration
  - Set total_duration_hours to the sum of all session durations, rounded to whole hours.

  Output Constraints:
  - Return ONLY a valid StudyPlan object.
  - Do NOT use Markdown.
  - Do NOT include headings, bullet points, or explanatory text outside the schema.
  """

  result = await scheduling_agent.run(
    deps=[material, graph],
    user_prompt=prompt
  )
  return result.output

async def evaluate_study_plan(material: StudyMaterial, plan: StudyPlan) -> StudyPlanEvaluation:
  prompt = f"""
  Given the following study material:
  {material.study_material}

  Given the following study plan:

  {plan}

  Evaluate whether this study plan is realistically achievable based on:
  - Time management: Are the time allocations reasonable?
  - Topic coverage: Does it adequately cover all topics from the knowledge graph?
  - Study methods: Are the recommended methods effective for learning the material?

  Provide a concise assessment as one of {', '.join([e.value for e in StudyPlanAchievability])}, along with a brief justification.
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
    Translate the given study plan into {language}.

    Study Plan:
    Overview:
    {plan.overview}

    Study Sessions:
    {', '.join([f'Topic: {session.topic.name}, Information: {session.information}, Duration: {session.duration_minutes}, Methods: {", ".join([method.value for method in session.methods])}' for session in plan.sessions])}

    Total Duration Hours: {plan.total_duration_hours}
    """
  )
  return result.output

async def generate_study_plan(material: StudyMaterial, language: str) -> StudyPlan:
  knowledge_graph_quality = Quality.BAD
  attempts = 0

  while knowledge_graph_quality != Quality.GOOD and attempts < 2:
    graph = await generate_knowledge_graph(material)
    evaluation = await evaluate_knowledge_graph(material, graph)
    knowledge_graph_quality = evaluation.quality
    # justification not yet used
    attempts += 1

  study_plan = StudyPlan(overview="", sessions=[], total_duration_hours=0)
  study_plan_achievability = StudyPlanAchievability.UNACHIEVABLE
  attempts = 0

  while study_plan_achievability != StudyPlanAchievability.ACHIEVABLE and attempts < 2:
    study_plan = await schedule_study_plan(material, graph)
    plan_evaluation = await evaluate_study_plan(material, study_plan)
    study_plan_achievability = plan_evaluation.achievability
    # justification not yet used
    attempts += 1

  study_plan = await translate_study_plan(study_plan, language=language)

  return study_plan
