from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.src.modules.sku import SKU


class SKUService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_sku_by_uuid(self, uuid: str) -> SKU | None:
        result = await self.session.execute(select(SKU).where(SKU.uuid == uuid))
        sku: SKU | None = result.scalars().first()
        return sku

    async def save_sku(self, sku_data: dict[str, Any]) -> None:
        result = await self.session.execute(select(SKU).where(SKU.product_id == int(sku_data["offer_id"])))
        existing_sku: Optional[SKU] = result.scalar_one_or_none()

        if existing_sku is None:
            sku = SKU(
                uuid=sku_data["uuid"],
                marketplace_id=sku_data["marketplace_id"],
                product_id=int(sku_data["offer_id"]),
                title=sku_data["name"],
                description=sku_data["description"],
                brand=sku_data["vendor"],
                barcode=(int(sku_data["barcode"]) if sku_data["barcode"] and sku_data["barcode"].isdigit() else None),
                category_id=(
                    int(sku_data["category_id"])
                    if sku_data["category_id"] and sku_data["category_id"].isdigit()
                    else None
                ),
                category_lvl_1=sku_data["category_lvl_1"],
                category_lvl_2=sku_data["category_lvl_2"],
                category_lvl_3=sku_data["category_lvl_3"],
                category_remaining=sku_data["category_remaining"],
                features=sku_data["params"],
                price_after_discounts=(float(sku_data["price"]) if sku_data["price"] else None),
                first_image_url=sku_data["picture"],
                currency=sku_data["currency_id"],
                inserted_at=func.now(),
                updated_at=func.now(),
            )
            self.session.add(sku)
