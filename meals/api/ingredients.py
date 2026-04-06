from ninja import Router

from meals.models import (
    Ingredient,
    IngredientUnitConversion,
    Recipe,
    RecipeIngredient,
)
from meals.schemas.ingredients import IngredientCreateSchema, IngredientSchema

router = Router()


@router.get("/ingredients", response=list[IngredientSchema])
def list_ingredients(request, q: str = None):
    qs = Ingredient.objects.all()
    if q:
        qs = qs.filter(name__icontains=q)
    return qs


@router.post("/ingredients", response=IngredientSchema)
def create_ingredient(request, data: IngredientCreateSchema):
    return Ingredient.objects.create(**data.dict())


@router.get("/units", response=list[str])
def list_units(request):
    units = set(
        [
            "g",
            "kg",
            "ml",
            "dl",
            "l",
            "Stück",
            "Bund",
            "Prise",
            "EL",
            "TL",
            "Pkg",
            "Dose",
        ]
    )
    units.update(IngredientUnitConversion.objects.values_list("unit_name", flat=True))
    units.update(RecipeIngredient.objects.values_list("unit", flat=True))
    units.update(Ingredient.objects.values_list("base_unit", flat=True))
    return sorted([u for u in units if u])


@router.get("/tags", response=list[str])
def list_tags(request):
    all_tags = Recipe.objects.values_list("tags", flat=True)
    tags_set = set()
    for t_list in all_tags:
        if isinstance(t_list, list):
            tags_set.update(t_list)
    return sorted(list(tags_set))
