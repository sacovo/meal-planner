from typing import Optional

from ninja import ModelSchema, Schema

from meals.models import Recipe

from .meals import DietaryPreferenceSchema


class RecipeSchema(ModelSchema):
    preferences: list[DietaryPreferenceSchema] = []
    tags: list[str] = []
    owner_username: Optional[str] = None
    collaborators: list[str] = []

    @staticmethod
    def resolve_owner_username(obj):
        return obj.owner.username if obj.owner else None

    @staticmethod
    def resolve_collaborators(obj):
        return [c.username for c in obj.collaborators.all()]

    class Meta:
        model = Recipe
        fields = [
            "id",
            "name",
            "description",
            "instructions",
            "tags",
            "default_portions",
            "is_importing",
        ]


class RecipeCreateSchema(ModelSchema):
    preference_ids: list[int] = []
    tags: list[str] = []

    class Meta:
        model = Recipe
        fields = ["name", "description", "instructions", "tags", "default_portions"]


class RecipeUpdateSchema(Schema):
    name: str | None = None
    description: str | None = None
    instructions: str | None = None
    default_portions: int | None = None
    preference_ids: list[int] | None = None
    tags: list[str] = None


class RecipeImportRequestSchema(Schema):
    raw_text: str
