from pathlib import Path
from time import sleep

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.configs import CHROMA_PATH, COLLECTION_NAME, EMBEDDING_LIMIT
from src.logger import get_logger
from src.models.google import get_embeddings_model
from src.utils.hash import get_text_hash

logger = get_logger(__name__)


def load_pdf_documents(dir_path: str) -> list[Document]:
    """
    Load all PDF files from a specified directory.

    Args:
        dir_path (str): The path to the directory containing PDF files.

    Returns:
        list: A list of loaded PDF documents of Langchain Document type.
    """
    path = Path(dir_path)

    if not path.exists():
        logger.error(f"path {dir_path} not found, create it first")
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    if not path.is_dir():
        logger.error(f"path {dir_path} is not a directory")
        raise ValueError(f"Path is not a directory: {dir_path}")

    try:
        logger.info(f"Loading PDF documents from {path.absolute()}")
        loader = PyPDFDirectoryLoader(path)
        docs = loader.load()

        if not docs:
            logger.warning(f"No PDF documents found in {path}")
        return docs
    except Exception as e:
        logger.error(f"Error loading PDF documents from {dir_path}: {e}")
        raise


def split_documents(docs: list[Document]) -> list[Document]:
    """
    Split a list of Langchain Document objects into chunks.

    Args:
        docs (list[Document]): A list of Langchain Document objects to split.

    Returns:
        list[Document]: A list of split Document objects.
    """
    if not docs:
        logger.warning("No documents to split")
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200,
        add_start_index=True,
        strip_whitespace=True,
        # TODO: use tiktoken to calculate token length
        length_function=len,
    )
    try:
        chunks = splitter.split_documents(docs)
        logger.info(f"{len(chunks)} chunks from {len(docs)} documents")
        return chunks
    except Exception as e:
        logger.error(f"Error splitting documents: {e}")
        raise


def save_chunks_to_db(chunks: list[Document], embeddings_model: Embeddings) -> None:
    if not chunks:
        logger.warning("No chunks to save")
        return
    db = Chroma(
        embedding_function=embeddings_model,
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_PATH,
    )
    existing_data = db.get()
    existing_ids = set(existing_data.get("ids", []))

    chunks_to_embed: list[Document] = []
    ids_to_add: list[str] = []

    for chunk in chunks:
        chunk_id = get_text_hash(chunk.page_content)
        if chunk_id not in existing_ids:
            chunks_to_embed.append(chunk)
            ids_to_add.append(chunk_id)

    if not chunks_to_embed:
        logger.info("No new chunks to add")
        return

    for i in range(0, len(chunks_to_embed), EMBEDDING_LIMIT):
        batch = chunks_to_embed[i : i + EMBEDDING_LIMIT]
        batch_ids = ids_to_add[i : i + EMBEDDING_LIMIT]
        try:
            db.add_documents(batch, ids=batch_ids)
            logger.info(f"Added {len(batch)} new chunks to the database")
        except Exception as e:
            if "429" in str(e):
                logger.warning("Rate limit hit, waiting 60 seconds before retry")
                sleep(60)
                try:
                    db.add_documents(batch, ids=batch_ids)
                    logger.info(f"Added {len(batch)} new chunks (retry)")
                except Exception as retry_error:
                    logger.error(f"Retry failed for batch {i}: {retry_error}")
                    break
            else:
                logger.error(f"Error adding documents: {e}")
                break


if __name__ == "__main__":
    docs = load_pdf_documents("data/")
    if docs:
        chunks = split_documents(docs)
        embeddings_model = get_embeddings_model()
        save_chunks_to_db(chunks, embeddings_model)
