from ninja import ModelSchema

from meals.models import GeneralCampItem


class GeneralCampItemSchema(ModelSchema):
    class Meta:
        model = GeneralCampItem
        fields = ["id", "camp", "name", "amount", "category"]


class GeneralCampItemCreateSchema(ModelSchema):
    class Meta:
        model = GeneralCampItem
        fields = ["name", "amount", "category"]
