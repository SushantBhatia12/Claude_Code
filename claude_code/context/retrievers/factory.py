from claude_code.config import config
from claude_code.observability.logger import get_logger

logger = get_logger(__name__)


def get_retriever():
    mode = config["rag"]["mode"]
    provider = config["vector_store"]["provider"]

    if mode == "hybrid" and provider == "qdrant":
        from .hybrid_qdrant import retrieve
    elif provider == "qdrant":
        from .semantic_quadrant import retrieve
    else:
        from .semantic_chroma import retrieve

    return retrieve