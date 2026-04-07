"""
Signal handlers for the meals app.

When a django-invitations invite is accepted:
  1. A User account is created (email used as username, unusable password).
  2. A "set your password" email is sent using the existing password-reset
     infrastructure so the user can reach /reset-password/:uid/:token in the
     frontend.
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.messages import add_message, constants as message_constants
from django.core.mail import send_mail
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from invitations.signals import invite_accepted


@receiver(invite_accepted)
def create_user_on_invite_accepted(sender, email, request, **kwargs):
    """
    Create a User for the accepted invitation and send them a
    'set your password' email so they can log in.

    If a user with that email already exists (e.g. the invite was resent)
    we still send the password-set email so they can recover access.
    """
    # Derive a username from the email (max 150 chars, Django's limit).
    username = email[:150]

    user, created = User.objects.get_or_create(
        email=email,
        defaults={"username": username},
    )

    if created:
        user.set_unusable_password()
        user.save()

    # Build a password-reset link pointing at the existing frontend route:
    # /reset-password/:uid/:token
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    protocol = "https" if (request and request.is_secure()) else "http"
    domain = (
        request.get_host()
        if request
        else settings.ALLOWED_HOSTS[0]
        if settings.ALLOWED_HOSTS
        else "localhost"
    )

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
        "registration/invite_set_password_subject.txt", context
    ).strip()
    body = render_to_string("registration/invite_set_password_email.html", context)

    add_message(
        request,
        message_constants.SUCCESS,
        "Du erhältst in Kürze eine E-Mail um dein Passwort festzulegen.",
    )

    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [email])
