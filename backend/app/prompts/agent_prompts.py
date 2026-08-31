APP_SYSTEM_INSTRUCTIONS = """
Formatting instructions:
- Use Markdown when it improves readability.
- When using Markdown tables, always use clear, separate column headers and valid Markdown table syntax.
""".strip()


def build_agent_system_prompt(
    user_system_prompt: str | None = None,
) -> str:

    user_prompt = (
        user_system_prompt or ""
    ).strip()

    if not user_prompt:
        return APP_SYSTEM_INSTRUCTIONS

    return f"""
{user_prompt}

{APP_SYSTEM_INSTRUCTIONS}
""".strip()