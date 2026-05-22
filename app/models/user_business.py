import enum
import uuid
from datetime import datetime
from sqlalchemy import DateTime, func, Uuid, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class UserRole(str, enum.Enum):
    OWNER = "Owner"
    ADMIN = "Admin"
    STAFF = "Staff"
    ACCOUNTANT = "Accountant"


USER_ROLE_ENUM = Enum(
    UserRole,
    name="user_role_enum",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)


class UserBusiness(Base):
    __tablename__ = "user_businesses"

    id: Mapped[uuid.UUID] = mapped_column(
        "Id",
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        "UserId",
        Uuid(as_uuid=True),
        ForeignKey("users.Id", ondelete="CASCADE"),
        nullable=False,
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        "BusinessId",
        Uuid(as_uuid=True),
        ForeignKey("businesses.Id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        "Role",
        USER_ROLE_ENUM,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        "CreatedAt",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
