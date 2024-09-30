from typing import Any
from uuid import UUID

from sqlalchemy import ARRAY, JSON, TIMESTAMP, BigInteger, Double, Float, Index, Integer, Numeric, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.src import Base


class SKU(Base):
    __tablename__ = "sku"
    __table_args__ = (
        Index("sku_brand_index", "brand"),
        Index(
            "sku_marketplace_id_sku_id_uindex",
            "marketplace_id",
            "product_id",
            unique=True,
        ),
        Index("sku_uuid_uindex", "uuid", unique=True),
        {"schema": "public"},
    )

    uuid: Mapped[str] = mapped_column(PGUUID(as_uuid=True), primary_key=True, comment="id товара в нашей бд")
    marketplace_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="id маркетплейса")
    product_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="id товара в маркетплейсе")
    title: Mapped[str | None] = mapped_column(Text, nullable=True, comment="название товара")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="описание товара")
    brand: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    seller_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    seller_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    category_lvl_1: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Первая часть категории товара")
    category_lvl_2: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Вторая часть категории товара")
    category_lvl_3: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Третья часть категории товара")
    category_remaining: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Остаток категории товара")
    features: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True, comment="Характеристики товара")
    rating_count: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="Кол-во отзывов о товаре")
    rating_value: Mapped[float | None] = mapped_column(Double, nullable=True, comment="Рейтинг товара (0-5)")
    price_before_discounts: Mapped[float | None] = mapped_column(Float, nullable=True)
    discount: Mapped[float | None] = mapped_column(Double, nullable=True)
    price_after_discounts: Mapped[float | None] = mapped_column(Float, nullable=True)
    bonuses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sales: Mapped[int | None] = mapped_column(Integer, nullable=True)
    inserted_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    currency: Mapped[str | None] = mapped_column(Text, nullable=True)
    barcode: Mapped[int | None] = mapped_column(Numeric(precision=60, scale=0), nullable=True, comment="Штрихкод")
    similar_sku: Mapped[list[UUID] | None] = mapped_column(ARRAY(PGUUID(as_uuid=True)), nullable=True)
