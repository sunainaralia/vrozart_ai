import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from fastapi import FastAPI
from app.models import user, workspace, workspace_user, message, chat 
from app.api import auth,chat,root,workspace,org_hierarchy
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from app.core.db import Base, engine

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()
Base.metadata.create_all(bind=engine)
app.include_router(root.router)
app.include_router(auth.router, prefix="/auth")
app.include_router(chat.router, prefix="/chat")
app.include_router(workspace.router, prefix="/workspace")
app.include_router(org_hierarchy.router, prefix="/org")
