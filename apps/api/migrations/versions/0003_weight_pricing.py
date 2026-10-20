"""Agrega Productos por kilo sin cambiar los detalles históricos existentes."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("pricing_type", sa.String(length=10), nullable=False, server_default="unit"),
    )
    op.create_check_constraint(
        "ck_products_pricing_type", "products", "pricing_type IN ('unit','weight')"
    )
    op.add_column(
        "sale_details",
        sa.Column("pricing_type", sa.String(length=10), nullable=False, server_default="unit"),
    )
    op.add_column("sale_details", sa.Column("weight_kg", sa.Numeric(12, 3), nullable=True))
    op.add_column("sale_details", sa.Column("entry_method", sa.String(length=10), nullable=True))
    op.add_column("sale_details", sa.Column("line_total", sa.Numeric(14, 2), nullable=True))
    op.execute("UPDATE sale_details SET line_total = unit_price * quantity")
    op.alter_column("sale_details", "line_total", nullable=False)
    op.create_check_constraint(
        "ck_sale_details_pricing_type", "sale_details",
        "pricing_type IN ('unit','weight')",
    )
    op.create_check_constraint(
        "ck_sale_details_positive_line_total", "sale_details", "line_total > 0"
    )
    op.create_check_constraint(
        "ck_sale_details_positive_weight", "sale_details",
        "weight_kg IS NULL OR weight_kg > 0",
    )
    op.create_check_constraint(
        "ck_sale_details_pricing_consistency", "sale_details",
        "(pricing_type = 'unit' AND weight_kg IS NULL AND entry_method IS NULL) OR "
        "(pricing_type = 'weight' AND weight_kg IS NOT NULL AND "
        "entry_method IN ('weight','amount') AND quantity = 1)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_sale_details_pricing_consistency", "sale_details", type_="check")
    op.drop_constraint("ck_sale_details_positive_weight", "sale_details", type_="check")
    op.drop_constraint("ck_sale_details_positive_line_total", "sale_details", type_="check")
    op.drop_constraint("ck_sale_details_pricing_type", "sale_details", type_="check")
    op.drop_column("sale_details", "line_total")
    op.drop_column("sale_details", "entry_method")
    op.drop_column("sale_details", "weight_kg")
    op.drop_column("sale_details", "pricing_type")
    op.drop_constraint("ck_products_pricing_type", "products", type_="check")
    op.drop_column("products", "pricing_type")
