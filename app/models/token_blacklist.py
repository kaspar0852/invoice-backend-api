from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    
    token: Mapped[str] = mapped_column(
        "Token", 
        String(500), 
        primary_key=True, 
        index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        "ExpiresAt", 
        DateTime(timezone=True), 
        nullable=False
    )
