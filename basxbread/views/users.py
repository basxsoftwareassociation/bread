import htmlgenerator as hg
from django.contrib.auth.models import Group, User
from django.utils.translation import gettext_lazy as _

from basxbread import layout, utils

from . import BrowseView, EditView, ReadView


class UserBrowseView(BrowseView):
    model = User
    columns = [
        "is_active",
        "username",
        "first_name",
        "last_name",
        "email",
        "is_superuser",
        "last_login",
    ]
    rowactions = (
        BrowseView.editlink(),
        utils.Link(
            href=utils.LazyHref("password_reset", query={"email": hg.C("row").email}),
            label=hg.If(
                hg.C("row").email, _("Send password reset"), _("User has no email")
            ),
            iconname="mail--all",
            is_submit=True,
            attributes={"disabled": hg.If(hg.C("row").email, None, True)},
            formfields={"email": hg.C("row").email},
            confirm_text=hg.format(
                _("Are you sure you want to send a password reset email to {}?"),
                hg.C("row").email,
            ),
        ),
    )


class UserEditView(EditView):
    model = User
    fields = [
        "is_active",
        "username",
        "first_name",
        "last_name",
        "email",
        "is_superuser",
        "groups",
        "user_permissions",
    ]

    layout = hg.DIV(
        hg.DIV(
            layout.forms.FormField("is_active"),
            layout.forms.FormField("username"),
            layout.forms.FormField("first_name"),
            layout.forms.FormField("last_name"),
            layout.forms.FormField("email"),
            layout.forms.FormField("is_superuser"),
            style="width: 100%",
        ),
        hg.DIV(
            layout.forms.FormField("groups"),
            layout.forms.FormField("user_permissions"),
            style="width: 100%",
        ),
        style="display: flex",
    )


class UserReadView(ReadView):
    model = User
    fields = [
        "is_active",
        "username",
        "first_name",
        "last_name",
        "email",
        "is_superuser",
        "groups",
        "user_permissions",
    ]


class GroupBrowseView(BrowseView):
    model = Group


class GroupEditView(EditView):
    model = Group
