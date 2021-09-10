import htmlgenerator as hg
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden
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
                            layout.modal.Modal.with_ajax_content(
                                _("Personal Information"),
                                reverse("userprofile.personal", query={"asajax": True}),
                                submitlabel=_("Save"),
                            ).attach_to_trigger(
                                layout.button.Button(
                                    _("Edit"),
                                    buttontype="tertiary",
                                    icon="edit",
                                    style="margin-top: 1rem",
                                )
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
                            profile_field("password", password=True),
                            profile_field("email"),
                            layout.modal.Modal.with_ajax_content(
                                _("Login"),
                                reverse("userprofile.login", query={"asajax": True}),
                                submitlabel=_("Save"),
                            ).attach_to_trigger(
                                layout.button.Button(
                                    _("Edit"),
                                    buttontype="tertiary",
                                    icon="edit",
                                    style="margin-top: 1rem",
                                )
                            ),
                            width=7,
                        ),
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
                            profile_field("is_active"),
                            profile_field("is_superuser"),
                            profile_field("is_staff"),
                            layout.modal.Modal.with_ajax_content(
                                _("Permissions"),
                                reverse(
                                    "userprofile.permissions", query={"asajax": True}
                                ),
                                submitlabel=_("Save"),
                            ).attach_to_trigger(
                                layout.button.Button(
                                    _("Edit"),
                                    buttontype="tertiary",
                                    icon="edit",
                                    style="margin-top: 1rem",
                                    disabled=not self.request.user.is_superuser,
                                )
                            ),
                            width=7,
                        ),
                    ),
                ),
                _class="bx--tile",
            ),
        )


class EditPersonalDataView(EditView):
    model = get_user_model()
    fields = ["first_name", "last_name"]

    def get_object(self):
        return self.request.user


class EditLoginView(EditView):
    model = get_user_model()
    fields = ["username", "email"]

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


def password_reset(request):
    """Automatically sends a password-reset email to the currently logged in user"""
    form = PasswordResetForm(data={"email": request.user.email})
    form.is_valid()
    form.save(request=request)
    return redirect("password_reset_done")


class EditPermissionsView(EditView):
    model = get_user_model()
    fields = ["is_active", "is_superuser", "is_staff"]

    def check_permissions(self, request):
        if not request.user.is_superuser:
            return HttpResponseForbidden()

    def get_object(self):
        return self.request.user


def profile_field(fieldname, password=False):
    fieldvalue = layout.ObjectFieldValue(fieldname) if not password else "●●●●●●●●●●●●"
    if password:
        fieldvalue = hg.BaseElement(
            fieldvalue,
            hg.A(
                _("Request reset"),
                href=reverse("userprofile.password_reset"),
                style="float: right",
            ),
        )
    return R(
        C(
            hg.SPAN(
                layout.ObjectFieldLabel(fieldname),
                style="font-weight: 700",
            ),
            width=4,
        ),
        C(fieldvalue),
        style="margin-bottom: 2rem",
    )
