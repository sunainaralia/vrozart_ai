from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.db import get_db
from app.models.workspace import Workspace
from app.models.user import User
from app.models.workspace_user import WorkspaceUser
from app.schemas.workspace import WorkspaceCreate, WorkspaceOut
from app.utils.auth_utils import get_current_user

router = APIRouter()

@router.post("/workspace/create", response_model=WorkspaceOut)
def create_workspace(
    payload: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Just create the workspace
    workspace = Workspace(name=payload.name)
    db.add(workspace)
    db.commit()
    db.refresh(workspace)

    # Add current user to workspace via association table
    link = WorkspaceUser(user_id=current_user.id, workspace_id=workspace.id)
    db.add(link)
    db.commit()

    return workspace

@router.post("/workspace/join")
def join_workspace(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workspace = db.query(Workspace).filter_by(id=workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Check if already joined
    exists = db.query(WorkspaceUser).filter_by(
        user_id=current_user.id,
        workspace_id=workspace.id
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Already joined")

    db.add(WorkspaceUser(user_id=current_user.id, workspace_id=workspace.id))
    db.commit()

    return {"message": "Joined workspace successfully"}
