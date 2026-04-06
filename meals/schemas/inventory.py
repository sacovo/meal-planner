from uuid import UUID

from ninja import Schema


class InventoryStatusSchema(Schema):
    ingredient_id: UUID
    ingredient_name: str
    category: str
    unit: str
    quantity_bought: float
    quantity_required: float
    balance: float
