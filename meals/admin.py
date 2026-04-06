from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.shortcuts import redirect
from django.urls import reverse_lazy
from modeltranslation.admin import TabbedTranslationAdmin
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action

from content.tasks import (
    translate_all_ingredients,
    translate_all_recipes,
    translate_ingredient,
    translate_recipe,
)

from .models import (
    Camp,
    CampMeal,
    DietaryPreference,
    GeneralCampItem,
    Ingredient,
    IngredientUnitConversion,
    Inventory,
    Recipe,
    RecipeIngredient,
    ShoppingList,
    ShoppingListItem,
)


@admin.register(Camp)
class CampAdmin(ModelAdmin):
    list_display = ("name", "start_date", "end_date", "default_people_count", "owner")
    search_fields = ("name",)

class IngredientUnitConversionInline(TabularInline):
    model = IngredientUnitConversion
    extra = 1


@admin.register(Ingredient)
class IngredientAdmin(ModelAdmin, TabbedTranslationAdmin):
    list_display = ("name", "category", "base_unit")
    list_filter = ("category",)
    search_fields = ("name",)
    actions_list = ["translate_all_ingredients_action"]
    actions = ["translate_ingredient_action"]
    actions_detail = ["translate_ingredient_single_action"]

    inlines = [IngredientUnitConversionInline]

    @action(
        description="Translate all ingredients (DE → FR) via AI",
        url_path="translate-all-ingredients",
    )
    def translate_all_ingredients_action(self, request: HttpRequest):
        translate_all_ingredients.delay()
        self.message_user(
            request,
            "AI translation task started for all ingredients missing French translations.",
        )
        return redirect(reverse_lazy("admin:meals_ingredient_changelist"))

    @action(description="Translate selected ingredients")
    def translate_ingredient_action(
        self, request: HttpRequest, query: QuerySet[Ingredient]
    ):
        for ingredient in query:
            translate_ingredient.delay(ingredient.id)

        self.message_user(
            request,
            f"AI translation task started for {len(query)} ingredients.",
        )
        return redirect(reverse_lazy("admin:meals_ingredient_changelist"))

    @action(description="Translate")
    def translate_ingredient_single_action(self, request: HttpRequest, object_id: int):
        translate_ingredient.delay(object_id)
        self.message_user(
            request,
            f"AI translation task started for ingredient {object_id}.",
        )
        return redirect(reverse_lazy("admin:meals_ingredient_change", args=[object_id]))


@admin.register(IngredientUnitConversion)
class IngredientUnitConversionAdmin(ModelAdmin):
    list_display = ("ingredient",  "unit_name", "multiplier", "ingredient__base_unit", "needs_review")
    list_filter = ("needs_review", "ingredient__base_unit")
    search_fields = ("ingredient__name", "unit_name")
    list_editable = ("needs_review", "multiplier")

class RecipeIngredientInline(TabularInline):
    model = RecipeIngredient
    extra = 1

    readonly_fields = ("ingredient", "unit", "amount")

@admin.register(Recipe)
class RecipeAdmin(ModelAdmin, TabbedTranslationAdmin):
    list_display = ("name", "default_portions", "owner")
    search_fields = ("name",)
    actions_list = ["translate_all_recipes_action"]
    actions_detail = ["translate_recipe_single_action"]
    actions = ["translate_action"]

    inlines = [RecipeIngredientInline]

    @action(
        description="Translate all recipes (DE → FR) via AI",
        url_path="translate-all-recipes",
    )
    def translate_all_recipes_action(self, request: HttpRequest):
        translate_all_recipes.delay()
        self.message_user(
            request,
            "AI translation task started for all recipes missing French translations.",
        )
        return redirect(reverse_lazy("admin:meals_recipe_changelist"))

    @action(
        description="Translate selected recipes",
    )
    def translate_action(self, request: HttpRequest, query: QuerySet[Recipe]):
        for recipe in query:
            translate_recipe.delay(recipe.id)

        self.message_user(
            request,
            f"AI translation task started for {len(query)} recipes.",
        )
        return redirect(reverse_lazy("admin:meals_recipe_changelist"))

    @action(
        description="Translate",
    )
    def translate_recipe_single_action(self, request: HttpRequest, object_id: int):
        translate_recipe.delay(object_id)
        self.message_user(
            request,
            f"AI translation task started for recipe {object_id}.",
        )
        return redirect(reverse_lazy("admin:meals_recipe_change", args=[object_id]))


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(ModelAdmin):
    list_display = ("recipe", "ingredient", "amount", "unit")
    search_fields = ("recipe__name", "ingredient__name")


@admin.register(CampMeal)
class CampMealAdmin(ModelAdmin):
    list_display = ("camp", "recipe", "meal_type", "date")
    list_filter = ("meal_type", "date")


@admin.register(GeneralCampItem)
class GeneralCampItemAdmin(ModelAdmin):
    list_display = ("camp", "name", "amount", "category")


@admin.register(ShoppingList)
class ShoppingListAdmin(ModelAdmin):
    list_display = ("camp", "created_at", "updated_at")


@admin.register(ShoppingListItem)
class ShoppingListItemAdmin(ModelAdmin):
    list_display = (
        "shopping_list",
        "ingredient",
        "custom_name",
        "amount",
        "unit",
        "is_checked",
    )
    list_filter = ("is_checked", "category")


@admin.register(Inventory)
class InventoryAdmin(ModelAdmin):
    list_display = ("camp", "ingredient", "quantity_bought", "quantity_used", "unit")


@admin.register(DietaryPreference)
class DietaryPreferenceAdmin(ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
