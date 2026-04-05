from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.utils import translation
from django.views.decorators.csrf import csrf_exempt
from ninja import Form, NinjaAPI, Schema
from ninja.security import django_auth
from ninja.throttling import AnonRateThrottle, AuthRateThrottle
from sesame.utils import get_user

import meals.api

api = NinjaAPI(
    auth=django_auth,
    throttle=[
        AnonRateThrottle("50/s"),
        AuthRateThrottle("200/s"),
    ],
    version="1.0.0",
)

api.add_router("/meals", meals.api.router)


@api.exception_handler(ValidationError)
def validation_exception_handler(request, exc):
    return api.create_response(
        request,
        data={
            "detail": exc.message_dict if hasattr(exc, "message_dict") else exc.messages
        },
        status=400,
    )


@api.exception_handler(ValueError)
def value_exception_handler(request, exc):
    return api.create_response(
        request,
        data={"detail": str(exc)},
        status=400,
    )


@api.exception_handler(PermissionError)
def permission_exception_handler(request, exc):
    return api.create_response(
        request,
        data={"detail": str(exc)},
        status=403,
    )


class LoginResponse(Schema):
    success: bool
    error: str | None = None


AUTH_RESPONSE = {
    200: LoginResponse,
    401: LoginResponse,
}


@api.post("/auth/login", auth=None, response=AUTH_RESPONSE)
def login_view(request, username: Form[str], password: Form[str]):
    if (
        user := authenticate(request, username=username, password=password)
    ) is not None:
        login(request, user)
        return {"success": True}
    return api.create_response(
        request,
        data=LoginResponse(success=False, error="Invalid credentials"),
        status=401,
    )


@api.post("/auth/logout", auth=django_auth)
@csrf_exempt
def logout_view(request, forget: Form[bool] = False):
    if forget:
        print("Revoking trusted agent")
        django_agent_trust.revoke_agent(request)
    logout(request)
    return {"success": True}


@api.post("/auth/set-password", response=AUTH_RESPONSE)
def change_password_view(request, old_password: Form[str], new_password: Form[str]):
    user = request.user
    if not user.check_password(old_password):
        return api.create_response(
            request,
            data=LoginResponse(success=False, error="Old password is incorrect"),
            status=401,
        )
    if old_password == new_password:
        return api.create_response(
            request,
            data=LoginResponse(
                success=False, error="New password must be different from old password"
            ),
            status=400,
        )
    try:
        validate_password(new_password, user)
    except ValidationError as e:
        return api.create_response(
            request,
            data=[err.message for err in e.error_list],
            status=400,
        )
    with transaction.atomic():
        user.set_password(new_password)
        user.save()
    return {"success": True}


class AccountResponse(Schema):
    username: str | None
    is_staff: bool | None = None
    is_superuser: bool | None = None
    verified: bool | None = None
    otp: bool | None = None
    is_trusted: bool | None = None
    full_name: str | None = None


@api.post("/auth/account", response=AccountResponse, auth=None)
def account(request):
    if request.user.is_authenticated:
        return {
            "username": request.user.username,
            "is_staff": request.user.is_staff,
            "is_superuser": request.user.is_superuser,
            "full_name": request.user.get_full_name(),
        }
    return {"username": None, "is_staff": None, "is_superuser": None}


@api.get("/set-language/", auth=None)
def set_language(request, language: str):
    if language not in dict(settings.LANGUAGES):
        language = settings.LANGUAGE_CODE
    translation.activate(language)
    response = HttpResponse()
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language)
    return response
