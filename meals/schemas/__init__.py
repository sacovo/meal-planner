"""Schemas package — re-exports all schemas for backward compatibility."""

from .camps import (
    CampCreateSchema,
    CampSchema,
    CampUpdateSchema,
    CollaboratorInviteSchema,
)
from .general_items import GeneralCampItemCreateSchema, GeneralCampItemSchema
from .ingredients import (
    IngredientCreateSchema,
    IngredientSchema,
    RecipeIngredientCreateOrMapSchema,
    RecipeIngredientSchema,
    RecipeIngredientUpdateSchema,
)
from .inventory import InventoryStatusSchema
from .meals import (
    CampMealCreateSchema,
    CampMealSchema,
    CampMealUpdateSchema,
    DietaryPreferenceSchema,
)
from .recipes import (
    RecipeCreateSchema,
    RecipeImportRequestSchema,
    RecipePaginatedSchema,
    RecipeSchema,
    RecipeUpdateSchema,
)
from .shopping import (
    ShoppingListGenerateRequestSchema,
    ShoppingListItemSchema,
    ShoppingListManualItemSchema,
    ShoppingListOverviewSchema,
    ShoppingListSchema,
)

__all__ = [
    "CampCreateSchema",
    "CampMealCreateSchema",
    "CampMealSchema",
    "CampMealUpdateSchema",
    "CampSchema",
    "CampUpdateSchema",
    "CollaboratorInviteSchema",
    "DietaryPreferenceSchema",
    "GeneralCampItemCreateSchema",
    "GeneralCampItemSchema",
    "IngredientCreateSchema",
    "IngredientSchema",
    "InventoryStatusSchema",
    "RecipeCreateSchema",
    "RecipeImportRequestSchema",
    "RecipeIngredientCreateOrMapSchema",
    "RecipeIngredientSchema",
    "RecipeIngredientUpdateSchema",
    "RecipePaginatedSchema",
    "RecipeSchema",
    "RecipeUpdateSchema",
    "ShoppingListGenerateRequestSchema",
    "ShoppingListItemSchema",
    "ShoppingListManualItemSchema",
    "ShoppingListOverviewSchema",
    "ShoppingListSchema",
]
