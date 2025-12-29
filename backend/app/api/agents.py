from pydantic_ai import Agent, RunContext
from app.api.models import StudyMaterial, KnowledgeGraph, StudyPlan, StudyMethod, StudyPlanEvaluation, StudyPlanEvaluationAssesments
from dotenv import load_dotenv

load_dotenv()

manager_agent = Agent(
  model="gpt-4o",
  deps_type=StudyMaterial,
  output_type=StudyPlan,
  output_retries=1,
  system_prompt="""
  You are a study-plan manager agent.

  You are responsible for orchestrating other agents.

  Workflow rules:
  1. You must first create a knowledge graph from the study material.
  2. You must evaluate the quality of the knowledge graph.
  3. If the graph quality is not "good":
    - You must refine or regenerate the graph before proceeding.
  4. Only once the graph is assessed as "good", generate a study plan.
  5. You must evaluate whether the study plan is realistically achievable.
  6. If the study plan is not achievable:
    - You must revise the study plan accordingly.
  7. Only finalize and return the StudyPlan once it is confirmed as achievable.

  Constraints:
  - Do not skip any steps in the workflow.
  - Do not generate a study plan before confirming the graph quality.
  - Do not finalize the study plan before confirming its achievability.

  Limits:
    - You may attempt to improve the knowledge graph at most 2 times.
    - You may attempt to revise the study plan at most 1 time.
    - If quality is still insufficient, proceed with the best available result.

  """
)

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
  model="gpt-4o",
  deps_type=[StudyMaterial, KnowledgeGraph],
  output_type=str,
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
  model="gpt-4o",
  deps_type=[StudyMaterial, StudyPlan],
  output_type=StudyPlanEvaluation,
  output_retries=1,
  system_prompt="Evaluate the achievability of the provided study plan based on the study material."
)

@manager_agent.tool
async def generate_knowledge_graph(ctx: RunContext[StudyMaterial]) -> KnowledgeGraph:
  result = await knowledge_graph_agent.run(
    deps=ctx.deps,
    user_prompt=f"Study material: {ctx.deps.study_material}",
  )
  return result.output

@manager_agent.tool
async def evaluate_knowledge_graph(ctx: RunContext[StudyMaterial], graph: KnowledgeGraph) -> str:
  prompt = f"""
  Given the following knowledge graph:

  Nodes:
  {', '.join([f'{node.name}: {node.description}' for node in graph.nodes])}

  Edges:
  {', '.join([f'({edge.from_topic} {edge.relationship.value} {edge.to_topic})' for edge in graph.edges])}

  Evaluate the quality of this knowledge graph based on:
  - Completeness: Are all key topics from the study material included?
  - Accuracy: Are the relationships between topics correctly represented?
  - Clarity: Is the graph easy to understand and navigate?

  Provide a concise assessment as either "good" or "needs improvement", along with a brief justification.
  """
  result = await graph_critic_agent.run(
    deps=[ctx.deps, graph],
    user_prompt=prompt
  )
  return result.output

@manager_agent.tool
async def schedule_study_plan(ctx: RunContext[StudyMaterial], graph: KnowledgeGraph) -> StudyPlan:
  prompt = f"""
  You are generating a structured StudyPlan object.

  Input:
  - Study material
  - A validated KnowledgeGraph with topics and relationships

  Knowledge Graph Topics:
  {', '.join([node.name for node in graph.nodes])}

  Knowledge Graph Relationships:
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
    deps=[ctx.deps, graph],
    user_prompt=prompt
  )
  return result.output

@manager_agent.tool
async def evaluate_study_plan(ctx: RunContext[StudyMaterial], plan: StudyPlan) -> StudyPlanEvaluation:
  prompt = f"""
  Given the following study plan:

  {plan}

  Evaluate whether this study plan is realistically achievable based on:
  - Time management: Are the time allocations reasonable?
  - Topic coverage: Does it adequately cover all topics from the knowledge graph?
  - Study methods: Are the recommended methods effective for learning the material?

  Provide a concise assessment as one of {', '.join([e.value for e in StudyPlanEvaluationAssesments])}, along with a brief justification.
  """
  result = await schedule_critic_agent.run(
    deps=[ctx.deps, plan],
    user_prompt=prompt
  )
  return result.output

async def generate_study_plan(material: StudyMaterial) -> StudyPlan:
  result = await manager_agent.run(
    deps=material,
    user_prompt="Create a comprehensive study plan based on the provided study material."
  )
  return result.output
