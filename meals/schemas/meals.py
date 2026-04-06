from datetime import date
from uuid import UUID

from ninja import ModelSchema, Schema

from meals.models import CampMeal, DietaryPreference


class DietaryPreferenceSchema(ModelSchema):
    class Meta:
        model = DietaryPreference
        fields = ["id", "name"]


class CampMealSchema(ModelSchema):
    serves_preference: DietaryPreferenceSchema | None = None
    recipe_name: str = ""
    recipe_default_portions: int = 4

    @staticmethod
    def resolve_recipe_name(obj):
        return obj.recipe.name

    @staticmethod
    def resolve_recipe_default_portions(obj):
        return obj.recipe.default_portions

    class Meta:
        model = CampMeal
        fields = [
            "id",
            "camp",
            "recipe",
            "meal_type",
            "date",
            "override_people_count",
            "leftovers_noted",
            "is_done",
        ]


class CampMealCreateSchema(Schema):
    recipe_id: UUID
    meal_type: str
    date: date
    override_people_count: int = None
    serves_preference_id: int = None


class CampMealUpdateSchema(Schema):
    override_people_count: int | None = None
    serves_preference_id: int | None = None
