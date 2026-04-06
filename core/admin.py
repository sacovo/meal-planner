"""Admin registrations for User, Group, and Invitation models.

These are framework-level admin customizations, not domain-specific,
so they live in core/ rather than in any specific app.
"""

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from django.utils.translation import gettext_lazy as _
from invitations.adapters import get_invitations_adapter
from invitations.exceptions import AlreadyAccepted, AlreadyInvited, UserRegisteredEmail
from invitations.models import Invitation
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold.widgets import UnfoldAdminEmailInputWidget

admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.unregister(Invitation)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
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
            kwargs["form"] = InvitationAdminChangeForm
        else:
            kwargs["form"] = InvitationAdminAddForm
            InvitationAdminAddForm.request = request
        return super().get_form(request, obj, **kwargs)
