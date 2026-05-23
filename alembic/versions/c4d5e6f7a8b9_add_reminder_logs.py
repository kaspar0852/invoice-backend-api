"""add_reminder_logs

Revision ID: c4d5e6f7a8b9
Revises: a98614fcb7fe
Create Date: 2026-05-23 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, Sequence[str], None] = "a98614fcb7fe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reminder_logs",
        sa.Column("Id", sa.Uuid(), nullable=False),
        sa.Column("InvoiceId", sa.Uuid(), nullable=False),
        sa.Column("BusinessId", sa.Uuid(), nullable=False),
        sa.Column("RecipientEmail", sa.String(length=255), nullable=False),
        sa.Column("Channel", sa.String(length=50), nullable=False),
        sa.Column("SentAt", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("Status", sa.String(length=50), nullable=False),
        sa.Column("ErrorMessage", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["BusinessId"], ["businesses.Id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["InvoiceId"], ["invoices.Id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("Id"),
    )


def downgrade() -> None:
    op.drop_table("reminder_logs")
