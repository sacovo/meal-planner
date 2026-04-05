from meals.models import Inventory
import os
from typing import List
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from ninja import Router

from .models import Camp, Ingredient, Recipe, ShoppingList, GeneralCampItem, RecipeIngredient, CampMeal, DietaryPreference, ShoppingListItem, IngredientUnitConversion
from .schemas import (
    CampSchema, CampCreateSchema, CampUpdateSchema, IngredientSchema, IngredientCreateSchema,
    RecipeSchema, RecipeCreateSchema, GeneralCampItemSchema, GeneralCampItemCreateSchema,
    ShoppingListSchema, RecipeUpdateSchema, RecipeIngredientUpdateSchema,
    InventoryStatusSchema, ShoppingListManualItemSchema,
    RecipeIngredientSchema, RecipeIngredientCreateOrMapSchema,
    RecipeImportRequestSchema, CampMealSchema, CampMealCreateSchema,
    CampMealUpdateSchema, DietaryPreferenceSchema, ShoppingListGenerateRequestSchema,
    ShoppingListItemSchema, ShoppingListOverviewSchema
)
from .tasks import classify_ingredient, estimate_conversion_multiplier, import_recipe_ai_task, internal_add_ingredient_to_recipe

router = Router()
User = get_user_model()

@router.get("/camps", response=list[CampSchema])
def list_camps(request):
    return Camp.objects.all()

@router.post("/camps", response=CampSchema)
def create_camp(request, data: CampCreateSchema):
    owner = User.objects.first() # Placeholder
    camp = Camp.objects.create(**data.dict(), owner=owner)
    return camp

@router.get("/camps/{camp_id}", response=CampSchema)
def get_camp(request, camp_id: str):
    return get_object_or_404(Camp, id=camp_id)

@router.put("/camps/{camp_id}", response=CampSchema)
def update_camp(request, camp_id: str, data: CampUpdateSchema):
    camp = get_object_or_404(Camp, id=camp_id)
    update_data = data.dict(exclude_unset=True)
    for attr, value in update_data.items():
        setattr(camp, attr, value)
    camp.save()
    return camp

@router.get("/auth/me", auth=None)
def get_current_user_status(request):
    if request.user.is_authenticated:
        return {"is_logged_in": True, "username": request.user.username}
    return {"is_logged_in": False}

@router.put("/camps/{camp_id}/meals/{meal_id}/toggle-done", response=CampMealSchema)
def toggle_camp_meal_done(request, camp_id: str, meal_id: str):
    meal = get_object_or_404(CampMeal, camp_id=camp_id, id=meal_id)
    meal.is_done = not meal.is_done
    meal.save()
    return meal

@router.get("/camps/{camp_id}/inventory-status", response=List[InventoryStatusSchema])
def get_inventory_status(request, camp_id: str):
    camp = get_object_or_404(Camp, id=camp_id)
    
    # 1. Total requirements for non-done meals
    remaining_meals = CampMeal.objects.filter(camp=camp, is_done=False).prefetch_related('recipe__ingredients__ingredient')
    reqs = {} # ingredient_id -> data
    
    for meal in remaining_meals:
        p_count = meal.override_people_count if meal.override_people_count is not None else camp.default_people_count
        ratio = p_count / meal.recipe.default_portions if meal.recipe.default_portions else 1
        
        for ri in meal.recipe.ingredients.all():
            ing = ri.ingredient
            qty = ri.amount * ratio
            
            if ri.unit != ing.base_unit:
                conv = IngredientUnitConversion.objects.filter(ingredient=ing, unit_name=ri.unit).first()
                if conv:
                    qty = qty * conv.multiplier
            
            if ing.id not in reqs:
                reqs[ing.id] = {
                    "ingredient_id": ing.id,
                    "ingredient_name": ing.name,
                    "category": ing.category,
                    "unit": ing.base_unit,
                    "quantity_bought": 0,
                    "quantity_required": 0
                }
            reqs[ing.id]["quantity_required"] += qty

    # 2. Add Stock from Inventory model
    inventory_items = Inventory.objects.filter(camp=camp)
    for item in inventory_items:
        if item.ingredient_id not in reqs:
            reqs[item.ingredient_id] = {
                "ingredient_id": item.ingredient.id,
                "ingredient_name": item.ingredient.name,
                "category": item.ingredient.category,
                "unit": item.ingredient.base_unit,
                "quantity_bought": 0,
                "quantity_required": 0
            }
        reqs[item.ingredient_id]["quantity_bought"] += item.quantity_bought

    # 3. Format result
    result = []
    for r in reqs.values():
        r["balance"] = r["quantity_bought"] - r["quantity_required"]
        result.append(r)
    
    return sorted(result, key=lambda x: (x["category"], x["ingredient_name"]))

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
    units = set(["g", "kg", "ml", "dl", "l", "Stück", "Bund", "Prise", "EL", "TL", "Pkg", "Dose"])
    units.update(IngredientUnitConversion.objects.values_list('unit_name', flat=True))
    units.update(RecipeIngredient.objects.values_list('unit', flat=True))
    units.update(Ingredient.objects.values_list('base_unit', flat=True))
    return sorted([u for u in units if u])

