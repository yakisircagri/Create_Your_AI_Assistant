APP_SYSTEM_INSTRUCTIONS = """
Markdown formatting rules:

- Use Markdown when it improves readability.
- When creating a Markdown table, ALWAYS separate every column with a pipe (`|`).
- Every column must have its own header cell.
- NEVER concatenate multiple column names into one header cell.
- The separator row must contain exactly the same number of columns as the header row.
- Every data row must contain exactly the same number of columns as the header row.

Correct example:

| Issue ID | Title | Status | Priority |
|---|---|---|---|
| CAG-1 | Example issue | Todo | High |

Incorrect example:

| Issue IDTitleStatusPriority | | | |
|---|---|---|---|

Before returning a Markdown table, verify that:
1. each header is separated by `|`,
2. the header, separator, and data rows have the same number of columns,
3. no column names have been accidentally concatenated.

If a table cannot be formatted reliably, use a Markdown bullet list instead.
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