from datetime import datetime
from ninja import ModelSchema, Schema
from typing import List, Optional
from datetime import date, datetime
from uuid import UUID

from .models import (
    Camp,
    Ingredient,
    IngredientUnitConversion,
    Recipe,
    RecipeIngredient,
    CampMeal,
    GeneralCampItem,
    ShoppingList,
    ShoppingListItem,
    Inventory,
    DietaryPreference,
)

class DietaryPreferenceSchema(ModelSchema):
    class Meta:
        model = DietaryPreference
        fields = ["id", "name"]

class IngredientSchema(ModelSchema):
    class Meta:
        model = Ingredient
        fields = ["id", "name", "category", "base_unit"]

class IngredientCreateSchema(ModelSchema):
    class Meta:
        model = Ingredient
        fields = ["name", "category", "base_unit"]

class CampSchema(ModelSchema):
    owner_username: str = None
    collaborators: List[str] = []

    @staticmethod
    def resolve_owner_username(obj):
        return obj.owner.username

    @staticmethod
    def resolve_collaborators(obj):
        return [c.username for c in obj.collaborators.all()]

    class Meta:
        model = Camp
        fields = ["id", "name", "default_people_count", "start_date", "end_date", "notes"]

class CampCreateSchema(Schema):
    name: str
    default_people_count: int
    start_date: date
    end_date: date

class CampUpdateSchema(Schema):
    name: Optional[str] = None
    default_people_count: Optional[int] = None
    notes: Optional[str] = None

class CollaboratorInviteSchema(Schema):
    username: str

class CampMealSchema(ModelSchema):
    serves_preference: DietaryPreferenceSchema | None = None
    class Meta:
        model = CampMeal
        fields = ["id", "camp", "recipe", "meal_type", "date", "override_people_count", "leftovers_noted", "is_done"]

class CampMealCreateSchema(Schema):
    recipe_id: UUID
    meal_type: str
    date: date
    override_people_count: int = None
    serves_preference_id: int = None

class CampMealUpdateSchema(Schema):
    override_people_count: int | None = None
    serves_preference_id: int | None = None


class CampCreateSchema(ModelSchema):
    class Meta:
        model = Camp
        fields = ["name", "default_people_count", "start_date", "end_date"]

class RecipeSchema(ModelSchema):
    preferences: List[DietaryPreferenceSchema] = []
    class Meta:
        model = Recipe
        fields = ["id", "name", "description", "instructions", "owner", "tags", "default_portions"]

class RecipeCreateSchema(ModelSchema):
    preference_ids: List[int] = []
    class Meta:
        model = Recipe
        fields = ["name", "description", "instructions", "tags", "default_portions"]

class RecipeIngredientSchema(ModelSchema):
    ingredient: IngredientSchema
    class Meta:
        model = RecipeIngredient
        fields = ["id", "ingredient", "amount", "unit"]

class RecipeIngredientCreateOrMapSchema(Schema):
    ingredient_name: str
    amount: float
    unit: str

class RecipeIngredientUpdateSchema(Schema):
    amount: float
    unit: str

class RecipeUpdateSchema(Schema):
    name: str = None
    description: str = None
    instructions: str = None
    default_portions: int = None
    preference_ids: List[int] = None

class RecipeImportRequestSchema(Schema):
    raw_text: str

class GeneralCampItemSchema(ModelSchema):
    class Meta:
        model = GeneralCampItem
        fields = ["id", "camp", "name", "amount", "category"]

class GeneralCampItemCreateSchema(ModelSchema):
    class Meta:
        model = GeneralCampItem
        fields = ["name", "amount", "category"]

class ShoppingListItemSchema(ModelSchema):
    ingredient: IngredientSchema | None = None
    source_meals_text: List[str] = []
    class Meta:
        model = ShoppingListItem
        fields = ["id", "shopping_list", "ingredient", "custom_name", "amount", "unit", "category", "is_checked"]

class ShoppingListGenerateRequestSchema(Schema):
    meal_ids: List[UUID]

class ShoppingListOverviewSchema(Schema):
    id: UUID
    camp_id: UUID
    shared_token: UUID
    created_at: datetime
    included_meals: List[str]

class ShoppingListSchema(Schema):
    id: UUID
    camp_id: UUID
    shared_token: UUID
    items: List[ShoppingListItemSchema]

class InventoryStatusSchema(Schema):
    ingredient_id: UUID
    ingredient_name: str
    category: str
    unit: str
    quantity_bought: float
    quantity_required: float
    balance: float

class ShoppingListManualItemSchema(Schema):
    ingredient_id: UUID
    amount: float
    unit: str
