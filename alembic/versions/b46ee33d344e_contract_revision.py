"""Contract Revision

Revision ID: b46ee33d344e
Revises: 62fec24eb912
Create Date: 2026-06-27 14:15:01.932576

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b46ee33d344e'
down_revision: Union[str, Sequence[str], None] = '62fec24eb912'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade() -> None:
    op.add_column('contract', sa.Column('job_id', sa.String(), nullable=False))
    op.create_foreign_key(None, 'contract', 'job', ['job_id'], ['job_id'])

  
    new_enum = postgresql.ENUM('PENDING_PAYMENT', 'GUARANTEED', 'COMPLETED', 'REFUNDED', 'FAILED', 'DISPUTED', name='contract_types')
    new_enum.create(op.get_bind(), checkfirst=True)


    op.execute("""
        ALTER TABLE contract 
        ALTER COLUMN status TYPE contract_types 
        USING (
            CASE status::text
                WHEN 'REFOUNDED' THEN 'REFUNDED'::contract_types
                ELSE status::text::contract_types
            END
        )
    """)


    old_enum = postgresql.ENUM('PENDING_PAYMENT', 'GUARANTEED', 'COMPLETED', 'REFOUNDED', 'FAILED', 'DISPUTED', name='contract types')
    old_enum.drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:

    old_enum = postgresql.ENUM('PENDING_PAYMENT', 'GUARANTEED', 'COMPLETED', 'REFOUNDED', 'FAILED', 'DISPUTED', name='contract types')
    old_enum.create(op.get_bind(), checkfirst=True)

    op.execute("""
        ALTER TABLE contract 
        ALTER COLUMN status TYPE "contract types" 
        USING (
            CASE status::text
                WHEN 'REFUNDED' THEN 'REFOUNDED'::"contract types"
                ELSE status::text::"contract types"
            END
        )
    """)
    new_enum = postgresql.ENUM('PENDING_PAYMENT', 'GUARANTEED', 'COMPLETED', 'REFUNDED', 'FAILED', 'DISPUTED', name='contract_types')
    new_enum.drop(op.get_bind(), checkfirst=True)

    op.drop_constraint(None, 'contract', type_='foreignkey')
    op.drop_column('contract', 'job_id')