@router.get("/recipes", response=list[RecipeSchema])
def list_recipes(request, q: str = None):
    qs = Recipe.objects.all()
    if q:
        qs = qs.filter(name__icontains=q)
    return qs

@router.post("/recipes", response=RecipeSchema)
def create_recipe(request, data: RecipeCreateSchema):
    recipe_data = data.dict(exclude={"preference_ids"})
    recipe = Recipe.objects.create(**recipe_data)
    if data.preference_ids:
        recipe.preferences.set(data.preference_ids)
    return recipe

@router.post("/recipes/import", response=RecipeSchema)
def import_recipe(request, data: RecipeImportRequestSchema):
    owner = User.objects.first() # Placeholder
    recipe = Recipe.objects.create(
        name="Importing...",
        is_importing=True,
        owner=owner
    )
    import_recipe_ai_task.delay(recipe.id, data.raw_text)
    return recipe

@router.get("/recipes/{recipe_id}", response=RecipeSchema)
def get_recipe(request, recipe_id: str):
    return get_object_or_404(Recipe, id=recipe_id)

@router.put("/recipes/{recipe_id}", response=RecipeSchema)
def update_recipe(request, recipe_id: str, data: RecipeUpdateSchema):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    update_data = data.dict(exclude_unset=True)
    pref_ids = update_data.pop("preference_ids", None)
    for attr, value in update_data.items():
        setattr(recipe, attr, value)
    recipe.save()
    if pref_ids is not None:
        recipe.preferences.set(pref_ids)
    return recipe

@router.get("/recipes/{recipe_id}/ingredients", response=list[RecipeIngredientSchema])
def list_recipe_ingredients(request, recipe_id: str):
    return RecipeIngredient.objects.filter(recipe_id=recipe_id).select_related('ingredient')

@router.post("/recipes/{recipe_id}/ingredients", response=RecipeIngredientSchema)
def add_recipe_ingredient(request, recipe_id: str, data: RecipeIngredientCreateOrMapSchema):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    return internal_add_ingredient_to_recipe(recipe, data.ingredient_name, data.amount, data.unit)

@router.put("/recipes/{recipe_id}/ingredients/{ingredient_id}", response=RecipeIngredientSchema)
def update_recipe_ingredient(request, recipe_id: str, ingredient_id: str, data: RecipeIngredientUpdateSchema):
    ri = get_object_or_404(RecipeIngredient, recipe_id=recipe_id, id=ingredient_id)
    ri.amount = data.amount
    ri.unit = data.unit.lower().strip()
    ri.save()
    return ri

@router.delete("/recipes/{recipe_id}/ingredients/{ingredient_id}")
def delete_recipe_ingredient(request, recipe_id: str, ingredient_id: str):
    ri = get_object_or_404(RecipeIngredient, recipe_id=recipe_id, id=ingredient_id)
    ri.delete()
    return {"success": True}

@router.get("/preferences", response=list[DietaryPreferenceSchema])
def list_preferences(request):
    return DietaryPreference.objects.all()

@router.get("/camps/{camp_id}/meals", response=list[CampMealSchema])
def list_camp_meals(request, camp_id: str):
    return CampMeal.objects.filter(camp_id=camp_id).select_related('serves_preference').order_by("date", "meal_type")

