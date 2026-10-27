"""Insumos, compras, recetas y costo histórico por detalle de venta."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "supplies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("normalized_name", sa.String(150), nullable=False),
        sa.Column("unit", sa.String(10), nullable=False),
        sa.Column("current_unit_cost", sa.Numeric(14, 4), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("normalized_name", name="uq_supplies_normalized_name"),
        sa.CheckConstraint("unit IN ('kg','unit')", name="ck_supplies_unit"),
        sa.CheckConstraint(
            "current_unit_cost IS NULL OR current_unit_cost >= 0", name="ck_supplies_cost"
        ),
    )
    op.create_table(
        "supply_purchases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("supply_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("supplies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("total_cost", sa.Numeric(14, 2), nullable=False),
        sa.Column("unit_cost", sa.Numeric(14, 4), nullable=False),
        sa.Column("purchased_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_supply_purchases_quantity"),
        sa.CheckConstraint("total_cost >= 0", name="ck_supply_purchases_total_cost"),
        sa.CheckConstraint("unit_cost >= 0", name="ck_supply_purchases_unit_cost"),
    )
    op.create_index("ix_supply_purchases_supply_id", "supply_purchases", ["supply_id"])
    op.create_table(
        "product_supplies",
        sa.Column("product_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("supply_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("supplies.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("mode", sa.String(10), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_product_supplies_quantity"),
        sa.CheckConstraint("mode IN ('variable','fixed')", name="ck_product_supplies_mode"),
    )
    op.add_column("sale_details", sa.Column("cost_total", sa.Numeric(14, 2), nullable=True))
    op.create_check_constraint(
        "ck_sale_details_nonnegative_cost", "sale_details",
        "cost_total IS NULL OR cost_total >= 0",
    )


def downgrade() -> None:
    op.drop_constraint("ck_sale_details_nonnegative_cost", "sale_details", type_="check")
    op.drop_column("sale_details", "cost_total")
    op.drop_table("product_supplies")
    op.drop_index("ix_supply_purchases_supply_id", table_name="supply_purchases")
    op.drop_table("supply_purchases")
    op.drop_table("supplies")
