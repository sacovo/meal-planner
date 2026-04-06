from typing import Optional

from ninja import ModelSchema, Schema

from meals.models import Camp


class CampSchema(ModelSchema):
    owner_username: Optional[str] = None
    collaborators: list[str] = []

    @staticmethod
    def resolve_owner_username(obj):
        return obj.owner.username

    @staticmethod
    def resolve_collaborators(obj):
        return [c.username for c in obj.collaborators.all()]

    class Meta:
        model = Camp
        fields = [
            "id",
            "name",
            "default_people_count",
            "start_date",
            "end_date",
            "notes",
        ]


class CampCreateSchema(ModelSchema):
    class Meta:
        model = Camp
        fields = ["name", "default_people_count", "start_date", "end_date"]


class CampUpdateSchema(Schema):
    name: Optional[str] = None
    default_people_count: Optional[int] = None
    notes: Optional[str] = None


class CollaboratorInviteSchema(Schema):
    username: str
