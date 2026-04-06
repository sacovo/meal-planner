import io

import polars as pl
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ninja import Router

from meals.api.camps import check_camp_access
from meals.models import (
    Camp,
    CampMeal,
    GeneralCampItem,
    Ingredient,
    IngredientUnitConversion,
    ShoppingList,
    ShoppingListItem,
)
from meals.schemas.shopping import (
    ShoppingListGenerateRequestSchema,
    ShoppingListItemSchema,
    ShoppingListManualItemSchema,
    ShoppingListOverviewSchema,
    ShoppingListSchema,
)

router = Router()


def _generate_excel_response(s_list):
    """Generate an Excel file download response for a shopping list."""
    items = s_list.items.all().select_related("ingredient")
    if not items:
        df = pl.DataFrame(
            {
                "Category": [],
                "Item": [],
                "Amount": [],
                "Unit": [],
                "Sources": [],
                "Checked": [],
            }
        )
    else:
        df_data = []
        for item in items:
            name = (
                item.ingredient.name
                if item.ingredient
                else (item.custom_name or "Unknown")
            )
            df_data.append(
                {
                    "Category": item.category,
                    "Item": name,
                    "Amount": round(item.amount, 2),
                    "Unit": item.unit,
                    "Sources": ", ".join(item.source_meals_text),
                    "Checked": "✓" if item.is_checked else "",
                }
            )
        df = pl.DataFrame(df_data)

    buffer = io.BytesIO()
    df.write_excel(buffer)
    buffer.seek(0)

    filename = f"shopping_list_{s_list.camp.name.replace(' ', '_')}_{s_list.created_at.strftime('%Y%m%d')}.xlsx"
    response = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _add_general_items_to_shopping_list(camp, sl):
    """Add general camp items to a shopping list as ShoppingListItems."""
    g_items = GeneralCampItem.objects.filter(camp=camp)
    for g_item in g_items:
        ing, _ = Ingredient.objects.get_or_create(
            name=g_item.name,
            defaults={"category": g_item.category, "base_unit": "Stück"},
        )
        try:
            amt = float(g_item.amount.split()[0].replace(",", "."))
        except ValueError:
            amt = 1.0
        unit = g_item.amount.replace(str(amt), "").strip() or ing.base_unit

        ShoppingListItem.objects.create(
            shopping_list=sl,
            ingredient=ing,
            amount=amt,
            unit=unit,
            category=g_item.category,
            source_meals_text=["General Camp Item"],
        )


def _serialize_shopping_list(sl):
    """Build a dict matching ShoppingListSchema from a ShoppingList instance."""
    return {
        "id": sl.id,
        "camp_id": sl.camp_id,
        "shared_token": sl.shared_token,
        "items": list(sl.items.all()),
    }


@router.post(
    "/camps/{camp_id}/shopping-lists/add-manual-item", response=ShoppingListItemSchema
)
def add_manual_shopping_item(request, camp_id: str, data: ShoppingListManualItemSchema):
    camp = get_object_or_404(Camp, id=camp_id)
    ingredient = get_object_or_404(Ingredient, id=data.ingredient_id)

    sl = ShoppingList.objects.filter(camp=camp).order_by("-created_at").first()
    if not sl:
        sl = ShoppingList.objects.create(camp=camp)

    item = ShoppingListItem.objects.create(
        shopping_list=sl,
        ingredient=ingredient,
        amount=data.amount,
        unit=data.unit,
        category=ingredient.category,
        source_meals_text=["Manual addition from inventory"],
    )
    return item


@router.post("/camps/{camp_id}/shopping-list/generate", response=ShoppingListSchema)
def generate_shopping_list(
    request, camp_id: str, data: ShoppingListGenerateRequestSchema
):
    camp = check_camp_access(camp_id, request.user)
    meals = list(
        CampMeal.objects.filter(camp=camp, id__in=data.meal_ids).select_related(
            "recipe"
        )
    )
    sl = ShoppingList.objects.create(camp=camp)
    sl.meals.set(meals)
    ingredients_agg = {}
    for meal in meals:
        p_count = (
            meal.override_people_count
            if meal.override_people_count is not None
            else camp.default_people_count
        )
        ratio = (
            p_count / meal.recipe.default_portions
            if meal.recipe.default_portions
            else 1
        )
        for ri in meal.recipe.ingredients.select_related("ingredient"):
            ing = ri.ingredient
            qty = ri.amount * ratio
            key = ing.id
            if key not in ingredients_agg:
                ingredients_agg[key] = {
                    "ingredient": ing,
                    "amount": 0,
                    "unit": ing.base_unit,
                    "category": ing.category,
                    "sources": [],
                }
            if ri.unit == ing.base_unit:
                ingredients_agg[key]["amount"] += qty
            else:
                conv = IngredientUnitConversion.objects.filter(
                    ingredient=ing, unit_name=ri.unit
                ).first()
                if conv:
                    qty = qty * conv.multiplier
                ingredients_agg[key]["amount"] += qty
            day_str = meal.date.strftime("%a, %d.%m.")
            source_str = (
                f"{day_str} ({meal.get_meal_type_display()}): {meal.recipe.name}"
            )
            if source_str not in ingredients_agg[key]["sources"]:
                ingredients_agg[key]["sources"].append(source_str)
    for key, agg_data in ingredients_agg.items():
        ShoppingListItem.objects.create(
            shopping_list=sl,
            ingredient=agg_data["ingredient"],
            amount=agg_data["amount"],
            unit=agg_data["unit"],
            category=agg_data["category"],
            source_meals_text=agg_data["sources"],
        )

    _add_general_items_to_shopping_list(camp, sl)
    return _serialize_shopping_list(sl)


