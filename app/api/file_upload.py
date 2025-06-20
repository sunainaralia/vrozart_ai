from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.services.document_parser import extract_text_from_file
from app.services.vector_store import embed_and_store, delete_document_vectors
from app.utils.auth_utils import get_current_user
from app.core.db import get_db
from app.models.document import Document
from sqlalchemy.orm import Session
import uuid
import os
from datetime import datetime

router = APIRouter()
UPLOAD_DIR = "uploads"

@router.post("/upload")
async def upload_document(
    workspace_id: uuid.UUID,
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Ensure upload dir exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # Save file locally
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Extract text
        text = await extract_text_from_file(file)

        # Store embeddings in Qdrant
        await embed_and_store(text, workspace_id, file.filename)

        # Save metadata in PostgreSQL
        doc = Document(
            workspace_id=workspace_id,
            name=file.filename,
            path=file_path,
            uploaded_at=datetime.utcnow()
        )
        db.add(doc)
        db.commit()

        return {"status": "success", "message": f"File {file.filename} embedded & saved."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents")
async def list_documents(
    workspace_id: uuid.UUID,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    docs = db.query(Document).filter(Document.workspace_id == workspace_id).all()
    return [
        {"id": str(doc.id), "name": doc.name, "uploaded_at": doc.uploaded_at}
        for doc in docs
    ]


@router.get("/documents/{workspace_id}")
def list_documents(workspace_id: uuid.UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    docs = db.query(Document).filter_by(workspace_id=workspace_id).all()
    return [{"id": d.id, "name": d.name, "uploaded_at": d.uploaded_at} for d in docs]


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: uuid.UUID,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    delete_document_vectors(doc.workspace_id, doc.name)

    db.delete(doc)
    db.commit()
    return {"status": "deleted", "message": f"{doc.name} removed."}