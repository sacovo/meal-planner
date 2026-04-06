import json
import os

from celery import shared_task
from google import genai
from pydantic import BaseModel


class TranslationResult(BaseModel):
    translated_text: str


class BatchTranslationResult(BaseModel):
    translations: list[dict[str, str]]


class RecipeTranslationResult(BaseModel):
    name: str
    description: str
    instructions: str


@shared_task
def translate_ui_text(uitext_id):
    """Translate a single UIText entry from German to French using Gemini AI."""
    from django.core.exceptions import ObjectDoesNotExist

    from content.models import UIText

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return

    try:
        obj = UIText.objects.get(id=uitext_id)
    except ObjectDoesNotExist:
        return

    if not obj.text_de:
        return

    client = genai.Client(api_key=api_key)
    prompt = f"""Translate the following UI text from German to French.
This is a UI label/text for a camp meal planning application.
Keep it concise and natural. Only return the translation, nothing else.

German text: "{obj.text_de}"
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": TranslationResult,
            },
        )
        data = json.loads(response.text)
        obj.text_fr = data.get("translated_text", "")
        obj.save()
    except Exception as e:
        print(f"[AI] Error translating UIText {obj.key}: {e}")


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

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return

    try:
        ingredient = Ingredient.objects.get(id=ingredient_id)
    except ObjectDoesNotExist:
        return

    if not ingredient.name_de:
        return

    client = genai.Client(api_key=api_key)
    prompt = f"""Translate this food ingredient name from German to French.
Only return the translated name, nothing else. Keep it natural and commonly used.

German: "{ingredient.name_de}"
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": TranslationResult,
            },
        )
        data = json.loads(response.text)
        ingredient.name_fr = data.get("translated_text", "")
        ingredient.save()
    except Exception as e:
        print(f"[AI] Error translating Ingredient {ingredient.name_de}: {e}")


@shared_task
def translate_recipe(recipe_id):
    """Translate Recipe name, description, and instructions from German to French."""
    from django.core.exceptions import ObjectDoesNotExist

    from meals.models import Recipe

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return

    try:
        recipe = Recipe.objects.get(id=recipe_id)
    except ObjectDoesNotExist:
        return

    if not recipe.name_de:
        return

    client = genai.Client(api_key=api_key)

    fields_to_translate = {}
    if recipe.name_de:
        fields_to_translate["name"] = recipe.name_de
    if recipe.description_de:
        fields_to_translate["description"] = recipe.description_de
    if recipe.instructions_de:
        fields_to_translate["instructions"] = recipe.instructions_de

    if not fields_to_translate:
        return

    prompt = f"""Translate the following recipe fields from German to French.
This is for a camp meal planning application. Keep formatting (especially Markdown in instructions) intact.
Return a JSON object with the same keys but translated values.

Fields to translate:
{json.dumps(fields_to_translate, ensure_ascii=False)}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": RecipeTranslationResult,
            },
        )
        data = json.loads(response.text)

        if "name" in data:
            recipe.name_fr = data["name"]
        if "description" in data:
            recipe.description_fr = data["description"]
        if "instructions" in data:
            recipe.instructions_fr = data["instructions"]
        recipe.save()
    except Exception as e:
        print(f"[AI] Error translating Recipe {recipe.name_de}: {e}")


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
