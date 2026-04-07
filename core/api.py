from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.csrf import csrf_exempt
from ninja import Form, NinjaAPI, Schema
from ninja.security import django_auth
from ninja.throttling import AnonRateThrottle, AuthRateThrottle

import content.api
import core.admin  # noqa: F401 — registers User/Group/Invitation admin
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
api.add_router("/content", content.api.router)


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
def logout_view(request):
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
    first_name: str | None = None
    last_name: str | None = None


@api.get("/auth/account", response=AccountResponse, auth=None)
def account(request):
    if request.user.is_authenticated:
        return {
            "username": request.user.username,
            "is_staff": request.user.is_staff,
            "is_superuser": request.user.is_superuser,
            "full_name": request.user.get_full_name(),
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
        }
    return {"username": None, "is_staff": None, "is_superuser": None}


@api.post("/auth/profile", response=AccountResponse)
def update_profile(request, first_name: Form[str], last_name: Form[str]):
    user = request.user
    user.first_name = first_name
    user.last_name = last_name
    user.save()
    return {
        "username": user.username,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
        "full_name": user.get_full_name(),
        "first_name": user.first_name,
        "last_name": user.last_name,
    }


@api.post("/auth/password-reset-request", auth=None)
@csrf_exempt
def password_reset_request(request, email: Form[str]):
    try:
        user = User.objects.get(email=email)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        protocol = "https" if request.is_secure() else "http"
        domain = request.get_host()

        context = {
            "email": user.email,
            "domain": domain,
            "site_name": "Meal Planner",
            "uid": uid,
            "user": user,
            "token": token,
            "protocol": protocol,
        }

        subject = render_to_string(
            "registration/password_reset_subject.txt", context
        ).strip()
        email_body = render_to_string("registration/password_reset_email.html", context)

        send_mail(subject, email_body, settings.DEFAULT_FROM_EMAIL, [user.email])
    except User.DoesNotExist:
        # We don't want to leak if an email exists or not
        pass

    return {"success": True}


@api.post("/auth/password-reset-confirm", auth=None)
@csrf_exempt
def password_reset_confirm(
    request, uid: Form[str], token: Form[str], new_password: Form[str]
):
    try:
        uid_decoded = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=uid_decoded)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return api.create_response(
                request,
                data={"detail": e.messages},
                status=400,
            )
        user.set_password(new_password)
        user.save()
        return {"success": True}

    return api.create_response(
        request,
        data={"detail": "Invalid or expired token"},
        status=400,
    )


@api.get("/set-language/", auth=None)
def set_language(request, language: str):
    if language not in dict(settings.LANGUAGES):
        language = settings.LANGUAGE_CODE
    translation.activate(language)
    response = HttpResponse()
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language)
    return response


class CurrentUserStatusSchema(Schema):
    is_logged_in: bool
    username: str | None


@api.get("/meals/auth/me", auth=None, response=CurrentUserStatusSchema)
def get_current_user_status(request):
    if request.user.is_authenticated:
        return {"is_logged_in": True, "username": request.user.username}
    return {"is_logged_in": False}


@api.get(path="/messages/", auth=None, response={200: list[tuple[str, str]]})
def get_messages(request):
    return [
        (message.level_tag, message.message)
        for message in messages.get_messages(request)
    ]
