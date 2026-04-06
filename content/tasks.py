"""Celery tasks for AI-powered translations."""

from celery import shared_task

from content.services import (
    get_genai_client,
    translate_ingredient_name,
    translate_recipe_fields,
    translate_text_de_to_fr,
)


@shared_task
def translate_ui_text(uitext_id):
    """Translate a single UIText entry from German to French using Gemini AI."""
    from django.core.exceptions import ObjectDoesNotExist

    from content.models import UIText

    client = get_genai_client()
    if not client:
        return

    try:
        obj = UIText.objects.get(id=uitext_id)
    except ObjectDoesNotExist:
        return

    if not obj.text_de:
        return

    result = translate_text_de_to_fr(client, obj.text_de)
    if result is not None:
        obj.text_fr = result
        obj.save()


@shared_task
def translate_all_ui_texts():
    """Translate all UIText entries that have German but no French text."""
    from content.models import UIText

    texts = UIText.objects.all()
    for obj in texts:
        translate_ui_text.delay(obj.id)


@shared_task
def translate_ingredient(ingredient_id):
    """Translate Ingredient name from German to French using Gemini AI."""
    from django.core.exceptions import ObjectDoesNotExist

    from meals.models import Ingredient

    client = get_genai_client()
    if not client:
        return

    try:
        ingredient = Ingredient.objects.get(id=ingredient_id)
    except ObjectDoesNotExist:
        return

    if not ingredient.name_de:
        return

    result = translate_ingredient_name(client, ingredient.name_de)
    if result is not None:
        ingredient.name_fr = result
        ingredient.save()


@shared_task
def translate_recipe(recipe_id):
    """Translate Recipe name, description, and instructions from German to French."""
    from django.core.exceptions import ObjectDoesNotExist

    from meals.models import Recipe

    client = get_genai_client()
    if not client:
        return

    try:
        recipe = Recipe.objects.get(id=recipe_id)
    except ObjectDoesNotExist:
        return

    if not recipe.name_de:
        return

    fields_to_translate = {}
    if recipe.name_de:
        fields_to_translate["name"] = recipe.name_de
    if recipe.description_de:
        fields_to_translate["description"] = recipe.description_de
    if recipe.instructions_de:
        fields_to_translate["instructions"] = recipe.instructions_de

    if not fields_to_translate:
        return

    data = translate_recipe_fields(client, fields_to_translate)
    if data:
        if "name" in data:
            recipe.name_fr = data["name"]
        if "description" in data:
            recipe.description_fr = data["description"]
        if "instructions" in data:
            recipe.instructions_fr = data["instructions"]
        recipe.save()


@shared_task
def translate_all_ingredients():
    """Translate all Ingredients that have German but no French name."""
    from meals.models import Ingredient

    ingredients = Ingredient.objects.exclude(name_de="").exclude(name_de__isnull=True)
    for ing in ingredients:
        translate_ingredient(ing.id)


@shared_task
def translate_all_recipes():
    """Translate all Recipes that have German but no French name."""
    from meals.models import Recipe

    recipes = Recipe.objects.exclude(name_de="").exclude(name_de__isnull=True)
    for recipe in recipes:
        translate_recipe(recipe.id)
