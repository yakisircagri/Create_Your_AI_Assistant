from pydantic import BaseModel, Field

class MCPServerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=250)
    url: str = Field(min_length=1, max_length=2050)
    description: str | None = None

class MCPServerResponse(BaseModel):
    id: int
    name: str
    url: str
    description: str | None = None
    model_config = {
        "from_attributes" : True,
    }

