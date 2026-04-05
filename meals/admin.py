from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import (
    Camp, Ingredient, IngredientCategory, IngredientUnitConversion,
    Recipe, RecipeIngredient, CampMeal, GeneralCampItem,
    ShoppingList, ShoppingListItem, Inventory, DietaryPreference
)

@admin.register(Camp)
class CampAdmin(ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'default_people_count', 'owner')
    search_fields = ('name',)

@admin.register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = ('name', 'category', 'base_unit')
    list_filter = ('category',)
    search_fields = ('name',)

@admin.register(IngredientUnitConversion)
class IngredientUnitConversionAdmin(ModelAdmin):
    list_display = ('ingredient', 'unit_name', 'multiplier', 'needs_review')
    list_filter = ('needs_review',)
    search_fields = ('ingredient__name', 'unit_name')

@admin.register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = ('name', 'default_portions', 'owner')
    search_fields = ('name',)

@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount', 'unit')
    search_fields = ('recipe__name', 'ingredient__name')

@admin.register(CampMeal)
class CampMealAdmin(ModelAdmin):
    list_display = ('camp', 'recipe', 'meal_type', 'date')
    list_filter = ('meal_type', 'date')

@admin.register(GeneralCampItem)
class GeneralCampItemAdmin(ModelAdmin):
    list_display = ('camp', 'name', 'amount', 'category')

@admin.register(ShoppingList)
class ShoppingListAdmin(ModelAdmin):
    list_display = ('camp', 'created_at', 'updated_at')

@admin.register(ShoppingListItem)
class ShoppingListItemAdmin(ModelAdmin):
    list_display = ('shopping_list', 'ingredient', 'custom_name', 'amount', 'unit', 'is_checked')
    list_filter = ('is_checked', 'category')

@admin.register(Inventory)
class InventoryAdmin(ModelAdmin):
    list_display = ('camp', 'ingredient', 'quantity_bought', 'quantity_used', 'unit')

@admin.register(DietaryPreference)
class DietaryPreferenceAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
