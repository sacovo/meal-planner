import io

import polars as pl
from django.http import HttpResponse
from ninja import Router

from meals.api.camps import check_camp_access
from meals.models import (
    CampMeal,
    Inventory,
    IngredientUnitConversion,
)
from meals.schemas.inventory import InventoryStatusSchema

router = Router()


def get_inventory_data(camp, user):
    """Calculate inventory status for a camp (requirements vs. stock)."""
    remaining_meals = CampMeal.objects.filter(
        camp=camp, is_done=False
    ).prefetch_related("recipe__ingredients__ingredient")
    reqs = {}

    for meal in remaining_meals:
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

        for ri in meal.recipe.ingredients.all():
            ing = ri.ingredient
            qty = ri.amount * ratio

            if ri.unit != ing.base_unit:
                conv = IngredientUnitConversion.objects.filter(
                    ingredient=ing, unit_name=ri.unit
                ).first()
                if conv:
                    qty = qty * conv.multiplier

            if ing.id not in reqs:
                reqs[ing.id] = {
                    "ingredient_id": ing.id,
                    "ingredient_name": ing.name,
                    "category": ing.category,
                    "unit": ing.base_unit,
                    "quantity_bought": 0,
                    "quantity_required": 0,
                }
            reqs[ing.id]["quantity_required"] += qty

    inventory_items = Inventory.objects.filter(camp=camp)
    for item in inventory_items:
        if item.ingredient_id not in reqs:
            reqs[item.ingredient_id] = {
                "ingredient_id": item.ingredient.id,
                "ingredient_name": item.ingredient.name,
                "category": item.ingredient.category,
                "unit": item.ingredient.base_unit,
                "quantity_bought": 0,
                "quantity_required": 0,
            }
        reqs[item.ingredient_id]["quantity_bought"] += item.quantity_bought

    result = []
    for r in reqs.values():
        r["balance"] = r["quantity_bought"] - r["quantity_required"]
        result.append(r)

    return sorted(result, key=lambda x: (x["category"], x["ingredient_name"]))


@router.get("/camps/{camp_id}/inventory-status", response=list[InventoryStatusSchema])
def get_inventory_status(request, camp_id: str):
    camp = check_camp_access(camp_id, request.user)
    return get_inventory_data(camp, request.user)


@router.get("/camps/{camp_id}/inventory-status/export")
def export_inventory_excel(request, camp_id: str):
    camp = check_camp_access(camp_id, request.user)
    data = get_inventory_data(camp, request.user)

    if not data:
        df = pl.DataFrame(
            {
                "Category": [],
                "Ingredient": [],
                "Unit": [],
                "In Stock": [],
                "Still Needed": [],
                "Balance": [],
            }
        )
    else:
        df = pl.DataFrame(
            [
                {
                    "Category": item["category"],
                    "Ingredient": item["ingredient_name"],
                    "Unit": item["unit"],
                    "In Stock": round(item["quantity_bought"], 2),
                    "Still Needed": round(item["quantity_required"], 2),
                    "Balance": round(item["balance"], 2),
                }
                for item in data
            ]
        )

    buffer = io.BytesIO()
    df.write_excel(buffer)
    buffer.seek(0)

    filename = f"inventory_{camp.name.replace(' ', '_')}.xlsx"
    response = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