@router.post("/camps/{camp_id}/meals", response=CampMealSchema)
def create_camp_meal(request, camp_id: str, data: CampMealCreateSchema):
    camp = get_object_or_404(Camp, id=camp_id)
    recipe = get_object_or_404(Recipe, id=data.recipe_id)
    meal = CampMeal.objects.create(
        camp=camp,
        recipe=recipe,
        meal_type=data.meal_type,
        date=data.date,
        override_people_count=data.override_people_count,
        serves_preference_id=data.serves_preference_id
    )
    return meal

@router.put("/camps/{camp_id}/meals/{meal_id}", response=CampMealSchema)
def update_camp_meal(request, camp_id: str, meal_id: str, data: CampMealUpdateSchema):
    meal = get_object_or_404(CampMeal, camp_id=camp_id, id=meal_id)
    if data.override_people_count is not None:
        meal.override_people_count = data.override_people_count
    if data.serves_preference_id is not None:
        meal.serves_preference_id = data.serves_preference_id
    meal.save()
    return meal

@router.delete("/camps/{camp_id}/meals/{meal_id}")
def delete_camp_meal(request, camp_id: str, meal_id: str):
    meal = get_object_or_404(CampMeal, camp_id=camp_id, id=meal_id)
    meal.delete()
    return {"success": True}

@router.get("/camps/{camp_id}/general-items", response=list[GeneralCampItemSchema])
def list_camp_general_items(request, camp_id: str):
    return GeneralCampItem.objects.filter(camp_id=camp_id)

@router.post("/camps/{camp_id}/general-items", response=GeneralCampItemSchema)
def create_camp_general_item(request, camp_id: str, data: GeneralCampItemCreateSchema):
    camp = get_object_or_404(Camp, id=camp_id)
    return GeneralCampItem.objects.create(camp=camp, **data.dict())

@router.delete("/camps/{camp_id}/general-items/{item_id}")
def delete_camp_general_item(request, camp_id: str, item_id: str):
    item = get_object_or_404(GeneralCampItem, camp_id=camp_id, id=item_id)
    item.delete()
    return {"success": True}

@router.post("/camps/{camp_id}/shopping-lists/add-manual-item", response=ShoppingListItemSchema)
def add_manual_shopping_item(request, camp_id: str, data: ShoppingListManualItemSchema):
    camp = get_object_or_404(Camp, id=camp_id)
    ingredient = get_object_or_404(Ingredient, id=data.ingredient_id)
    
    # 1. Get or create latest shopping list
    sl = ShoppingList.objects.filter(camp=camp).order_by("-created_at").first()
    if not sl:
        sl = ShoppingList.objects.create(camp=camp)
    
    # 2. Add Item
    item = ShoppingListItem.objects.create(
        shopping_list=sl,
        ingredient=ingredient,
        amount=data.amount,
        unit=data.unit,
        category=ingredient.category,
        source_meals_text=["Manual addition from inventory"]
    )
    return item

