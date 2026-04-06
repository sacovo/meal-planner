from django.contrib.auth import get_user_model
from django.db import models
from django.shortcuts import get_object_or_404
from ninja import Router

from meals.models import Camp, GeneralCampItem
from meals.schemas.camps import (
    CampCreateSchema,
    CampSchema,
    CampUpdateSchema,
    CollaboratorInviteSchema,
)
from meals.schemas.general_items import (
    GeneralCampItemCreateSchema,
    GeneralCampItemSchema,
)

router = Router()
User = get_user_model()


def check_camp_access(camp_id, user):
    """Verify the user is the owner or a collaborator of the camp."""
    return get_object_or_404(
        Camp,
        models.Q(id=camp_id) & (models.Q(owner=user) | models.Q(collaborators=user)),
    )


@router.get("/camps", response=list[CampSchema])
def list_camps(request):
    return Camp.objects.filter(
        models.Q(owner=request.user) | models.Q(collaborators=request.user)
    ).distinct()


@router.post("/camps", response=CampSchema)
def create_camp(request, data: CampCreateSchema):
    camp = Camp.objects.create(**data.dict(), owner=request.user)
    return camp


@router.get("/camps/{camp_id}", response=CampSchema)
def get_camp(request, camp_id: str):
    return get_object_or_404(
        Camp,
        models.Q(id=camp_id)
        & (models.Q(owner=request.user) | models.Q(collaborators=request.user)),
    )


@router.put("/camps/{camp_id}", response=CampSchema)
def update_camp(request, camp_id: str, data: CampUpdateSchema):
    camp = get_object_or_404(Camp, id=camp_id)
    if (
        camp.owner != request.user
        and not camp.collaborators.filter(id=request.user.id).exists()
    ):
        raise PermissionError("You don't have access to this camp")

    update_data = data.dict(exclude_unset=True)
    for attr, value in update_data.items():
        setattr(camp, attr, value)
    camp.save()
    return camp


@router.delete("/camps/{camp_id}")
def delete_camp(request, camp_id: str):
    camp = get_object_or_404(Camp, id=camp_id, owner=request.user)
    camp.delete()
    return {"success": True}


@router.post("/camps/{camp_id}/collaborators", response=CampSchema)
def invite_collaborator(request, camp_id: str, data: CollaboratorInviteSchema):
    camp = get_object_or_404(Camp, id=camp_id, owner=request.user)
    new_member = get_object_or_404(User, username=data.username)
    if new_member == camp.owner:
        raise ValueError("Cannot invite the owner")
    camp.collaborators.add(new_member)
    return camp


@router.delete("/camps/{camp_id}/collaborators/{username}")
def remove_collaborator(request, camp_id: str, username: str):
    camp = get_object_or_404(Camp, id=camp_id)
    # Only owner can remove others, but users can remove themselves
    if camp.owner != request.user and request.user.username != username:
        raise PermissionError("Only the owner can remove other collaborators")

    user_to_remove = get_object_or_404(User, username=username)
    camp.collaborators.remove(user_to_remove)
    return {"success": True}


# --- General Camp Items ---


@router.get("/camps/{camp_id}/general-items", response=list[GeneralCampItemSchema])
def list_camp_general_items(request, camp_id: str):
    check_camp_access(camp_id, request.user)
    return GeneralCampItem.objects.filter(camp_id=camp_id)


@router.post("/camps/{camp_id}/general-items", response=GeneralCampItemSchema)
def create_camp_general_item(request, camp_id: str, data: GeneralCampItemCreateSchema):
    camp = check_camp_access(camp_id, request.user)
    return GeneralCampItem.objects.create(camp=camp, **data.dict())


@router.delete("/camps/{camp_id}/general-items/{item_id}")
def delete_camp_general_item(request, camp_id: str, item_id: str):
    check_camp_access(camp_id, request.user)
    item = get_object_or_404(GeneralCampItem, camp_id=camp_id, id=item_id)
    item.delete()
    return {"success": True}
