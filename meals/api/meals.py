from django.shortcuts import get_object_or_404
from ninja import Router

from meals.api.camps import check_camp_access
from meals.models import CampMeal, Recipe
from meals.schemas.meals import (
    CampMealCreateSchema,
    CampMealSchema,
    CampMealUpdateSchema,
)

router = Router()


@router.get("/camps/{camp_id}/meals", response=list[CampMealSchema])
def list_camp_meals(request, camp_id: str):
    check_camp_access(camp_id, request.user)
    return (
        CampMeal.objects.filter(camp_id=camp_id)
        .select_related("serves_preference", "recipe")
        .order_by("date", "meal_type")
    )


@router.post("/camps/{camp_id}/meals", response=CampMealSchema)
def create_camp_meal(request, camp_id: str, data: CampMealCreateSchema):
    camp = check_camp_access(camp_id, request.user)
    recipe = get_object_or_404(Recipe, id=data.recipe_id)
    meal = CampMeal.objects.create(
        camp=camp,
        recipe=recipe,
        meal_type=data.meal_type,
        date=data.date,
        override_people_count=data.override_people_count,
        serves_preference_id=data.serves_preference_id,
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


@router.put("/camps/{camp_id}/meals/{meal_id}/toggle-done", response=CampMealSchema)
def toggle_camp_meal_done(request, camp_id: str, meal_id: str):
    meal = get_object_or_404(CampMeal, camp_id=camp_id, id=meal_id)
    meal.is_done = not meal.is_done
    meal.save()
    return meal
