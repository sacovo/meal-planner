from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from ninja import Router

from meals.models import (
    DietaryPreference,
    Recipe,
    RecipeIngredient,
)
from meals.schemas.camps import CollaboratorInviteSchema
from meals.schemas.ingredients import (
    RecipeIngredientCreateOrMapSchema,
    RecipeIngredientSchema,
    RecipeIngredientUpdateSchema,
)
from meals.schemas.meals import DietaryPreferenceSchema
from meals.schemas.recipes import (
    RecipeCreateSchema,
    RecipeImportRequestSchema,
    RecipePaginatedSchema,
    RecipeSchema,
    RecipeUpdateSchema,
)
from meals.services import add_ingredient_to_recipe
from meals.tasks import import_recipe_ai_task

router = Router()
User = get_user_model()


def check_recipe_edit_access(recipe, user):
    """Verify the user is the owner or a collaborator of the recipe."""
    if recipe.owner != user and not recipe.collaborators.filter(id=user.id).exists():
        raise PermissionError("You don't have permission to edit this recipe")
    return recipe


@router.get("/recipes", response=RecipePaginatedSchema)
def list_recipes(
    request, page: int = 1, q: str = None, tags: str = None, preference_id: int = None
):
    page_size = 20
    offset = (page - 1) * page_size
    qs = Recipe.objects.all().order_by("name")
    if q:
        qs = qs.filter(name__icontains=q)
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        for t in tag_list:
            qs = qs.filter(tags__contains=t)
    if preference_id:
        qs = qs.filter(preferences__id=preference_id)

    count = qs.count()
    items = list(qs[offset : offset + page_size])

    return {"items": items, "count": count}


@router.post("/recipes", response=RecipeSchema)
def create_recipe(request, data: RecipeCreateSchema):
    recipe_data = data.dict(exclude={"preference_ids"})
    recipe = Recipe.objects.create(**recipe_data, owner=request.user)
    if data.preference_ids:
        recipe.preferences.set(data.preference_ids)
    return recipe


@router.post("/recipes/import", response=RecipeSchema)
def import_recipe(request, data: RecipeImportRequestSchema):
    recipe = Recipe.objects.create(
        name="Importing...", is_importing=True, owner=request.user
    )
    import_recipe_ai_task.delay(recipe.id, data.raw_text)
    return recipe


@router.get("/recipes/{recipe_id}", response=RecipeSchema)
def get_recipe(request, recipe_id: str):
    return get_object_or_404(Recipe, id=recipe_id)


@router.put("/recipes/{recipe_id}", response=RecipeSchema)
def update_recipe(request, recipe_id: str, data: RecipeUpdateSchema):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    check_recipe_edit_access(recipe, request.user)
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
    return RecipeIngredient.objects.filter(recipe_id=recipe_id).select_related(
        "ingredient"
    )


@router.post("/recipes/{recipe_id}/ingredients", response=RecipeIngredientSchema)
def add_recipe_ingredient(
    request, recipe_id: str, data: RecipeIngredientCreateOrMapSchema
):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    check_recipe_edit_access(recipe, request.user)
    return add_ingredient_to_recipe(
        recipe, data.ingredient_name, data.amount, data.unit
    )


@router.put(
    "/recipes/{recipe_id}/ingredients/{ingredient_id}", response=RecipeIngredientSchema
)
def update_recipe_ingredient(
    request, recipe_id: str, ingredient_id: str, data: RecipeIngredientUpdateSchema
):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    check_recipe_edit_access(recipe, request.user)
    ri = get_object_or_404(RecipeIngredient, recipe_id=recipe_id, id=ingredient_id)
    ri.amount = data.amount
    ri.unit = data.unit.lower().strip()
    ri.save()
    return ri


@router.delete("/recipes/{recipe_id}/ingredients/{ingredient_id}")
def delete_recipe_ingredient(request, recipe_id: str, ingredient_id: str):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    check_recipe_edit_access(recipe, request.user)
    ri = get_object_or_404(RecipeIngredient, recipe_id=recipe_id, id=ingredient_id)
    ri.delete()
    return {"success": True}


@router.post("/recipes/{recipe_id}/collaborators", response=RecipeSchema)
def invite_recipe_collaborator(request, recipe_id: str, data: CollaboratorInviteSchema):
    recipe = get_object_or_404(Recipe, id=recipe_id, owner=request.user)
    new_member = get_object_or_404(User, username=data.username)
    if new_member == recipe.owner:
        raise ValueError("Cannot invite the owner")
    recipe.collaborators.add(new_member)
    return recipe


@router.delete("/recipes/{recipe_id}/collaborators/{username}")
def remove_recipe_collaborator(request, recipe_id: str, username: str):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    # Only owner can remove others, but users can remove themselves
    if recipe.owner != request.user and request.user.username != username:
        raise PermissionError("Only the owner can remove other collaborators")

    user_to_remove = get_object_or_404(User, username=username)
    recipe.collaborators.remove(user_to_remove)
    return {"success": True}


@router.get("/preferences", response=list[DietaryPreferenceSchema])
def list_preferences(request):
    return DietaryPreference.objects.all()
