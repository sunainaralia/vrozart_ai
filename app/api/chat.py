from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.utils.auth_utils import get_current_user
from app.services.vector_store import search_context, embed_and_store, delete_document_vectors
from app.services.llm_router import stream_chat_response, get_full_chat_response  
from app.services.redis_cache import store_chat_memory, get_chat_memory
from app.services.document_parser import extract_text_from_file
from app.models.message import Message
from app.models.chat import Chat
from app.models.document import Document
from app.models.workspace import Workspace
from app.core.db import get_db
from sqlalchemy.orm import Session
import uuid
import os
from datetime import datetime

router = APIRouter()

class ChatRequest(BaseModel):
    chat_id: uuid.UUID
    message: str
    model: str 

class CreateChatRequest(BaseModel):
    workspace_id: uuid.UUID
    title: str = "New Chat"
    model: str = "gpt-4"

@router.post("/create")
def create_chat(
    request: CreateChatRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify workspace exists and user has access
    workspace = db.query(Workspace).filter_by(id=request.workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Create new chat
    chat = Chat(
        user_id=user.id,
        workspace_id=request.workspace_id,
        title=request.title,
        model=request.model
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    
    return {
        "chat_id": str(chat.id),
        "title": chat.title,
        "model": chat.model,
        "created_at": chat.created_at
    }

@router.get("/list/{workspace_id}")
def list_chats(
    workspace_id: uuid.UUID,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chats = db.query(Chat).filter_by(
        workspace_id=workspace_id,
        user_id=user.id
    ).order_by(Chat.created_at.desc()).all()
    
    return [
        {
            "chat_id": str(chat.id),
            "title": chat.title,
            "model": chat.model,
            "created_at": chat.created_at
        }
        for chat in chats
    ]

@router.post("/chat")
async def chat_stream(
    body: ChatRequest,
    request: Request,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify chat exists and belongs to user
    chat = db.query(Chat).filter_by(id=body.chat_id, user_id=user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    memory = get_chat_memory(body.chat_id)
    context_docs = search_context(body.message, body.chat_id)

    # Combine memory and docs as prompt
    memory_text = ""
    if memory:
        memory_text = "\n".join([f"User: {m['msg']}\nAssistant: {m['res']}" for m in memory[-5:]]) + "\n\n"
    
    context_text = f"Context from documents:\n{context_docs}\n\n" if context_docs else ""
    
    prompt = f"{memory_text}{context_text}User: {body.message}"

    async def event_stream():
        # Stream chunks to frontend
        async for chunk in stream_chat_response(body.model, prompt):
            yield chunk

        # Fetch full response for storage
        final_response = await get_full_chat_response(body.model, prompt)

        # Save to Redis and DB
        store_chat_memory(body.chat_id, body.message, final_response)
        db.add(Message(
            user_id=user.id,
            chat_id=body.chat_id,
            content=body.message,
            response=final_response
        ))
        db.commit()

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@router.post("/upload-document")
async def upload_document_in_chat(
    chat_id: uuid.UUID,
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify chat exists and belongs to user
    chat = db.query(Chat).filter_by(id=chat_id, user_id=user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    try:
        # Ensure upload dir exists
        upload_dir = f"uploads/chat_{chat_id}"
        os.makedirs(upload_dir, exist_ok=True)

        # Save file locally
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Extract text
        text = await extract_text_from_file(file)

        # Store embeddings in Qdrant
        await embed_and_store(text, chat_id, file.filename)

        # Save metadata in PostgreSQL
        doc = Document(
            chat_id=chat_id,
            name=file.filename,
            path=file_path,
            uploaded_at=datetime.utcnow()
        )
        db.add(doc)
        db.commit()

        return {"status": "success", "message": f"File {file.filename} uploaded to chat and embedded."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{chat_id}")
def list_chat_documents(
    chat_id: uuid.UUID,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify chat exists and belongs to user
    chat = db.query(Chat).filter_by(id=chat_id, user_id=user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    docs = db.query(Document).filter_by(chat_id=chat_id).all()
    return [
        {"id": str(doc.id), "name": doc.name, "uploaded_at": doc.uploaded_at}
        for doc in docs
    ]

@router.delete("/documents/{doc_id}")
async def delete_chat_document(
    doc_id: uuid.UUID,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Verify chat belongs to user
    chat = db.query(Chat).filter_by(id=doc.chat_id, user_id=user.id).first()
    if not chat:
        raise HTTPException(status_code=403, detail="Access denied")

    # Delete from vector store
    delete_document_vectors(doc.chat_id, doc.name)

    # Delete file
    if os.path.exists(doc.path):
        os.remove(doc.path)

    # Delete from database
    db.delete(doc)
    db.commit()
    
    return {"status": "deleted", "message": f"{doc.name} removed from chat."}

@router.get("/history/{chat_id}")
def get_chat_history(
    chat_id: uuid.UUID, 
    user=Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # Verify chat exists and belongs to user
    chat = db.query(Chat).filter_by(id=chat_id, user_id=user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    messages = db.query(Message).filter_by(chat_id=chat_id).order_by(Message.created_at.asc()).all()
    return [
        {
            "user_id": m.user_id,
            "message": m.content,
            "response": m.response,
            "created_at": m.created_at
        }
        for m in messages
    ]
