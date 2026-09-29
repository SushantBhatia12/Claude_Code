import chromadb
from claude_code.config import config
from claude_code.llm.factory import get_embedder
from claude_code.observability.logger import get_logger

logger = get_logger(__name__)

def retrieve(query: str, k: int = 5) -> list[dict]:
  """
  Embed the query and find the k most similar chunks in ChromaDB.
  Returns a list of results with content and metadata.
  """
  print(f"path for chroma client is  {config["chromadb"]["persist_dir"]}")
  print(f"path for collection is {config["chromadb"]["collection_name"]} ")
  chroma_client = chromadb.PersistentClient(path=config["chromadb"]["persist_dir"])
  collection = chroma_client.get_or_create_collection(name=config["chromadb"]["collection_name"])


  logger.info(f"Retrieving top {k} chunks for query: {query}")


  # Use the same embedder as the indexer — model must match or results will be wrong
  embedder = get_embedder()
  query_embedding = embedder.embed_query(query)


  results = collection.query(
      query_embeddings=[query_embedding],
      n_results=k,
      include=["documents", "metadatas", "distances"]
  )
  print(f"the result for the code :{results["documents"][0]}")

  chunks = []
  for doc, meta, dist in zip(
      results["documents"][0],
      results["metadatas"][0],
      results["distances"][0]
  ):     
      
      chunks.append({
          "content": doc,
          "source": meta["source"],
          "name": meta["name"],
          "type": meta["type"],
          "start_line": meta["start_line"],
          "end_line": meta["end_line"],
          "distance": dist,   # lower = more similar
      })
      logger.debug(f"  Retrieved {meta['type']} '{meta['name']}' from {meta['source']} (distance: {dist:.4f})")


  logger.info(f"Retrieved {len(chunks)} chunks")
  return chunks


    


