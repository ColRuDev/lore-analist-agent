from src.agent.core import get_analyst_agent
from src.agent.exceptions import ModelUnavailableError
from src.agent.runner import AgentRunner
from src.models.google import GoogleLLMModel
from src.tools import get_all_tools

_MODEL_COMMAND = "/model"

_HELP_TEXT = f"""
Commands:
  {_MODEL_COMMAND}              — show the current model and list available models
  {_MODEL_COMMAND} <name>       — switch to a different model (history is preserved)
  exit                  — quit the session
""".strip()


def _print_model_list(current: GoogleLLMModel) -> None:
    print("\nAvailable models:")
    for m in GoogleLLMModel:
        marker = " (active)" if m is current else ""
        print(f"  {m.value}{marker}")
    print()


def _resolve_model(name: str) -> GoogleLLMModel | None:
    """Match *name* against enum names (case-insensitive). Returns None if not found."""
    for m in GoogleLLMModel:
        if m.value == name:
            return m
    return None


def run_cli() -> None:
    """Run the Lore Analyst agent as an interactive CLI session."""
    tools = get_all_tools()
    current_model = GoogleLLMModel.GEMINI_3_1_FLASH_LITE

    agent = get_analyst_agent(tools, current_model)
    runner = AgentRunner(agent)

    print("--- Lore Analyst Agent (LAA) ---")
    print(f"Model: {current_model.value}")
    print("Type 'help' for available commands or 'exit' to quit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("Goodbye.")
            break

        if user_input.lower() == "help":
            print(f"\n{_HELP_TEXT}\n")
            continue

        # ── /model command ────────────────────────────────────────────────────
        if user_input.lower().startswith(_MODEL_COMMAND):
            remainder = user_input[len(_MODEL_COMMAND) :].strip()

            if not remainder:
                # Just "/model" — show list
                _print_model_list(current_model)
                continue

            target = _resolve_model(remainder)
            if target is None:
                print(f"\nUnknown model '{remainder}'.")
                _print_model_list(current_model)
                continue

            if target is current_model:
                print(f"\nAlready using {current_model.value}.\n")
                continue

            print(f"\nSwitching model: {current_model.value} → {target.value} ...")
            current_model = target
            new_agent = get_analyst_agent(tools, current_model)
            runner.swap_agent(new_agent)
            print("Model switched. Conversation history preserved.\n")
            continue
        # ─────────────────────────────────────────────────────────────────────

        print("\nLAA: ", end="", flush=True)
        try:
            for chunk in runner.stream(user_input):
                print(chunk, end="", flush=True)
            print("\n")
        except ModelUnavailableError as e:
            print(f"\n⚠️  {e}\n")


if __name__ == "__main__":
    run_cli()
