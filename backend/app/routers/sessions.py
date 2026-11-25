import json
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Message
from app.schemas import SessionHistoryResponse, StoredMessage

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("/{session_id}/messages", response_model=SessionHistoryResponse)
def get_session_messages(
    session_id: str = Path(..., min_length=1, max_length=128),
    db: Session = Depends(get_db)
):
    """
    Returns the stored history of one session from SQLite, oldest first,
    without the system prompt.
    Returns 404 if the session has no stored messages.
    """
    db_messages = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.id.asc())
        .all()
    )

    if not db_messages:
        raise HTTPException(status_code=404, detail="session not found")

    messages_out = []
    for msg in db_messages:
        meta_dict = None
        if msg.role == "assistant" and msg.message_metadata:
            try:
                meta_dict = json.loads(msg.message_metadata)
            except Exception:
                meta_dict = None

        messages_out.append(
            StoredMessage(
                role=msg.role,
                content=msg.content,
                metadata=meta_dict
            )
        )

    return SessionHistoryResponse(
        session_id=session_id,
        messages=messages_out
    )
