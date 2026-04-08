from enum import Enum

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings


class GoogleEmbeddingModel(str, Enum):
    GEMINI_EMBEDDING_001 = "models/gemini-embedding-001"
    TEXT_EMBEDDING_004 = "models/text-embedding-004"


class GoogleLLMModel(str, Enum):
    GEMINI_3_1_FLASH_LITE = "gemini-3.1-flash-lite-preview"
    GEMINI_3_0_FLASH = "gemini-3-flash-preview"
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_5_FLASH_LITE = "gemini-2.5-flash-lite"


def get_embeddings_model(
    model: GoogleEmbeddingModel = GoogleEmbeddingModel.GEMINI_EMBEDDING_001,
) -> GoogleGenerativeAIEmbeddings:
    return GoogleGenerativeAIEmbeddings(
        model=model.value, task_type="retrieval_document"
    )


def get_llm_model(
    model: GoogleLLMModel = GoogleLLMModel.GEMINI_2_5_FLASH,
) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(model=model.value)
