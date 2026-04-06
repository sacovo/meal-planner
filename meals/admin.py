from django import forms
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from django.db.models import QuerySet
from django.http import HttpRequest
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from invitations.adapters import get_invitations_adapter
from invitations.exceptions import (AlreadyAccepted, AlreadyInvited,
                                    UserRegisteredEmail)
from invitations.models import Invitation
from modeltranslation.admin import TabbedTranslationAdmin
from unfold.admin import ModelAdmin
from unfold.decorators import action
from unfold.forms import (AdminPasswordChangeForm, UserChangeForm,
                          UserCreationForm)
from unfold.widgets import UnfoldAdminEmailInputWidget

from content.tasks import (translate_all_ingredients, translate_all_recipes,
                           translate_ingredient, translate_recipe)

from .models import (Camp, CampMeal, DietaryPreference, GeneralCampItem,
                     Ingredient, IngredientUnitConversion, Inventory, Recipe,
                     RecipeIngredient, ShoppingList, ShoppingListItem)

admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.unregister(Invitation)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    # Forms loaded from `unfold.forms`
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


class InvitationAdminAddForm(forms.ModelForm):
    """Used when creating a new invitation — sends the invite email on save."""

    email = forms.EmailField(
        label=_("E-mail"),
        required=True,
        widget=UnfoldAdminEmailInputWidget(),
    )

    # request is injected by InvitationAdmin.get_form
    request = None

    def clean_email(self):
        email = self.cleaned_data["email"]
        email = get_invitations_adapter().clean_email(email)
        errors = {
            "already_invited": _("This e-mail address has already been invited."),
            "already_accepted": _(
                "This e-mail address has already accepted an invite."
            ),
            "email_in_use": _("An active user is using this e-mail address."),
        }
        try:
            if Invitation.objects.all_valid().filter(
                email__iexact=email, accepted=False
            ):
                raise AlreadyInvited
            elif Invitation.objects.filter(email__iexact=email, accepted=True):
                raise AlreadyAccepted
            from django.contrib.auth import get_user_model

            if get_user_model().objects.filter(email__iexact=email):
                raise UserRegisteredEmail
        except AlreadyInvited:
            raise forms.ValidationError(errors["already_invited"])
        except AlreadyAccepted:
            raise forms.ValidationError(errors["already_accepted"])
        except UserRegisteredEmail:
            raise forms.ValidationError(errors["email_in_use"])
        return email

    def save(self, *args, **kwargs):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        params = {"email": email}
        if cleaned_data.get("inviter"):
            params["inviter"] = cleaned_data.get("inviter")
        instance = Invitation.create(**params)
        instance.send_invitation(self.request)
        # Bind the already-persisted instance so the admin has a valid object,
        # and provide a no-op save_m2m so save_related() doesn't crash.
        self.instance = instance
        self.save_m2m = lambda: None
        return instance

    class Meta:
        model = Invitation
        fields = ("email", "inviter")


class InvitationAdminChangeForm(forms.ModelForm):
    """Used when editing an existing invitation — no email is (re)sent."""

    class Meta:
        model = Invitation
        fields = "__all__"


@admin.register(Invitation)
class InvitationAdmin(ModelAdmin):
    list_display = ("email", "sent", "accepted", "inviter")
    search_fields = ("email",)
    autocomplete_fields = ("inviter",)
    readonly_fields = ("sent", "accepted", "key")

    def get_form(self, request, obj=None, **kwargs):
        if obj:
            # Editing an existing invitation
            kwargs["form"] = InvitationAdminChangeForm
        else:
            # Creating a new invitation — inject request so send_invitation works
            kwargs["form"] = InvitationAdminAddForm
            InvitationAdminAddForm.request = request
        return super().get_form(request, obj, **kwargs)


@admin.register(Camp)
class CampAdmin(ModelAdmin):
    list_display = ("name", "start_date", "end_date", "default_people_count", "owner")
    search_fields = ("name",)


@admin.register(Ingredient)
class IngredientAdmin(ModelAdmin, TabbedTranslationAdmin):
    list_display = ("name", "category", "base_unit")
    list_filter = ("category",)
    search_fields = ("name",)
    actions_list = ["translate_all_ingredients_action"]
    actions = ["translate_ingredient_action"]
    actions_detail = ["translate_ingredient_single_action"]

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
    list_display = ("ingredient", "unit_name", "multiplier", "needs_review")
    list_filter = ("needs_review",)
    search_fields = ("ingredient__name", "unit_name")


@admin.register(Recipe)
class RecipeAdmin(ModelAdmin, TabbedTranslationAdmin):
    list_display = ("name", "default_portions", "owner")
    search_fields = ("name",)
    actions_list = ["translate_all_recipes_action"]
    actions_detail = ["translate_recipe_single_action"]
    actions = ["translate_action"]

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
