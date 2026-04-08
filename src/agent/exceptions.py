"""Custom exceptions for the agent layer."""


class ModelUnavailableError(Exception):
    """Raised when the LLM API returns a 503 / high-demand transient error.

    The underlying cause is logged by AgentRunner before this is raised,
    so callers should only show the user-friendly ``str(exc)`` message.
    """
