import json
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Message
from app.schemas import ChatRequest, ChatResponse, ChatMetadata
from app.services.llm_service import llm_service

router = APIRouter(tags=["Chat"])

DEFAULT_SYSTEM_PROMPT = "You are a helpful, concise AI assistant."


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(
    request: ChatRequest,
    x_simulate_failure: Optional[str] = Header(None, alias="X-Simulate-Failure"),
    db: Session = Depends(get_db)
):
    """
    POST /chat
    Handles multi-turn AI conversations, key failover, response caching,
    token & latency tracking, and SQLite persistence.
    """
    # 1. Fetch existing session history (oldest first)
    prev_messages = (
        db.query(Message)
        .filter(Message.session_id == request.session_id)
        .order_by(Message.id.asc())
        .all()
    )

    # 2. Build full message list for LiteLLM
    system_prompt = request.system_prompt.strip() if request.system_prompt else DEFAULT_SYSTEM_PROMPT
    if not system_prompt:
        system_prompt = DEFAULT_SYSTEM_PROMPT

    llm_messages = [{"role": "system", "content": system_prompt}]
    for msg in prev_messages:
        llm_messages.append({"role": msg.role, "content": msg.content})
    llm_messages.append({"role": "user", "content": request.message})

    # 3. Execute completion with LiteLLM gateway (handles failover and cache)
    # If this raises HTTPException (e.g. 503), turn is NOT persisted
    llm_result = llm_service.execute_completion(
        messages=llm_messages,
        simulation_header=x_simulate_failure
    )

    reply_text = llm_result["reply"]
    metadata_dict = llm_result["metadata"]

    # 4. Atomically persist user and assistant messages in SQLite
    user_db_message = Message(
        session_id=request.session_id,
        role="user",
        content=request.message,
        message_metadata=None
    )

    assistant_db_message = Message(
        session_id=request.session_id,
        role="assistant",
        content=reply_text,
        message_metadata=json.dumps(metadata_dict)
    )

    try:
        db.add(user_db_message)
        db.add(assistant_db_message)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to persist chat messages: {str(e)}")

    return ChatResponse(
        session_id=request.session_id,
        reply=reply_text,
        metadata=ChatMetadata(**metadata_dict)
    )
