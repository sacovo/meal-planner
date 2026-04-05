import os
import json
import uuid
from typing import List
from celery import shared_task
from django.conf import settings
from google import genai
from pydantic import BaseModel, ConfigDict
from enum import Enum

# Standard Models
from meals.models import Ingredient, IngredientUnitConversion, Recipe, RecipeIngredient

class CategoryEnum(str, Enum):
    PRODUCE = "PRODUCE"
    MEAT = "MEAT"
    DAIRY = "DAIRY"
    PANTRY = "PANTRY"
    SPICES = "SPICES"
    BREAD = "BREAD"
    DRINKS = "DRINKS"
    FROZEN = "FROZEN"
    NON_FOOD = "NON_FOOD"
    OTHER = "OTHER"

class ClassifiedIngredient(BaseModel):
    category: CategoryEnum
    base_unit: str

@shared_task
def classify_ingredient(ingredient_id, original_unit=None):
    from django.core.exceptions import ObjectDoesNotExist
    
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return
        
    try:
        ingredient = Ingredient.objects.get(id=ingredient_id)
    except ObjectDoesNotExist:
        return

    client = genai.Client(api_key=api_key)
    prompt = f"Categorize this ingredient strictly: \"{ingredient.name}\". Provide category and typical base metric unit."

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                'response_mime_type': 'application/json',
                'response_schema': ClassifiedIngredient,
            },
        )
        data = json.loads(response.text)
        new_category = data.get("category", "OTHER")
        new_unit = data.get("base_unit", ingredient.base_unit)
        
        ingredient.category = new_category
        if new_unit in ["g", "kg", "ml", "dl", "l", "pieces", "Stück"]:
            if ingredient.base_unit != new_unit:
                ingredient.base_unit = new_unit
                if original_unit and original_unit != new_unit:
                    conv, created = IngredientUnitConversion.objects.get_or_create(
                        ingredient=ingredient,
                        unit_name=original_unit,
                        defaults={'multiplier': 1.0, 'needs_review': True}
                    )
                    if created:
                        estimate_conversion_multiplier.delay(conv.id)
            
        ingredient.save()
    except Exception as e:
        print(f"[AI] Error during classification: {e}")

class AIConversionEstimator(BaseModel):
    estimated_multiplier: float
    explanation: str

@shared_task
def estimate_conversion_multiplier(conversion_id):
    from django.core.exceptions import ObjectDoesNotExist
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key: return
        
    try:
        conv = IngredientUnitConversion.objects.select_related('ingredient').get(id=conversion_id)
    except ObjectDoesNotExist:
        return

    client = genai.Client(api_key=api_key)
    prompt = f"Estimate multiplier for {conv.ingredient.name}: {conv.unit_name} -> {conv.ingredient.base_unit}"

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                'response_mime_type': 'application/json',
                'response_schema': AIConversionEstimator,
            },
        )
        data = json.loads(response.text)
        conv.multiplier = float(data.get("estimated_multiplier", 1.0))
        conv.save()
    except Exception as e:
        print(f"[AI] Error during conversion estimation: {e}")

class AIRecipeIngredient(BaseModel):
    name: str
    amount: float
    unit: str

class AIRecipeLayout(BaseModel):
    name: str
    description: str
    instructions: str
    default_portions: int
    ingredients: list[AIRecipeIngredient]

def internal_add_ingredient_to_recipe(recipe, ingredient_name, amount, unit):
    ing_name = ingredient_name.strip()
    unit_input = unit.lower().strip()
    unit_map = {'g': ('kg', 0.001), 'kg': ('kg', 1.0), 'ml': ('l', 0.001), 'dl': ('l', 0.1), 'l': ('l', 1.0)}
    
    ingredient = Ingredient.objects.filter(name__iexact=ing_name).first()
    if not ingredient:
        base_unit = unit_map.get(unit_input, (unit_input, 1.0))[0]
        ingredient = Ingredient.objects.create(name=ing_name, base_unit=base_unit)
        classify_ingredient.delay(ingredient.id, original_unit=unit_input)
        if unit_input in unit_map and unit_input != base_unit:
            IngredientUnitConversion.objects.create(ingredient=ingredient, unit_name=unit_input, multiplier=unit_map[unit_input][1])
    else:
        if ingredient.base_unit != unit_input:
            conv = IngredientUnitConversion.objects.filter(ingredient=ingredient, unit_name=unit_input).first()
            if not conv:
                if unit_input in unit_map and ingredient.base_unit == unit_map[unit_input][0]:
                    IngredientUnitConversion.objects.create(ingredient=ingredient, unit_name=unit_input, multiplier=unit_map[unit_input][1])
                else:
                    conv = IngredientUnitConversion.objects.create(ingredient=ingredient, unit_name=unit_input, multiplier=1.0, needs_review=True)
                    estimate_conversion_multiplier.delay(conv.id)

    return RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredient, amount=amount, unit=unit_input)

@shared_task
def import_recipe_ai_task(recipe_id, raw_text):
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key: return
    
    recipe = Recipe.objects.get(id=recipe_id)
    client = genai.Client(api_key=api_key)
    prompt = f"""
    Analyze this recipe text and extract it into a structured JSON format.
    
    CRITICAL INSTRUCTIONS for Ingredients:
    - Generalize the ingredient name: Remove preparation methods like "gepresst", "fein gehackt", "geschält", "gewürfelt", etc.
    - Normalize the name: For example, "Knoblauchzehe" should become "Knoblauch" with the unit "Zehe".
    - Avoid specific brands unless essential.
    - NEVER use 0 as an amount. Even if the recipe says "to taste" or "nach Belieben", estimate a reasonable shopping quantity for the `default_portions` and use a standard unit (g, ml, Stück, Zehe, etc.) so it shows up correctly on a shopping list.
    - Use Markdown for `instructions`: Use numbered lists for steps, bold for emphasis on timings or temperatures, and bullet points for variations if present.
    
    TEXT TO ANALYZE:
    {raw_text}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                'response_mime_type': 'application/json',
                'response_schema': AIRecipeLayout,
            },
        )
        parsed = json.loads(response.text)
        
        recipe.name = parsed.get("name", recipe.name)
        recipe.description = parsed.get("description", "")
        recipe.instructions = parsed.get("instructions", "")
        recipe.default_portions = parsed.get("default_portions", 1)
        recipe.save()
        
        for ing_data in parsed.get("ingredients", []):
            internal_add_ingredient_to_recipe(recipe, ing_data.get("name"), ing_data.get("amount", 1), ing_data.get("unit", ""))
            
        # Finalize import
        recipe.is_importing = False
        recipe.save()
            
    except Exception as e:
        recipe.name = f"Import Failed: {recipe.name}"
        recipe.is_importing = False
        recipe.save()
        print(f"[AI] Magic Import failed: {e}")