@router.post(
    "/camps/{camp_id}/shopping-lists/{list_id}/move-general-items",
    response=ShoppingListSchema,
)
def move_general_items_to_shopping_list(request, camp_id: str, list_id: str):
    camp = check_camp_access(camp_id, request.user)
    sl = get_object_or_404(ShoppingList, id=list_id, camp=camp)

    _add_general_items_to_shopping_list(camp, sl)

    # Delete them from source as requested by user ("move")
    GeneralCampItem.objects.filter(camp=camp).delete()

    return _serialize_shopping_list(sl)


@router.get("/shopping-lists/{list_id}", response=ShoppingListSchema)
def get_shopping_list(request, list_id: str):
    s_list = get_object_or_404(ShoppingList, id=list_id)
    check_camp_access(s_list.camp_id, request.user)
    return _serialize_shopping_list(s_list)


@router.get("/shopping-lists/{list_id}/export")
def export_shopping_list(request, list_id: str):
    s_list = get_object_or_404(ShoppingList, id=list_id)
    check_camp_access(s_list.camp_id, request.user)
    return _generate_excel_response(s_list)


@router.get(
    "/camps/{camp_id}/shopping-lists", response=list[ShoppingListOverviewSchema]
)
def list_camp_shopping_lists(request, camp_id: str):
    check_camp_access(camp_id, request.user)
    lists = (
        ShoppingList.objects.filter(camp_id=camp_id)
        .prefetch_related("meals__recipe")
        .order_by("-created_at")
    )
    result = []
    for sl in lists:
        included_meals = [
            f"{m.date.strftime('%a, %d.%m.')} ({m.get_meal_type_display()}): {m.recipe.name}"
            for m in sl.meals.all()
        ]
        result.append(
            {
                "id": sl.id,
                "camp_id": sl.camp_id,
                "shared_token": sl.shared_token,
                "created_at": sl.created_at,
                "included_meals": included_meals,
            }
        )
    return result


@router.delete("/shopping-lists/{list_id}")
def delete_shopping_list(request, list_id: str):
    s_list = get_object_or_404(ShoppingList, id=list_id)
    s_list.delete()
    return {"success": True}


@router.get("/shared/shopping-lists/{token}", response=ShoppingListSchema, auth=None)
def get_shared_shopping_list(request, token: str):
    sl = get_object_or_404(ShoppingList, shared_token=token)
    return _serialize_shopping_list(sl)


@router.get("/shared/shopping-lists/{token}/export", auth=None)
def export_shared_shopping_list(request, token: str):
    sl = get_object_or_404(ShoppingList, shared_token=token)
    return _generate_excel_response(sl)


@router.put(
    "/shared/shopping-lists/{token}/items/{item_id}/toggle",
    response=ShoppingListItemSchema,
    auth=None,
)
def toggle_shared_shopping_item(request, token: str, item_id: str):
    from meals.models import Inventory

    sl = get_object_or_404(ShoppingList, shared_token=token)
    item = get_object_or_404(ShoppingListItem, shopping_list=sl, id=item_id)

    new_checked = not item.is_checked
    item.is_checked = new_checked
    item.save()

    # Sync to Inventory
    if item.ingredient:
        inv, _ = Inventory.objects.get_or_create(
            camp=sl.camp, ingredient=item.ingredient, defaults={"unit": item.unit}
        )

        diff = item.amount if new_checked else -item.amount

        base_diff = diff
        if item.unit != item.ingredient.base_unit:
            conv = IngredientUnitConversion.objects.filter(
                ingredient=item.ingredient, unit_name=item.unit
            ).first()
            if conv:
                base_diff = diff * conv.multiplier

        inv.quantity_bought += base_diff
        inv.save()

    return item
