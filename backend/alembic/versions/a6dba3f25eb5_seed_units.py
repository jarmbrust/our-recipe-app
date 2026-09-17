"""seed units

Revision ID: a6dba3f25eb5
Revises: 2623858c829f
Create Date: 2026-09-14 10:21:43.214219

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a6dba3f25eb5'
down_revision: Union[str, Sequence[str], None] = '2623858c829f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    units_table = sa.table(
        "units",
        sa.column("name", sa.String),
        sa.column("abbreviation", sa.String),
        sa.column("system", sa.String),
    )
    op.bulk_insert(
        units_table,
        [
            {"name": "cup", "abbreviation": "c", "system": "imperial"},
            {"name": "tablespoon", "abbreviation": "tbsp", "system": "imperial"},
            {"name": "teaspoon", "abbreviation": "tsp", "system": "imperial"},
            {"name": "ounce", "abbreviation": "oz", "system": "imperial"},
            {"name": "pound", "abbreviation": "lb", "system": "imperial"},
            {"name": "gram", "abbreviation": "g", "system": "metric"},
            {"name": "milliliter", "abbreviation": "ml", "system": "metric"},
            {"name": "liter", "abbreviation": "l", "system": "metric"},
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "DELETE FROM units WHERE name IN ('cup', 'tablespoon', 'teaspoon', 'ounce', 'pound', 'gram', 'milliliter', 'liter')"
    )
