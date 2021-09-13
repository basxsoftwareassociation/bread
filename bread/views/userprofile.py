import htmlgenerator as hg
from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

from .. import layout
from ..utils import reverse
from . import EditView, ReadView

R = layout.grid.Row
C = layout.grid.Col


class UserProfileView(ReadView):
    model = get_user_model()

    def get_object(self):
        return self.request.user

    def get_layout(self):

        return hg.BaseElement(
            hg.H4(_("Manage Profile")),
            hg.DIV(
                layout.grid.Grid(
                    R(
                        C(
                            hg.H4(
                                layout.icon.Icon("user--profile"),
                                style="text-align: center",
                            ),
                            width=1,
                        ),
                        C(
                            hg.H4(
                                _("Personal Information"), style="margin-bottom: 3rem"
                            ),
                            profile_field("first_name"),
                            profile_field("last_name"),
                            layout.modal.modal_with_trigger(
                                layout.modal.Modal.with_ajax_content(
                                    _("Personal Information"),
                                    reverse(
                                        "userprofile.personal", query={"asajax": True}
                                    ),
                                    submitlabel=_("Save"),
                                ),
                                layout.button.Button,
                                _("Edit"),
                                buttontype="tertiary",
                                icon="edit",
                                style="margin-top: 1rem",
                            ),
                            width=7,
                        ),
                        C(
                            hg.H4(
                                layout.icon.Icon("password"),
                                style="text-align: center",
                            ),
                            width=1,
                        ),
                        C(
                            hg.H4(_("Login"), style="margin-bottom: 3rem"),
                            profile_field("username"),
                            profile_field("email"),
                            profile_field_password("password"),
                            layout.modal.modal_with_trigger(
                                layout.modal.Modal.with_ajax_content(
                                    _("Login"),
                                    reverse(
                                        "userprofile.login", query={"asajax": True}
                                    ),
                                    submitlabel=_("Save"),
                                ),
                                layout.button.Button,
                                _("Edit"),
                                buttontype="tertiary",
                                icon="edit",
                                style="margin-top: 1rem",
                            ),
                            width=7,
                        ),
                        style="margin-bottom: 2rem; margin-top: 2rem",
                    ),
                    R(
                        C(
                            hg.H4(
                                layout.icon.Icon("virtual-column--key"),
                                style="text-align: center",
                            ),
                            width=1,
                        ),
                        C(
                            hg.H4(_("Permissions")),
                            profile_field_checkbox("is_active"),
                            profile_field_checkbox("is_superuser"),
                            profile_field_checkbox("is_staff"),
                            layout.modal.modal_with_trigger(
                                layout.modal.Modal.with_ajax_content(
                                    _("Permissions"),
                                    reverse(
                                        "userprofile.permissions",
                                        query={"asajax": True},
                                    ),
                                    submitlabel=_("Save"),
                                ),
                                layout.button.Button,
                                _("Edit"),
                                buttontype="tertiary",
                                icon="edit",
                                style="margin-top: 1rem",
                                disabled=not self.request.user.is_superuser,
                            ),
                            width=7,
                        ),
                        C(width=1),
                        C(
                            hg.DIV(
                                layout.toggle.Toggle(
                                    _("Developer Mode"),
                                    _("Disabled"),
                                    _("Enabled"),
                                    help_text=hg.SPAN(
                                        _(
                                            "Warning: This is a dangerous option!",
                                        ),
                                        hg.BR(),
                                        _(
                                            "Enable it only if you know what you are doing!",
                                        ),
                                        style="color: red",
                                    ),
                                    widgetattributes={
                                        "checked": hg.C(
                                            f"request.session.{layout.DEVMODE_KEY}"
                                        ),
                                    },
                                    onclick=f"fetch('{reverse('devmode', kwargs={'enable': not self.request.session.get(layout.DEVMODE_KEY, False)})}').then((resp) => {{}}).then(() => location.reload(true)); return false;",
                                    style="margin-bottom: 0",
                                ),
                                style="align-self: flex-end",
                            ),
                            width=7,
                            style="display: flex; justify-content: flex-end",
                        ),
                        style="margin-bottom: 2rem; margin-top: 2rem",
                    ),
                ),
                _class="bx--tile",
            ),
        )


class EditPersonalDataView(EditView):
    model = get_user_model()
    fields = ["first_name", "last_name"]
    urlparams = {}

    def get_object(self):
        return self.request.user


class EditLoginView(EditView):
    model = get_user_model()
    fields = ["username", "email"]
    urlparams = {}

    def get_form_class(self, *args, **kwargs):
        class EditLoginForm(super().get_form_class(*args, **kwargs)):

            current_password = forms.CharField(
                label=_("Confirm changes with current password"),
                strip=False,
                widget=forms.PasswordInput(),
                help_text=_(
                    "Please enter your current password to confirm these changes"
                ),
            )

            def clean_current_password(self_inner):
                current_password = self_inner.cleaned_data["current_password"]
                if not self.request.user.check_password(current_password):
                    raise ValidationError(
                        _(
                            "Your current password was entered incorrectly. Please enter it again."
                        ),
                    )
                return current_password

        return EditLoginForm

    def get_form(self, *args, **kwargs):
        ret = super().get_form(*args, **kwargs)
        return ret

    def get_layout(self):
        ret = super().get_layout()
        ret.append(layout.form.FormField("current_password"))
        return ret

    def get_object(self):
        return self.request.user


class EditPermissionsView(EditView):
    model = get_user_model()
    fields = ["is_active", "is_superuser", "is_staff"]
    urlparams = {}

    def check_permissions(self, request):
        if not request.user.is_superuser:
            return HttpResponseForbidden()

    def get_object(self):
        return self.request.user


def profile_field(fieldname):
    return R(
        C(
            hg.SPAN(
                layout.ObjectFieldLabel(fieldname),
                style="font-weight: 700",
            ),
            width=4,
        ),
        C(layout.ObjectFieldValue(fieldname)),
        style="margin-bottom: 2rem",
    )


def profile_field_password(fieldname):
    ret = profile_field(fieldname)
    ret[1] = C(
        hg.BaseElement(
            "●●●●●●●●●●●●",
            hg.A(
                _("Request reset"),
                href=reverse("userprofile.password_reset"),
                style="float: right",
            ),
        )
    )
    return ret


def profile_field_checkbox(fieldname):
    return layout.checkbox.Checkbox(
        layout.ObjectFieldLabel(fieldname),
        disabled=True,
        widgetattributes={"checked": hg.C(f"object.{fieldname}")},
    )


def password_reset(request):
    """Automatically sends a password-reset email to the currently logged in user"""
    form = PasswordResetForm(data={"email": request.user.email})
    if form.is_valid():
        form.save(request=request)
        return redirect("password_reset_done")
    else:
        messages.error(request, form.errors)
        return redirect("userprofile")


def set_devmode(request, enable: str):
    request.session[layout.DEVMODE_KEY] = enable.lower() in ["true", "1"]
    messages.success(
        request,
        _("Enabled developer mode")
        if request.session[layout.DEVMODE_KEY]
        else _("Disabled developer mode"),
    )
    return HttpResponse("OK")
