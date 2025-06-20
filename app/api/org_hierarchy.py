from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.db import get_db
from app.models.organization import Organization
from app.models.department import Department
from app.models.team import Team
from app.models.user import User
from app.models.user_organization import UserOrganization
from app.models.user_department import UserDepartment
from app.models.user_team import UserTeam
from app.utils.auth_utils import get_current_user
from pydantic import BaseModel

router = APIRouter()

# --- Schemas ---
class OrgCreate(BaseModel):
    name: str

class DeptCreate(BaseModel):
    name: str
    organization_id: UUID

class TeamCreate(BaseModel):
    name: str
    department_id: UUID

class UserAdd(BaseModel):
    user_id: UUID
    role: str = "member"

class RoleChange(BaseModel):
    user_id: UUID
    role: str

# --- Permission Checkers ---
def require_org_role(role: str):
    def checker(user=Depends(get_current_user), org_id: UUID = None, db: Session = Depends(get_db)):
        assoc = db.query(UserOrganization).filter_by(user_id=user.id, organization_id=org_id).first()
        if not assoc or (role and assoc.role != role):
            raise HTTPException(status_code=403, detail=f"Requires {role} role in organization")
        return True
    return checker

def require_dept_role(role: str):
    def checker(user=Depends(get_current_user), dept_id: UUID = None, db: Session = Depends(get_db)):
        assoc = db.query(UserDepartment).filter_by(user_id=user.id, department_id=dept_id).first()
        if not assoc or (role and assoc.role != role):
            raise HTTPException(status_code=403, detail=f"Requires {role} role in department")
        return True
    return checker

def require_team_role(role: str):
    def checker(user=Depends(get_current_user), team_id: UUID = None, db: Session = Depends(get_db)):
        assoc = db.query(UserTeam).filter_by(user_id=user.id, team_id=team_id).first()
        if not assoc or (role and assoc.role != role):
            raise HTTPException(status_code=403, detail=f"Requires {role} role in team")
        return True
    return checker

