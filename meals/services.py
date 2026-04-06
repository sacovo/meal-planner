"""Business logic for ingredient/recipe operations, decoupled from Celery tasks."""

from meals.models import Ingredient, IngredientUnitConversion, RecipeIngredient

# Standard metric unit conversions: input_unit -> (base_unit, multiplier)
UNIT_MAP = {
    "g": ("kg", 0.001),
    "kg": ("kg", 1.0),
    "ml": ("l", 0.001),
    "dl": ("l", 0.1),
    "l": ("l", 1.0),
}


def add_ingredient_to_recipe(recipe, ingredient_name, amount, unit):
    """
    Add an ingredient to a recipe, creating/mapping the Ingredient and
    IngredientUnitConversion as needed.

    Returns the created RecipeIngredient.
    """
    from meals.tasks import classify_ingredient, estimate_conversion_multiplier

    ing_name = ingredient_name.strip()
    unit_input = unit.lower().strip()

    ingredient = Ingredient.objects.filter(name__iexact=ing_name).first()
    if not ingredient:
        base_unit = UNIT_MAP.get(unit_input, (unit_input, 1.0))[0]
        ingredient = Ingredient.objects.create(name=ing_name, base_unit=base_unit)
        classify_ingredient.delay(ingredient.id, original_unit=unit_input)
        if unit_input in UNIT_MAP and unit_input != base_unit:
            IngredientUnitConversion.objects.create(
                ingredient=ingredient,
                unit_name=unit_input,
                multiplier=UNIT_MAP[unit_input][1],
            )
    else:
        if ingredient.base_unit != unit_input:
            conv = IngredientUnitConversion.objects.filter(
                ingredient=ingredient, unit_name=unit_input
            ).first()
            if not conv:
                if (
                    unit_input in UNIT_MAP
                    and ingredient.base_unit == UNIT_MAP[unit_input][0]
                ):
                    IngredientUnitConversion.objects.create(
                        ingredient=ingredient,
                        unit_name=unit_input,
                        multiplier=UNIT_MAP[unit_input][1],
                    )
                else:
                    conv = IngredientUnitConversion.objects.create(
                        ingredient=ingredient,
                        unit_name=unit_input,
                        multiplier=1.0,
                        needs_review=True,
                    )
                    estimate_conversion_multiplier.delay(conv.pk)

    return RecipeIngredient.objects.create(
        recipe=recipe, ingredient=ingredient, amount=amount, unit=unit_input
    )
