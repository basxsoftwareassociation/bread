import htmlgenerator as hg
from django.conf import settings
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetView,
)
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .. import layout
from .util import BreadView


def auth_page(content, submitname, show_cancelbutton=False):
    return hg.DIV(
        hg.DIV(
            hg.H3(hg.C("pagetitle")),
            hg.FORM(id="cancelform", action=reverse("login")),
            content,
            hg.DIV(
                hg.If(
                    show_cancelbutton,
                    layout.button.Button(
                        _("Cancel"),
                        buttontype="ghost",
                        form="cancelform",
                        type="submit",
                        style="width: 50%",
                    ),
                    hg.DIV(style="width: 50%"),
                ),
                layout.button.Button(
                    submitname, type="submit", form="authform", style="width: 50%"
                ),
                style="margin: 1rem -1rem -1rem -1rem; display: flex; height: 64px",
            ),
            style="margin: auto; width: 25rem",
            _class="bx--tile",
        ),
        style="background-image: linear-gradient(#0F62FE, #0008C9); position: absolute; left: 0; top: 0; bottom: 0; right: 0; display: flex; flex-direction: column",
    )


class BreadLoginView(BreadView, LoginView):
    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        return super().get(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        return {
            **super().get_context_data(*args, **kwargs),
            "pagetitle": _("Login"),
        }

    def get_layout(self):
        return auth_page(
            layout.forms.Form(
                hg.C("form"),
                hg.A(
                    _("Lost password?"),
                    href=reverse("password_reset"),
                    style="display: block; text-align: right; font-size: 0.75rem",
                ),
                layout.forms.FormField(
                    fieldname="username",
                    form="form",
                    inputelement_attrs={"_class": "field-02-background"},
                    style="width: 100%",
                ),
                layout.forms.FormField(
                    fieldname="password",
                    form="form",
                    inputelement_attrs={"_class": "field-02-background"},
                    style="width: 100%",
                ),
                id="authform",
            ),
            _("Login"),
        )

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["username"].widget.attrs["autofocus"] = True
        return form


class BreadLogoutView(BreadView, LogoutView):
    def get(self, *args, **kwargs):
        super().get(*args, **kwargs)
        return redirect("login")

    def get_context_data(self, *args, **kwargs):
        return {
            **super().get_context_data(*args, **kwargs),
            "pagetitle": _("Logout"),
        }

    def get_layout(self):
        return hg.DIV(_("Logged out"))


class BreadPasswordResetView(BreadView, PasswordResetView):
    def get_context_data(self, *args, **kwargs):
        return {
            **super().get_context_data(*args, **kwargs),
            "pagetitle": _("Password reset"),
        }

    def get_layout(self):
        return auth_page(
            layout.forms.Form(
                hg.C("form"),
                hg.A(
                    _("Lost password?"),
                    href=reverse("password_reset"),
                    style="float: right; font-size: 0.75rem",
                ),
                layout.forms.FormField(
                    "email",
                    inputelement_attrs={
                        "_class": "field-02-background",
                    },
                    style="width: 100%",
                ),
                id="authform",
            ),
            _("Reset password"),
            show_cancelbutton=True,
        )


class BreadPasswordResetDoneView(BreadView, PasswordResetView):
    def get_context_data(self, *args, **kwargs):
        return {
            **super().get_context_data(*args, **kwargs),
            "pagetitle": _("Password reset"),
        }

    def get_layout(self):
        return auth_page(
            hg.BaseElement(
                layout.notification.InlineNotification(
                    _("Email instructions sent"),
                    _(
                        "If the email address provided exists, you will shortly receive an email containing recovery instructions."
                    ),
                    kind="success",
                    lowcontrast=True,
                    style="margin-bottom: 4rem",
                ),
                hg.FORM(action=reverse("login"), id="authform"),
            ),
            _("Back to Login"),
        )


class BreadPasswordResetConfirmView(BreadView, PasswordResetConfirmView):
    def get_context_data(self, *args, **kwargs):
        return {
            **super().get_context_data(*args, **kwargs),
            "pagetitle": _("Change password"),
        }

    def get_layout(self):
        return hg.If(
            hg.C("validlink"),
            auth_page(
                layout.forms.Form(
                    hg.C("form"),
                    layout.forms.FormField(
                        "new_password1",
                        inputelement_attrs={"_class": "field-02-background"},
                        style="width: 100%",
                    ),
                    layout.forms.FormField(
                        "new_password2",
                        inputelement_attrs={"_class": "field-02-background"},
                    ),
                    id="authform",
                ),
                _("Change password"),
            ),
            auth_page(
                hg.BaseElement(
                    hg.FORM(id="authform", action=reverse("login")),
                    layout.notification.InlineNotification(
                        _("Invalid password reset link"),
                        _(
                            "The password reset link was invalid, possibly because it has already been used. Please request a new password reset."
                        ),
                        kind="error",
                        lowcontrast=True,
                        style="margin-bottom: 4rem",
                    ),
                ),
                _("Back to Login"),
            ),
        )


class BreadPasswordResetCompleteView(BreadView, PasswordResetCompleteView):
    def get_context_data(self, *args, **kwargs):
        return {
            **super().get_context_data(*args, **kwargs),
            "pagetitle": _("Change password"),
        }

    def get_layout(self):
        return auth_page(
            hg.BaseElement(
                layout.notification.InlineNotification(
                    _("Password successfully changed"),
                    _("Please login again"),
                    kind="success",
                    lowcontrast=True,
                    style="margin-bottom: 4rem",
                ),
                hg.FORM(action=reverse("login"), id="authform"),
            ),
            _("Back to Login"),
        )
