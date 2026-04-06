from ninja import ModelSchema, Schema

from meals.models import Ingredient, RecipeIngredient


class IngredientSchema(ModelSchema):
    class Meta:
        model = Ingredient
        fields = ["id", "name", "category", "base_unit"]


class IngredientCreateSchema(ModelSchema):
    class Meta:
        model = Ingredient
        fields = ["name", "category", "base_unit"]


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
