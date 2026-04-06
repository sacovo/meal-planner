from datetime import datetime
from uuid import UUID

from ninja import ModelSchema, Schema

from meals.models import ShoppingListItem

from .ingredients import IngredientSchema


class ShoppingListItemSchema(ModelSchema):
    ingredient: IngredientSchema | None = None
    source_meals_text: list[str] = []

    class Meta:
        model = ShoppingListItem
        fields = [
            "id",
            "shopping_list",
            "ingredient",
            "custom_name",
            "amount",
            "unit",
            "category",
            "is_checked",
        ]


class ShoppingListGenerateRequestSchema(Schema):
    meal_ids: list[UUID]


class ShoppingListOverviewSchema(Schema):
    id: UUID
    camp_id: UUID
    shared_token: UUID
    created_at: datetime
    included_meals: list[str]


class ShoppingListSchema(Schema):
    id: UUID
    camp_id: UUID
    shared_token: UUID
    items: list[ShoppingListItemSchema]


class ShoppingListManualItemSchema(Schema):
    ingredient_id: UUID
    amount: float
    unit: str
