"""0001 extensions

Revision ID: 6030d4c779ae
Revises: 
Create Date: 2025-11-10 19:09:15.999947

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6030d4c779ae'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto;')
    op.execute('CREATE EXTENSION IF NOT EXISTS citext;')


def downgrade() -> None:
    op.execute('DROP EXTENSION IF EXISTS citext;')
    op.execute('DROP EXTENSION IF EXISTS pgcrypto;')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp";')
