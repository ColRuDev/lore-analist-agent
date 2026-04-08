from langchain.agents import create_agent
from langchain_core.tools import BaseTool, StructuredTool

from src.logger import get_logger
from src.models.google import GoogleLLMModel, get_llm_model
from src.prompts.lore_analyst import SYS_PROMPT

logger = get_logger(__name__)


def get_analyst_agent(
    tools: list[BaseTool | StructuredTool],
    model: GoogleLLMModel = GoogleLLMModel.GEMINI_2_5_FLASH,
):
    llm = get_llm_model(model)
    logger.info(f"Model loaded: {model.value}")

    try:
        agent = create_agent(llm, tools, system_prompt=SYS_PROMPT)
        logger.info("Agent created")
        return agent
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise
