from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models import ArchitectureCanvas, GeneratedArtifact, User

router = APIRouter(prefix="/api", tags=["persistence"])


class CanvasRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    graph: dict[str, Any]


class ArtifactRequest(BaseModel):
    format: str = Field(pattern=r"^(terraform|cloudformation)$")
    content: str = Field(min_length=1, max_length=1_000_000)
    canvas_id: UUID | None = None


@router.post("/canvases")
def save_canvas(request: CanvasRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    canvas = ArchitectureCanvas(user_id=user.id, name=request.name, graph=request.graph)
    db.add(canvas)
    db.commit()
    return {"id": str(canvas.id), "name": canvas.name}


@router.get("/canvases")
def list_canvases(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict[str, str]]:
    canvases = db.scalars(select(ArchitectureCanvas).where(ArchitectureCanvas.user_id == user.id).order_by(ArchitectureCanvas.updated_at.desc())).all()
    return [{"id": str(canvas.id), "name": canvas.name, "updated_at": canvas.updated_at.isoformat() if canvas.updated_at else ""} for canvas in canvases]


@router.post("/artifacts")
def save_artifact(request: ArtifactRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    if request.canvas_id and db.scalar(select(ArchitectureCanvas).where(ArchitectureCanvas.id == request.canvas_id, ArchitectureCanvas.user_id == user.id)) is None:
        raise HTTPException(status_code=404, detail="Canvas not found")
    artifact = GeneratedArtifact(user_id=user.id, canvas_id=request.canvas_id, format=request.format, content=request.content)
    db.add(artifact)
    db.commit()
    return {"id": str(artifact.id), "format": artifact.format}