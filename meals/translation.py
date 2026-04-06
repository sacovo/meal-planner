from modeltranslation.translator import TranslationOptions, register

from .models import Ingredient, Recipe


@register(Ingredient)
class IngredientTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Recipe)
class RecipeTranslationOptions(TranslationOptions):
    fields = ("name", "description", "instructions")
