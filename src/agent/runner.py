from typing import Iterator

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from src.agent.exceptions import ModelUnavailableError
from src.logger import get_logger

logger = get_logger(__name__)

_UNAVAILABLE_MARKERS = ("503", "UNAVAILABLE", "high demand", "ServiceUnavailable")


def _is_unavailable(exc: Exception) -> bool:
    """Return True if *exc* represents a transient 503 / high-demand API error."""
    text = str(exc)
    return any(marker in text for marker in _UNAVAILABLE_MARKERS)


class AgentRunner:
    """
    Wraps a LangChain agent and manages conversation history.

    Provides invoke() for full responses and stream() for token-by-token output,
    decoupling the agent logic from the transport layer (CLI, API, GUI).
    """

    def __init__(self, agent) -> None:
        self._agent = agent
        self._history: list[BaseMessage] = []

    def swap_agent(self, agent) -> None:
        """
        Replace the underlying agent (e.g. after a model change).
        Conversation history is preserved so the session continues seamlessly.

        Args:
            agent: The new LangChain agent to use for subsequent messages.
        """
        self._agent = agent
        logger.info("Agent swapped; conversation history retained")

    def invoke(self, query: str) -> str:
        """
        Send a query to the agent and return the full response string.

        Args:
            query: The user's input message.

        Returns:
            The agent's final text response.
        """
        self._history.append(HumanMessage(content=query))
        logger.info(f"Invoking agent (history length: {len(self._history)})")

        try:
            response = self._agent.invoke({"messages": self._history})
        except Exception as e:
            logger.error(f"Agent invocation failed: {e}")
            if _is_unavailable(e):
                raise ModelUnavailableError(
                    "The model is currently experiencing high demand. "
                    "Please try again later or change model."
                ) from e
            raise

        ai_message: AIMessage = response["messages"][-1]
        self._history.append(ai_message)

        return str(ai_message.content)

    def stream(self, query: str) -> Iterator[str]:
        """
        Send a query to the agent and yield response tokens as they are generated.

        Uses stream_mode="messages" which yields (token_chunk, metadata) tuples,
        enabling true token-by-token output. Only text tokens from the LLM agent
        node are yielded; tool-call and tool-result chunks are skipped.

        Args:
            query: The user's input message.

        Yields:
            Text chunks from the agent's final response stream.
        """
        self._history.append(HumanMessage(content=query))
        logger.info(f"Streaming agent response (history length: {len(self._history)})")

        accumulated = ""

        try:
            for token, metadata in self._agent.stream(
                {"messages": self._history},
                stream_mode="messages",
            ):
                # Only emit text from the LLM node; skip tool-call/tool-result chunks
                if metadata.get("langgraph_node") != "model" or not token.content:
                    continue
                text: str = ""
                # content can be a plain string or a list of typed blocks (e.g. [{'type': 'text', 'text': '...'}])
                if isinstance(token.content, list):
                    text = "".join(
                        block.get("text", "")
                        for block in token.content
                        if isinstance(block, dict) and block.get("type") == "text"
                    )
                else:
                    text = str(token.content)

                if text:
                    accumulated += text
                    yield text
        except Exception as e:
            logger.error(f"Stream failed: {e}")
            if not accumulated:
                # Nothing was yielded — roll back the HumanMessage we appended
                self._history.pop()
            if _is_unavailable(e):
                raise ModelUnavailableError(
                    "The model is currently experiencing high demand. "
                    "Please try again later or change model."
                ) from e
            raise

        if accumulated:
            self._history.append(AIMessage(content=accumulated))
        else:
            logger.warning("Stream completed with no text content")

    def clear_history(self) -> None:
        """Reset the conversation history."""
        self._history = []
        logger.info("Conversation history cleared")
