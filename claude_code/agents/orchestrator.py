from claude_code.agents.factory import build_agent
from claude_code.observability.logger import get_logger

logger = get_logger(__name__)


async def handle_query(question: str, thread_id: str) -> str:
   """Entry point for all user queries - builds the agent and runs it."""
   logger.info(f"Handling query: {question}")
   agent = build_agent()
   agent_config = {"configurable": {"thread_id": thread_id}}
   response = await agent.invoke({"messages": [{"role": "user", "content": question}]}, agent_config)
   return response["messages"][-1].content
   return response["output"]


 