from datetime import datetime

from pydantic import BaseModel, ConfigDict



class ConversationCreate(BaseModel):
    agent_id : int
    title : str | None = None

class ConversationResponse(BaseModel):
    id : int
    agent_id : int
    title : str | None = None
    created_at : datetime
    updated_at : datetime

    model_config = ConfigDict(from_attributes=True)

class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id : int
    conversation_id : int
    role : str
    content: str | None = None
    tool_name: str | None = None
    tool_call_id: str | None = None
    tool_arguments: str | None = None
    created_at : datetime

    model_config = ConfigDict(from_attributes=True)
