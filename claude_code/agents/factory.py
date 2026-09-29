from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from claude_code.llm.factory import get_llm
from claude_code.agents.tools import search_codebase
from claude_code.observability.logger import get_logger
from claude_code.memory.short_term import get_checkpointer,get_summarization_middleware
from claude_code.tools.terminal_tools import run_command, run_in_directory
from claude_code.tools.filesystem_tools import (
    read_file,
    write_file,
    append_file,
    delete_file,
    list_directory,
    file_exists,
)
from claude_code.mcp.ClaudeCode__mcp_client import get_claudecode_mcp_tools
from claude_code.skills.skill_tools import load_skill, build_skills_prompt

logger = get_logger(__name__)
SYSTEM_PROMPT = """You are a senior software engineer with deep knowledge of the codebase.
Always use the search_codebase tool before answering any question.
Reference specific file names, function names and line numbers in your answers.
If you cannot find the answer in the codebase, say so explicitly."""

async def build_agent(checkpointer):
  """Create and return a LangChain agent."""
  llm = get_llm()
  skills_prompt = build_skills_prompt()
  full_prompt = SYSTEM_PROMPT
  if skills_prompt:
    full_prompt = SYSTEM_PROMPT+"\n\n"+ skills_prompt
  mcp_tools = await get_claudecode_mcp_tools()
  tools = [search_codebase,
           load_skill,
        run_command,
        run_in_directory,
        *mcp_tools,
0
       
        ] 
  middleware = get_summarization_middleware()
  logger.info("Creating agent")
  return create_agent(
      llm,
      tools=tools,
      system_prompt=full_prompt,
      checkpointer=checkpointer,
      middleware=[middleware]

  )

