from pydantic import BaseModel, Field



class AgentCreate(BaseModel):
    name: str
    description: str | None = None
    system_prompt: str | None = None
    model: str = "gpt-5.2"

class AgentResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    system_prompt: str | None = None
    model: str

    model_config = {
        "from_attributes": True,
    }

class AgentToolSelect(BaseModel):
    tool_ids: list[int]

class AgentToolResponse(BaseModel):
    id: int
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}

class AgentToolCallRequest(BaseModel):
    arguments : dict= {}

class AgentChatRequest(BaseModel):
    message: str

class AgentChatResponse(BaseModel):
    response: str