# --- Organization Endpoints ---
@router.post("/organization/create")
def create_organization(payload: OrgCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    org = Organization(name=payload.name)
    db.add(org)
    db.commit()
    db.refresh(org)
    # Add creator as admin
    assoc = UserOrganization(user_id=user.id, organization_id=org.id, role="admin")
    db.add(assoc)
    db.commit()
    return {"id": org.id, "name": org.name}

@router.get("/organization/list")
def list_organizations(user=Depends(get_current_user), db: Session = Depends(get_db)):
    orgs = db.query(Organization).join(UserOrganization).filter(UserOrganization.user_id == user.id).all()
    return [{"id": o.id, "name": o.name} for o in orgs]

@router.post("/organization/{org_id}/add-user")
def add_user_to_org(org_id: UUID, payload: UserAdd, user=Depends(get_current_user), db: Session = Depends(get_db), perm=Depends(require_org_role("admin"))):
    # Only admin can add
    assoc = db.query(UserOrganization).filter_by(user_id=payload.user_id, organization_id=org_id).first()
    if assoc:
        raise HTTPException(status_code=400, detail="User already in organization")
    assoc = UserOrganization(user_id=payload.user_id, organization_id=org_id, role=payload.role)
    db.add(assoc)
    db.commit()
    return {"status": "added"}

@router.post("/organization/{org_id}/change-role")
def change_org_role(org_id: UUID, payload: RoleChange, user=Depends(get_current_user), db: Session = Depends(get_db), perm=Depends(require_org_role("admin"))):
    assoc = db.query(UserOrganization).filter_by(user_id=payload.user_id, organization_id=org_id).first()
    if not assoc:
        raise HTTPException(status_code=404, detail="User not in organization")
    assoc.role = payload.role
    db.commit()
    return {"status": "role updated"}

@router.get("/organization/{org_id}/members")
def list_org_members(org_id: UUID, user=Depends(get_current_user), db: Session = Depends(get_db), perm=Depends(require_org_role("admin"))):
    assocs = db.query(UserOrganization).filter_by(organization_id=org_id).all()
    return [{"user_id": a.user_id, "role": a.role} for a in assocs]

# --- Department Endpoints ---
@router.post("/department/create")
def create_department(payload: DeptCreate, user=Depends(get_current_user), db: Session = Depends(get_db), perm=Depends(require_org_role("admin"))):
    dept = Department(name=payload.name, organization_id=payload.organization_id)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return {"id": dept.id, "name": dept.name}

@router.get("/department/list/{org_id}")
def list_departments(org_id: UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    depts = db.query(Department).filter_by(organization_id=org_id).all()
    return [{"id": d.id, "name": d.name} for d in depts]

@router.post("/department/{dept_id}/add-user")
def add_user_to_dept(dept_id: UUID, payload: UserAdd, user=Depends(get_current_user), db: Session = Depends(get_db), perm=Depends(require_dept_role("admin"))):
    assoc = db.query(UserDepartment).filter_by(user_id=payload.user_id, department_id=dept_id).first()
    if assoc:
        raise HTTPException(status_code=400, detail="User already in department")
    assoc = UserDepartment(user_id=payload.user_id, department_id=dept_id, role=payload.role)
    db.add(assoc)
    db.commit()
    return {"status": "added"}

@router.post("/department/{dept_id}/change-role")
def change_dept_role(dept_id: UUID, payload: RoleChange, user=Depends(get_current_user), db: Session = Depends(get_db), perm=Depends(require_dept_role("admin"))):
    assoc = db.query(UserDepartment).filter_by(user_id=payload.user_id, department_id=dept_id).first()
    if not assoc:
        raise HTTPException(status_code=404, detail="User not in department")
    assoc.role = payload.role
    db.commit()
    return {"status": "role updated"}

@router.get("/department/{dept_id}/members")
def list_dept_members(dept_id: UUID, user=Depends(get_current_user), db: Session = Depends(get_db), perm=Depends(require_dept_role("admin"))):
    assocs = db.query(UserDepartment).filter_by(department_id=dept_id).all()
    return [{"user_id": a.user_id, "role": a.role} for a in assocs]

# --- Team Endpoints ---
@router.post("/team/create")
def create_team(payload: TeamCreate, user=Depends(get_current_user), db: Session = Depends(get_db), perm=Depends(require_dept_role("admin"))):
    team = Team(name=payload.name, department_id=payload.department_id)
    db.add(team)
    db.commit()
    db.refresh(team)
    return {"id": team.id, "name": team.name}

@router.get("/team/list/{dept_id}")
def list_teams(dept_id: UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    teams = db.query(Team).filter_by(department_id=dept_id).all()
    return [{"id": t.id, "name": t.name} for t in teams]

@router.post("/team/{team_id}/add-user")
def add_user_to_team(team_id: UUID, payload: UserAdd, user=Depends(get_current_user), db: Session = Depends(get_db), perm=Depends(require_team_role("admin"))):
    assoc = db.query(UserTeam).filter_by(user_id=payload.user_id, team_id=team_id).first()
    if assoc:
        raise HTTPException(status_code=400, detail="User already in team")
    assoc = UserTeam(user_id=payload.user_id, team_id=team_id, role=payload.role)
    db.add(assoc)
    db.commit()
    return {"status": "added"}

@router.post("/team/{team_id}/change-role")
def change_team_role(team_id: UUID, payload: RoleChange, user=Depends(get_current_user), db: Session = Depends(get_db), perm=Depends(require_team_role("admin"))):
    assoc = db.query(UserTeam).filter_by(user_id=payload.user_id, team_id=team_id).first()
    if not assoc:
        raise HTTPException(status_code=404, detail="User not in team")
    assoc.role = payload.role
    db.commit()
    return {"status": "role updated"}

@router.get("/team/{team_id}/members")
def list_team_members(team_id: UUID, user=Depends(get_current_user), db: Session = Depends(get_db), perm=Depends(require_team_role("admin"))):
    assocs = db.query(UserTeam).filter_by(team_id=team_id).all()
    return [{"user_id": a.user_id, "role": a.role} for a in assocs] 