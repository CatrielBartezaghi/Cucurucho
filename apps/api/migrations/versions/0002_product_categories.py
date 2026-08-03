"""Agrega categorías obligatorias a los productos."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("normalized_name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("normalized_name", name="uq_categories_normalized_name"),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO categories (id, name, normalized_name, created_at, updated_at)
            VALUES
              ('00000000-0000-0000-0000-000000000001', 'Helado', 'helado',
               CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
              ('00000000-0000-0000-0000-000000000002', 'Envasado', 'envasado',
               CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
              ('00000000-0000-0000-0000-000000000003', 'Otros', 'otros',
               CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
        )
    )
    op.add_column(
        "products",
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.execute(
        "UPDATE products "
        "SET category_id = '00000000-0000-0000-0000-000000000001'::uuid"
    )
    op.alter_column("products", "category_id", nullable=False)
    op.create_foreign_key(
        "fk_products_category_id_categories",
        "products",
        "categories",
        ["category_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_products_category_id", "products", ["category_id"])


def downgrade() -> None:
    op.drop_index("ix_products_category_id", table_name="products")
    op.drop_constraint(
        "fk_products_category_id_categories", "products", type_="foreignkey"
    )
    op.drop_column("products", "category_id")
    op.drop_table("categories")
