"""add_result_type_format

Revision ID: 29b866eaa4ea
Revises: a1f6907cdeb5
Create Date: 2025-05-16 20:32:12.925912

"""

from typing import Sequence, Union

from alembic import op

from file_storage.main.config import DB_SCHEMA  # noqa: F401

# revision identifiers, used by Alembic.
revision: str = "29b866eaa4ea"
down_revision: Union[str, None] = "a1f6907cdeb5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new value to the existing PostgreSQL ENUM type
    op.execute("ALTER TYPE files_schema.result_type_enum ADD VALUE IF NOT EXISTS 'CONVERT'")


def downgrade() -> None:
    # Downgrade is not straightforward for removing enum values in PostgreSQL
    # You must recreate the enum without the removed value

    # Rename the existing enum type
    op.execute("ALTER TYPE result_type_enum RENAME TO result_type_enum_old")

    # Recreate the enum without the 'FORMAT' value
    op.execute("""
        CREATE TYPE files_schema.result_type_enum AS ENUM (
            'FORMAT'
        )
    """)

    # Alter all columns using the old enum to use the new one
    op.execute("""
        ALTER TABLE results
        ALTER COLUMN type
        TYPE files_schema.result_type_enum
        USING type::text::result_type_enum
    """)

    # Drop the old enum
    op.execute("DROP TYPE files_schema.result_type_enum_old")
