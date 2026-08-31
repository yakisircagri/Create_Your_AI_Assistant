from fastapi import FastAPI
from app.api.mcp import router as mcp_router
from app.api.agents import router as agents_router
from app.api.conversations import router as conversations_router
from fastapi.middleware.cors import CORSMiddleware
from app.api.users import router as users_router
from app.api.auth import router as auth_router

app = FastAPI(
    title = "Create Your AI Assistant",
    version = "0.1.0",
)

app.include_router(mcp_router)
app.include_router(agents_router)
app.include_router(conversations_router)
app.include_router(users_router)
app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {
        "status": "ok"
    }