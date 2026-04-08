from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import BaseTool, StructuredTool, tool
from langchain_core.tools.retriever import create_retriever_tool

from src.logger import get_logger
from src.retriever import get_retriever

logger = get_logger(__name__)


def get_retriever_tool() -> StructuredTool:
    """Return a LangChain tool that searches the local lore vector database."""
    retriever = get_retriever()

    if not retriever:
        logger.error("Failed to get retriever")
        raise ValueError("Failed to get retriever")

    try:
        lore_tool = create_retriever_tool(
            retriever,
            name="lore_database_search",
            description=(
                "Useful for answering questions about scripts, "
                "game lore, plot points, or character details. "
                "Input should be a specific search query."
            ),
        )
        logger.info("Created lore_database_search tool")
        return lore_tool
    except Exception as e:
        logger.error(f"Failed to create lore_database_search tool: {e}")
        raise


def get_web_search_tool() -> BaseTool:
    """Return a LangChain tool that performs web searches via DuckDuckGo."""
    try:
        search = DuckDuckGoSearchRun()

        @tool
        def web_search(query: str) -> str:
            """Search the web for current information about video game releases, studio news, or public lore not found in the local database. Use this if the local database returns no results."""
            return search.run(query)

        logger.info("Created web_search tool")
        return web_search
    except Exception as e:
        logger.error(f"Failed to create web_search tool: {e}")
        raise


def get_all_tools() -> list[BaseTool | StructuredTool]:
    """Return all available tools for the agent."""
    tools = []

    retriever_tool = get_retriever_tool()
    if retriever_tool:
        tools.append(retriever_tool)

    web_search_tool = get_web_search_tool()
    if web_search_tool:
        tools.append(web_search_tool)

    return tools
