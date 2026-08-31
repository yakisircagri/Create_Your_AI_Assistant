import json

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
    def mcp_tools_to_openai_tools(mcp_tools):
        tools = []

        for tool in mcp_tools:
            schema = dict(tool.input_schema or {})

            properties = schema.get("properties", {})

            if properties and "required" not in schema:
                schema["required"] = list(properties.keys())

            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": schema,
                    },
                }
            )

        return tools


