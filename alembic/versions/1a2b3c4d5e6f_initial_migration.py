"""initial migration

Revision ID: 1a2b3c4d5e6f
Revises: 
Create Date: 2026-05-21 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('Id', sa.Uuid(), nullable=False),
        sa.Column('FullName', sa.String(length=255), nullable=False),
        sa.Column('Email', sa.String(length=255), nullable=False),
        sa.Column('Phone', sa.String(length=50), nullable=True),
        sa.Column('PasswordHash', sa.String(length=255), nullable=False),
        sa.Column('IsActive', sa.Boolean(), nullable=False),
        sa.Column('CreatedAt', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('Id')
    )
    op.create_index(op.f('ix_users_Email'), 'users', ['Email'], unique=True)
    op.create_index(op.f('ix_users_Id'), 'users', ['Id'], unique=False)

    # 2. businesses table
    op.create_table(
        'businesses',
        sa.Column('Id', sa.Uuid(), nullable=False),
        sa.Column('Name', sa.String(length=255), nullable=False),
        sa.Column('VatNumber', sa.String(length=100), nullable=True),
        sa.Column('PanNumber', sa.String(length=100), nullable=True),
        sa.Column('Address', sa.String(length=500), nullable=True),
        sa.Column('Phone', sa.String(length=50), nullable=True),
        sa.Column('LogoUrl', sa.String(length=500), nullable=True),
        sa.Column('CreatedAt', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('Id')
    )
    op.create_index(op.f('ix_businesses_Id'), 'businesses', ['Id'], unique=False)

    # 3. user_businesses table
    op.create_table(
        'user_businesses',
        sa.Column('Id', sa.Uuid(), nullable=False),
        sa.Column('UserId', sa.Uuid(), nullable=False),
        sa.Column('BusinessId', sa.Uuid(), nullable=False),
        sa.Column('Role', sa.Enum('Owner', 'Admin', 'Staff', 'Accountant', name='user_role_enum'), nullable=False),
        sa.Column('CreatedAt', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['BusinessId'], ['businesses.Id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['UserId'], ['users.Id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('Id')
    )
    op.create_index(op.f('ix_user_businesses_Id'), 'user_businesses', ['Id'], unique=False)

    # 4. customers table
    op.create_table(
        'customers',
        sa.Column('Id', sa.Uuid(), nullable=False),
        sa.Column('BusinessId', sa.Uuid(), nullable=False),
        sa.Column('Name', sa.String(length=255), nullable=False),
        sa.Column('Phone', sa.String(length=50), nullable=True),
        sa.Column('Email', sa.String(length=255), nullable=True),
        sa.Column('Address', sa.String(length=500), nullable=True),
        sa.Column('VatNumber', sa.String(length=100), nullable=True),
        sa.Column('CreatedAt', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['BusinessId'], ['businesses.Id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('Id')
    )
    op.create_index(op.f('ix_customers_Id'), 'customers', ['Id'], unique=False)

    # 5. invoices table
    op.create_table(
        'invoices',
        sa.Column('Id', sa.Uuid(), nullable=False),
        sa.Column('BusinessId', sa.Uuid(), nullable=False),
        sa.Column('CustomerId', sa.Uuid(), nullable=False),
        sa.Column('InvoiceNumber', sa.String(length=100), nullable=False),
        sa.Column('Status', sa.Enum('Draft', 'Sent', 'Paid', 'Partial', 'Overdue', 'Cancelled', name='invoice_status_enum'), nullable=False),
        sa.Column('Subtotal', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('VatAmount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('DiscountAmount', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('TotalAmount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('DueDate', sa.Date(), nullable=True),
        sa.Column('Notes', sa.String(length=1000), nullable=True),
        sa.Column('CreatedBy', sa.Uuid(), nullable=True),
        sa.Column('CreatedAt', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['BusinessId'], ['businesses.Id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['CreatedBy'], ['users.Id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['CustomerId'], ['customers.Id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('Id')
    )
    op.create_index(op.f('ix_invoices_InvoiceNumber'), 'invoices', ['InvoiceNumber'], unique=True)
    op.create_index(op.f('ix_invoices_Id'), 'invoices', ['Id'], unique=False)

    # 6. invoice_items table
    op.create_table(
        'invoice_items',
        sa.Column('Id', sa.Uuid(), nullable=False),
        sa.Column('InvoiceId', sa.Uuid(), nullable=False),
        sa.Column('ProductName', sa.String(length=255), nullable=False),
        sa.Column('Quantity', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('UnitPrice', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('VatRate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('Discount', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('LineTotal', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['InvoiceId'], ['invoices.Id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('Id')
    )
    op.create_index(op.f('ix_invoice_items_Id'), 'invoice_items', ['Id'], unique=False)

    # 7. payments table
    op.create_table(
        'payments',
        sa.Column('Id', sa.Uuid(), nullable=False),
        sa.Column('InvoiceId', sa.Uuid(), nullable=False),
        sa.Column('BusinessId', sa.Uuid(), nullable=False),
        sa.Column('Amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('PaymentDate', sa.Date(), nullable=False),
        sa.Column('PaymentMethod', sa.Enum('Cash', 'Bank', 'Mobile', 'Cheque', name='payment_method_enum'), nullable=False),
        sa.Column('Reference', sa.String(length=255), nullable=True),
        sa.Column('CreatedAt', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['BusinessId'], ['businesses.Id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['InvoiceId'], ['invoices.Id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('Id')
    )
    op.create_index(op.f('ix_payments_Id'), 'payments', ['Id'], unique=False)


def downgrade() -> None:
    op.drop_table('payments')
    op.drop_table('invoice_items')
    op.drop_table('invoices')
    op.drop_table('customers')
    op.drop_table('user_businesses')
    op.drop_table('businesses')
    op.drop_table('users')
