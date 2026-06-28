"""Application status


Revision ID: 1d5921549e34
Revises: 6c028c70481e
Create Date: 2026-06-20 20:40:24.313756

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1d5921549e34'
down_revision: Union[str, Sequence[str], None] = '6c028c70481e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


application_status_enum = sa.Enum(
    'PENDING', 'ACEPTED', 'REJECTED',
    name='application_status'
)

def upgrade():

    application_status_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'application',
        sa.Column('status', application_status_enum, nullable=False)
    )

def downgrade():
    op.drop_column('application', 'status')

    application_status_enum.drop(op.get_bind(), checkfirst=True)