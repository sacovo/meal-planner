"""Business logic for AI-powered translations, decoupled from Celery tasks."""

import json
import os

from google import genai
from pydantic import BaseModel


class TranslationResult(BaseModel):
    translated_text: str


class RecipeTranslationResult(BaseModel):
    name: str
    description: str
    instructions: str


def get_genai_client():
    """Return a configured Gemini client, or None if no API key is set."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)


def translate_text_de_to_fr(client, text, context="UI label/text"):
    """Translate a German text to French using Gemini AI. Returns the translated string or None."""
    prompt = f"""Translate the following UI text from German to French.
This is a {context} for a camp meal planning application.
Keep it concise and natural. Only return the translation, nothing else.

German text: "{text}"
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
        return data.get("translated_text", "")
    except Exception as e:
        print(f"[AI] Error translating text: {e}")
        return None


def translate_ingredient_name(client, name_de):
    """Translate a German ingredient name to French. Returns the translated string or None."""
    prompt = f"""Translate this food ingredient name from German to French.
Only return the translated name, nothing else. Keep it natural and commonly used.

German: "{name_de}"
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
        return data.get("translated_text", "")
    except Exception as e:
        print(f"[AI] Error translating ingredient: {e}")
        return None


def translate_recipe_fields(client, fields_to_translate):
    """
    Translate recipe fields from German to French.

    Args:
        client: Gemini client
        fields_to_translate: dict of field_name -> german_text

    Returns:
        dict of field_name -> french_text, or None on error
    """
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
        return json.loads(response.text)
    except Exception as e:
        print(f"[AI] Error translating recipe fields: {e}")
        return None
