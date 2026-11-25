from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Index
from app.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    session_id = Column(String(128), nullable=False, index=True)
    role = Column(String(32), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    # metadata: JSON string for assistant messages only (or None)
    message_metadata = Column("metadata", Text, nullable=True)
    created_at = Column(
        String(64),
        nullable=False,
        default=lambda: datetime.now(timezone.utc).isoformat()
    )


# Index for session history queries ordered by id
Index("idx_messages_session_id_id", Message.session_id, Message.id)