@router.post("/camps/{camp_id}/shopping-list/generate", response=ShoppingListSchema)
def generate_shopping_list(request, camp_id: str, data: ShoppingListGenerateRequestSchema):
    camp = get_object_or_404(Camp, id=camp_id)
    meals = list(CampMeal.objects.filter(camp=camp, id__in=data.meal_ids).select_related('recipe'))
    sl = ShoppingList.objects.create(camp=camp)
    sl.meals.set(meals)
    ingredients_agg = {}
    for meal in meals:
        p_count = meal.override_people_count if meal.override_people_count is not None else camp.default_people_count
        ratio = p_count / meal.recipe.default_portions if meal.recipe.default_portions else 1
        for ri in meal.recipe.ingredients.select_related('ingredient'):
            ing = ri.ingredient
            qty = ri.amount * ratio
            key = ing.id
            if key not in ingredients_agg:
                ingredients_agg[key] = {
                    "ingredient": ing, "amount": 0, "unit": ing.base_unit, "category": ing.category, "sources": []
                }
            if ri.unit == ing.base_unit:
                ingredients_agg[key]["amount"] += qty
            else:
                conv = IngredientUnitConversion.objects.filter(ingredient=ing, unit_name=ri.unit).first()
                if conv:
                    qty = qty * conv.multiplier
                ingredients_agg[key]["amount"] += qty
            day_str = meal.date.strftime("%a, %d.%m.")
            source_str = f"{day_str} ({meal.get_meal_type_display()}): {meal.recipe.name}"
            if source_str not in ingredients_agg[key]["sources"]:
                ingredients_agg[key]["sources"].append(source_str)
    for key, data in ingredients_agg.items():
        ShoppingListItem.objects.create(
            shopping_list=sl, ingredient=data["ingredient"], amount=data["amount"], unit=data["unit"], category=data["category"], source_meals_text=data["sources"]
        )

    # General Camp Items
    g_items = GeneralCampItem.objects.filter(camp=camp)
    for g_item in g_items:
        ing, _ = Ingredient.objects.get_or_create(
            name=g_item.name,
            defaults={"category": g_item.category, "base_unit": "Stück"}
        )
        # Parse amount if possible, else 1
        try:
            amt = float(g_item.amount.split()[0].replace(',', '.'))
        except:
            amt = 1.0
        unit = g_item.amount.replace(str(amt), "").strip() or ing.base_unit
        
        ShoppingListItem.objects.create(
            shopping_list=sl,
            ingredient=ing,
            amount=amt,
            unit=unit,
            category=g_item.category,
            source_meals_text=["General Camp Item"]
        )

    return {
        "id": sl.id, "camp_id": sl.camp_id, "shared_token": sl.shared_token, "items": list(sl.items.all())
    }

@router.get("/shopping-lists/{list_id}", response=ShoppingListSchema)
def get_shopping_list(request, list_id: str):
    s_list = get_object_or_404(ShoppingList, id=list_id)
    return {
        "id": s_list.id, "camp_id": s_list.camp.id, "shared_token": s_list.shared_token, "items": list(s_list.items.all())
    }

@router.get("/camps/{camp_id}/shopping-lists", response=list[ShoppingListOverviewSchema])
def list_camp_shopping_lists(request, camp_id: str):
    lists = ShoppingList.objects.filter(camp_id=camp_id).prefetch_related('meals__recipe').order_by('-created_at')
    result = []
    for sl in lists:
        included_meals = [f"{m.date.strftime('%a, %d.%m.')} ({m.get_meal_type_display()}): {m.recipe.name}" for m in sl.meals.all()]
        result.append({
            "id": sl.id,
            "camp_id": sl.camp_id,
            "shared_token": sl.shared_token,
            "created_at": sl.created_at,
            "included_meals": included_meals
        })
    return result

@router.delete("/shopping-lists/{list_id}")
def delete_shopping_list(request, list_id: str):
    s_list = get_object_or_404(ShoppingList, id=list_id)
    s_list.delete()
    return {"success": True}

@router.get("/shared/shopping-lists/{token}", response=ShoppingListSchema, auth=None)
def get_shared_shopping_list(request, token: str):
    sl = get_object_or_404(ShoppingList, shared_token=token)
    return {
        "id": sl.id, "camp_id": sl.camp_id, "shared_token": sl.shared_token, "items": list(sl.items.all())
    }

@router.put("/shared/shopping-lists/{token}/items/{item_id}/toggle", response=ShoppingListItemSchema, auth=None)
def toggle_shared_shopping_item(request, token: str, item_id: str):
    sl = get_object_or_404(ShoppingList, shared_token=token)
    item = get_object_or_404(ShoppingListItem, shopping_list=sl, id=item_id)
    
    old_checked = item.is_checked
    new_checked = not item.is_checked
    item.is_checked = new_checked
    item.save()

    # Sync to Inventory
    if item.ingredient:
        inv, _ = Inventory.objects.get_or_create(
            camp=sl.camp, 
            ingredient=item.ingredient,
            defaults={"unit": item.unit}
        )
        
        # Determine the amount to add/sub in base units if units differ
        diff = item.amount if new_checked else -item.amount
        
        # If the shopping list item unit is different from base_unit, convert it
        base_diff = diff
        if item.unit != item.ingredient.base_unit:
            conv = IngredientUnitConversion.objects.filter(ingredient=item.ingredient, unit_name=item.unit).first()
            if conv:
                base_diff = diff * conv.multiplier
        
        inv.quantity_bought += base_diff
        inv.save()

    return item
