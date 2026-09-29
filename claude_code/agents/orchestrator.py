from claude_code.agents.factory import build_agent
from claude_code.observability.logger import get_logger

logger = get_logger(__name__)


async def handle_query(agent, question: str, thread_id: str) -> str:
   """Run a user query through the async agent."""
   logger.info(f"Handling query: {question}")
   agent_config = {"configurable": {"thread_id": thread_id}}
   try:
      response = await agent.ainvoke(
         {"messages": [{"role": "user", "content": question}]},
         agent_config,
      )
      return response["messages"][-1].content
   except Exception as e:
      logger.error(f"Agent error: {e}")
      return f"Error: {e}"


 