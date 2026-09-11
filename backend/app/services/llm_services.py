import json
import re

from openai import AsyncOpenAI

from app.core.config import settings


class LLMService:

    def __init__(self):
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key
        )

    async def chat(
        self,
        message: str,
        system_prompt: str | None = None,
        model: str = "gpt-5.2",
        tools: list[dict] | None = None,
    ):
        response = await self.client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt or "",
                },
                {
                    "role": "user",
                    "content": message,
                },
            ],
            tools=tools or [],
        )

        return response

    async def generate_final_response(
            self,
            user_message: str,
            tool_name: str,
            tool_arguments: dict,
            tool_result: str,
            system_prompt: str | None = None,
            model: str = "gpt-5.2",
    ):
        response = await self.client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt or "",
                },
                {
                    "role": "user",
                    "content": user_message,
                },
                {
                    "role": "assistant",
                    "tool_calls" : [
                        {
                            "id": "mcp_tool_call",
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(tool_arguments),
                            },
                        }

                    ],
                },
                {
                    "role": "tool",
                    "tool_call_id": "mcp_tool_call",
                    "content": tool_result,
                }

            ]
        )

        return response.choices[0].message.content or ""




    async def continue_conversation(
            self,
            messages: list[dict],
            tools: list[dict],
            model: str = "gpt-5.2",
    ):
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools or [],
        )

        return response.choices[0].message



    async def generate_conversation_title(
            self,
            messages: list[dict],
    ) -> str:
        title_messages = [
        {
            "role": "system",
            "content": (
                "Generate a very short title for this conversation. "
                "Summarize only the main topic. "
                "Use a MAXIMUM of 4 words. "
                "Keep the title under 35 characters. "
                "Use the same language as the conversation. "
                "Return only the title. "
                "Do not use quotation marks. "
                "Do not add punctuation at the end. "
                "Do not include unnecessary details."
            ),
        },
        {
            "role": "user",
            "content": (
                "Conversation:\n"
                + "\n".join(
                    f"{message.get('role')}: "
                    f"{message.get('content') or ''}"
                    for message in messages
                    if message.get("role") in {
                        "user",
                        "assistant",
                    }
                )
            ),
        },
    ]
        response = await self.client.chat.completions.create(
            model="gpt-5.2",
            messages=title_messages,
        )

        title = response.choices[0].message.content or ""

        if not title:
            return "New Conversation"

        return title.strip()

    @staticmethod
    def normalize_server_name(
            server_name: str,
    ) -> str:

        normalized = server_name.lower()

        normalized = re.sub(
            r"[^a-z0-9]+",
            "_",
            normalized,
        )

        return normalized.strip("_")

    @classmethod
    def get_openai_tool_name(
            cls,
            tool,
            server_name: str,
    ) -> str:

        server_namespace = cls.normalize_server_name(
            server_name
        )

        return f"{server_namespace}__{tool.name}"

    @classmethod
    def mcp_tools_to_openai_tools(
            cls,
            mcp_tools,
            server_names: dict[int, str],
    ):
        tools = []

        for tool in mcp_tools:

            schema = dict(
                tool.input_schema or {}
            )

            if "type" not in schema:
                schema["type"] = "object"

            if "properties" not in schema:
                schema["properties"] = {}

            server_name = server_names.get(
                tool.mcp_server_id
            )

            if not server_name:
                raise ValueError(
                    f"MCP server name not found "
                    f"for server id "
                    f"{tool.mcp_server_id}"
                )

            openai_tool_name = (
                cls.get_openai_tool_name(
                    tool,
                    server_name,
                )
            )

            tools.append({
                "type": "function",
                "function": {
                    "name": openai_tool_name,
                    "description": (
                        f"[MCP Server: {server_name}] "
                        f"{tool.description or ''}"
                    ),
                    "parameters": schema,
                },
            })

        return tools



