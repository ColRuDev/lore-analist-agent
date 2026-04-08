from langchain_chroma import Chroma
from langchain_core.vectorstores import VectorStoreRetriever

from src.configs import CHROMA_PATH, COLLECTION_NAME, RETRIEVER_FETCH_K, RETRIEVER_K, RETRIEVER_LAMBDA_MULT, SEARCH_STRATEGY
from src.logger import get_logger
from src.models.google import get_embeddings_model

logger = get_logger(__name__)


def get_retriever() -> VectorStoreRetriever:
    """
    Returns a Chroma retriever optimized.
    """
    try:
        embeddings = get_embeddings_model()
        vector_store = Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME,
        )
        logger.info("Retriever created successfully")
        retriever = vector_store.as_retriever(
            search_type=SEARCH_STRATEGY,
            search_kwargs={"k": RETRIEVER_K, "fetch_k": RETRIEVER_FETCH_K, "lambda_mult": RETRIEVER_LAMBDA_MULT},
        )
        logger.info(
            f"Retriever configured successfully with strategy: {SEARCH_STRATEGY}"
        )
        return retriever
    except Exception as e:
        logger.error(f"Failed to create Chroma retriever: {e}")
        raise
