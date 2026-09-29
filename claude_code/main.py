import os
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt
import chromadb
import asyncio

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from  claude_code.agents.factory import build_agent
from claude_code.config import config
from claude_code.observability.logger import get_logger
from claude_code.context.indexers.factory import get_indexer, get_index_inspector
from claude_code.context.indexers.semantic_chroma import index_codebase
from claude_code.llm.factory import get_llm, get_embedder
from claude_code.memory.short_term import get_checkpointer_db_path
from claude_code.agents.orchestrator import handle_query
from claude_code.memory.session import get_current_session, new_session, switch_session

load_dotenv(Path(__file__).parent.parent / ".env")
console = Console()
logger = get_logger(__name__)

def get_or_create_index():
    repo_path = str(Path.cwd())
    logger.info(f"Checking index for: {repo_path}")
    console.print(f"[dim]Checking index for {repo_path}...[/dim]")
    return get_indexer()(repo_path)

def show_semantic_index(collection: chromadb.Collection) -> None:
 """Display all documents stored in the ChromaDB collection."""
 results = collection.get(include=["documents", "metadatas", "embeddings"])
 console.print(f"\n[bold]Semantic Index — {collection.count()} chunks[/bold]\n")


 for i, (doc, meta, emb) in enumerate(zip(
     results["documents"],
     results["metadatas"],
     results["embeddings"]
 )):
     console.print(f"[bold cyan]── Chunk {i+1} ──────────────────────────[/bold cyan]")
     console.print(f"  File     : {meta['source']}")
     console.print(f"  Name     : {meta['name']} ({meta['type']})")
     console.print(f"  Lines    : {meta['start_line']} - {meta['end_line']}")
     console.print(f"  Embedding: [{', '.join(f'{v:.4f}' for v in emb[:5])}...] ({len(emb)} dims)")
     console.print(f"  Code     :\n[dim]{doc[:300]}[/dim]\n")

async def initialize(checkpointer):
   """Bootstrap LLM, embedder, index and session before the REPL starts."""
   llm = get_llm()
   embedder = get_embedder()
   console.print(f"[dim]LLM: {config['llm']['provider']} / {config['llm']['model']}[/dim]")
   console.print(f"[dim]Embedder: {config['embeddings']['provider']} / {config['embeddings']['model']}[/dim]")


   index = get_or_create_index()
   agent = await build_agent(checkpointer)
   session_id = get_current_session()
   console.print(f"[dim]Session: {session_id}[/dim]")
   console.print(f"[green]✓ Ready[/green]\n")
   return llm, embedder, index, agent, session_id

async def _run_async():
   logger.info("Starting Claude code")
   console.print("\n[bold blue] Claude code[/bold blue] — RAG-powered code assistant")


   async with AsyncSqliteSaver.from_conn_string(get_checkpointer_db_path()) as checkpointer:
      llm, embedder, index, agent, session_id = await initialize(checkpointer)
      console.print("Type [bold]'/exit'[/bold] to quit\n")
      while True:
          user_input = Prompt.ask("[bold green]>[/bold green]")
          if not user_input.strip():
              continue
          if user_input.lower() in ("/exit", "/quit"):
              logger.info("Shutting down")
              console.print("[dim]Goodbye![/dim]")
              break
          elif user_input.startswith("/ask "):
              question = user_input.removeprefix("/ask ").strip()
              logger.info(f"Ask command received: {question}")
              console.print(f"[dim]Searching for: {question}...[/dim]")
              response = await handle_query(agent, question, session_id)
              console.print(response)
          elif user_input == "/new_session":
              session_id = new_session()
              console.print(f"[green]New session started: {session_id}[/green]")
          elif user_input.startswith("/switch "):
             target = user_input.removeprefix("/switch ").strip()
             session_id = switch_session(target)
             console.print(f"[green]Switched to session: {session_id}[/green]")
          elif user_input == "/session":
              console.print(f"[dim]Current session: {session_id}[/dim]")
          elif user_input == "/show_index":
             logger.info("Showing index")
             get_index_inspector()(index)
          else:
             logger.warning(f"Unknown command received: {user_input}")
             console.print("[yellow]Unknown command. Try:[/yellow]")
             console.print("  [bold]/ask <question>[/bold]          — ask a question about the codebase")
             console.print("  [bold]/show_index[/bold]              — show all chunks in the index")
             console.print("  [bold]/new_session[/bold]             — start a fresh conversation")
             console.print("  [bold]/switch <session_id>[/bold]     — resume a past session")
             console.print("  [bold]/session[/bold]                 — show current session id")

def run():
   asyncio.run(_run_async())

if __name__ == "__main__":
   run()

