"""add size to results

Revision ID: a1f6907cdeb5
Revises: f84c5c673cde
Create Date: 2025-05-13 01:02:11.156310

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from file_storage.main.config import DB_SCHEMA  # noqa: F401

# revision identifiers, used by Alembic.
revision: str = "a1f6907cdeb5"
down_revision: Union[str, None] = "f84c5c673cde"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("results", sa.Column("size", sa.Integer(), nullable=False), schema="files_schema")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("results", "size", schema="files_schema")
    # ### end Alembic commands ###
