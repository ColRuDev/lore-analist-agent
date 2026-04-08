"""
Entry point for the Lore Analyst Agent.

Usage:
    python -m src                  # default: CLI mode
    python -m src --mode cli       # interactive CLI
    python -m src --mode test      # run predefined test queries
    uv run lore-agent              # via pyproject.toml script
"""

import argparse

from dotenv import load_dotenv

load_dotenv()


def run_test() -> None:
    """Run a set of predefined queries against the agent for quick validation."""
    from src.agent.core import get_analyst_agent
    from src.agent.runner import AgentRunner
    from src.tools import get_all_tools

    agent = get_analyst_agent(get_all_tools())
    runner = AgentRunner(agent)

    test_queries = [
        "What is the main conflict in the lore database?",
        "Search the web for recent news about BioShock 4.",
        "Based on the previous answer, what studio is developing it?",
    ]

    print("=== Running test queries ===\n")
    for query in test_queries:
        print(f"[Q] {query}")
        response = runner.invoke(query)
        print(f"[A] {response}\n{'-' * 60}\n")


def run_cli() -> None:
    """Start the interactive CLI session."""
    from src.agent.chat import run_cli as _run_cli
    _run_cli()


def main() -> None:
    parser = argparse.ArgumentParser(description="Lore Analyst Agent")
    parser.add_argument(
        "--mode",
        choices=["cli", "test"],
        default="cli",
        help="Interaction mode: 'cli' for interactive chat, 'test' for quick validation (default: cli)",
    )
    args = parser.parse_args()

    if args.mode == "test":
        run_test()
    else:
        run_cli()


if __name__ == "__main__":
    main()
