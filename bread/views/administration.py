import os
import re
import subprocess  # nosec because we covered everything
from io import StringIO
from typing import Union

import htmlgenerator as hg
import pkg_resources
import requests
from django import forms
from django.conf import settings
from django.contrib import auth, contenttypes, messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.core import management
from django.core.exceptions import ValidationError
from django.db import connection
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from django_celery_results.models import TaskResult
from htmlgenerator import Lazy

from bread import layout
from bread.layout import ObjectFieldLabel, ObjectFieldValue
from bread.layout.components import tabs
from bread.layout.components.button import Button
from bread.layout.components.datatable import DataTable, DataTableColumn
from bread.layout.components.forms import Form, FormField
from bread.layout.components.forms.menu_picker import MenuPicker
from bread.layout.components.modal import modal_with_trigger
from bread.utils import ModelHref
from bread.views import AddView, BrowseView, EditView
from bread.views.read import ReadView

from ..layout.components.icon import Icon
from ..utils import Link, aslayout

R = layout.grid.Row
C = layout.grid.Col
F = layout.forms.FormField

TR = layout.datatable.DataTable.row
TD = layout.datatable.DataTableColumn


DjangoUserModel = get_user_model()


@user_passes_test(lambda user: user.is_superuser)
@aslayout
def maintenancesettings(request):
    # Add the view's header
    ret = layout.grid.Grid(R(C(hg.H3(_("Maintenance")))), gutter=False)

    # Add the Package Information modal
    ret.append(
        R(
            C(
                hg.H4(_("Packages")),
                maintainance_package_layout(request),
            ),
            C(
                hg.H4(_("Optimize database")),
                maintenance_database_optimization(request),
                hg.H4(_("Rebuild search index"), _style="margin-top: 3rem;"),
                maintenance_search_reindex(request),
            ),
        )
    )

    return ret


class UserBrowseView(BrowseView):
    columns = [
        "id",
        DataTableColumn(
            hg.DIV(_("Active"), style="text-align: center;"),
            hg.DIV(
                hg.If(
                    hg.C("row").is_active,
                    Icon("checkmark--filled", size="16"),
                    Icon("misuse--outline", size="16"),
                ),
                style="text-align: center;",
            ),
        ),
        DataTableColumn(
            hg.DIV(_("Staff"), style="text-align: center;"),
            hg.DIV(
                hg.If(
                    hg.C("row").is_staff,
                    Icon("checkmark--filled", size="16"),
                    Icon("misuse--outline", size="16"),
                ),
                style="text-align: center;",
            ),
        ),
        DataTableColumn(
            hg.DIV(_("Superuser"), style="text-align: center;"),
            hg.DIV(
                hg.If(
                    hg.C("row").is_superuser,
                    Icon("checkmark--filled", size="16"),
                    Icon("misuse--outline", size="16"),
                ),
                style="text-align: center;",
            ),
        ),
        DataTableColumn(_("Username"), hg.C("row.username")),
        DataTableColumn(_("First Name"), hg.C("row.first_name")),
        DataTableColumn(_("Last Name"), hg.C("row.last_name")),
        DataTableColumn(
            _("Groups"),
            hg.BaseElement(
                hg.Iterator(
                    hg.C("row").groups.values(),
                    "usergroup",
                    hg.If(
                        hg.F(lambda context: context["usergroup_index"] < 3),
                        hg.DIV(
                            hg.C("usergroup.name"),
                            style="margin-bottom: 0.25rem;",  # for groups that may have a long name
                        ),
                    ),
                ),
                hg.If(
                    hg.F(lambda context: len(context["row"].groups.values()) >= 3),
                    hg.SPAN(
                        hg.F(
                            lambda context: f"... and {len(context['row'].groups.values()) - 3} more"
                        ),
                        style="font-style: italic;" "font-weight: bold;",
                    ),
                ),
            ),
        ),
        DataTableColumn(
            _("Permissions"),
            hg.BaseElement(
                hg.Iterator(
                    hg.C("row").user_permissions.values(),
                    "usergroup",
                    hg.If(
                        hg.F(lambda context: context["usergroup_index"] < 3),
                        hg.DIV(
                            hg.F(
                                lambda c: contenttypes.models.ContentType.objects.get(
                                    pk=c["usergroup"]["content_type_id"]
                                ).app_label
                            ),
                            ".",
                            hg.C("usergroup.codename"),
                            style="margin-bottom: 0.25rem;",  # for ones that may have a long name
                        ),
                    ),
                ),
                hg.If(
                    hg.F(
                        lambda context: len(context["row"].user_permissions.values())
                        >= 3
                    ),
                    hg.SPAN(
                        hg.F(
                            lambda context: f"... and {len(context['row'].user_permissions.values()) - 3} more"
                        ),
                        style="font-style: italic;" "font-weight: bold;",
                    ),
                ),
            ),
        ),
    ]
    title = "Users"
    rowclickaction = BrowseView.gen_rowclickaction("read")
    viewstate_sessionkey = "adminusermanagement"

    class FilterForm(forms.Form):
        status = forms.MultipleChoiceField(
            choices=[("active", _("Active")), ("inactive", _("Inactive"))],
            widget=forms.CheckboxSelectMultiple,
            required=False,
        )
        types = forms.MultipleChoiceField(
            choices=[("superuser", _("Superuser")), ("staff", _("Staff"))],
            widget=forms.CheckboxSelectMultiple,
            required=False,
        )
        groups = forms.ModelMultipleChoiceField(
            auth.models.Group.objects.all(),
            widget=forms.SelectMultiple,
            required=False,
        )
        permissions = forms.ModelMultipleChoiceField(
            auth.models.Permission.objects.all(),
            widget=forms.SelectMultiple,
            required=False,
        )

    def _filterform(self):
        return self.FilterForm({"status": ["active"], **self.request.GET})

    def get_queryset(self):
        form = self._filterform()
        qs = super().get_queryset()

        q = Q()

        if form.is_valid():
            filter_conds = (
                # (field name, field value, Q object)
                *(
                    (
                        ("status", val, Q(is_active=qval))
                        for val, qval in (("active", True), ("inactive", False))
                    )
                    if any(
                        status not in form.cleaned_data["status"]
                        for status in ("active", "inactive")
                    )
                    else tuple()
                ),
                *(
                    ("types", val, Q(**{f"is_{val}": True}))
                    for val in ("superuser", "staff")
                ),
            )
            for name, val, qcond in filter_conds:
                if val in form.cleaned_data[name]:
                    q &= qcond

            # filtering groups and permissions
            group_pks = [group["id"] for group in form.cleaned_data["groups"].values()]
            permission_pks = [
                permission["id"]
                for permission in form.cleaned_data["permissions"].values()
            ]

            if group_pks:
                q &= Q(groups__pk__in=group_pks)
            if permission_pks:
                q &= Q(user_permissions__pk__in=permission_pks)

        print(q)
        print(qs)

        qs = qs.filter(q)
        return qs

    def get_settingspanel(self):
        return hg.DIV(
            layout.forms.Form(
                self._filterform(),
                hg.DIV(
                    hg.DIV(
                        hg.DIV(
                            hg.DIV(
                                layout.forms.FormField(
                                    "types",
                                ),
                                layout.forms.FormField("status"),
                                style="margin-right: 16px",
                            ),
                            hg.DIV(
                                layout.forms.FormField(
                                    "groups",
                                ),
                                layout.forms.FormField(
                                    "permissions",
                                ),
                                style="margin-right: 16px",
                            ),
                            style="display: flex",
                        ),
                    ),
                    style="display: flex; max-height: 50vh; padding: 24px 32px 0 32px",
                ),
                hg.DIV(
                    layout.button.Button(
                        _("Cancel"),
                        buttontype="ghost",
                        onclick="this.parentElement.parentElement.parentElement.parentElement.parentElement.style.display = 'none'",
                    ),
                    layout.button.Button.fromlink(
                        Link(
                            label=_("Reset"),
                            href=self.request.path + "?reset=1",
                            iconname=None,
                        ),
                        buttontype="secondary",
                    ),
                    layout.button.Button(
                        pgettext_lazy("apply filter", "Filter"),
                        type="submit",
                    ),
                    style="display: flex; justify-content: flex-end; margin-top: 24px",
                    _class="bx--modal-footer",
                ),
                method="GET",
            ),
            style="background-color: #fff",
            onclick="updateCheckboxCounter(this)",
        )


class UserAddView(AddView):
    model = DjangoUserModel
    fields = [
        "is_active",
        "username",
        "password1",
        "password2",
        "first_name",
        "last_name",
        "email",
        "is_superuser",
        "is_staff",
    ]

    class UserAddForm(UserCreationForm):
        """Based on Django User model"""

        class Meta:
            model = DjangoUserModel
            fields = (
                "username",
                "first_name",
                "last_name",
                "email",
                "is_superuser",
                "is_staff",
                "is_active",
                "groups",
                "user_permissions",
            )
            field_classes = {"username": auth.forms.UsernameField}

        first_name = forms.CharField(
            label=_("first name"), max_length=150, required=False
        )
        last_name = forms.CharField(
            label=_("last name"), max_length=150, required=False
        )
        email = forms.EmailField(label=_("email"), required=False)
        is_superuser = forms.BooleanField(
            label=_("Is superuser?"),
            help_text=_(
                "Designates that this user has all permissions without "
                "explicitly assigning them."
            ),
            required=False,
        )
        is_staff = forms.BooleanField(
            label=_("Is staff?"),
            help_text=_("Designates whether the user can log into this admin site."),
            required=False,
        )
        is_active = forms.BooleanField(
            label=_("Is active?"),
            help_text=_(
                "Designates whether this user should be treated as active. "
                "Unselect this instead of deleting accounts."
            ),
            initial=True,
            required=False,
        )
        groups = forms.ModelMultipleChoiceField(
            auth.models.Group.objects.all(),
            label=_("groups"),
            help_text=_(
                "The groups this user belongs to. A user will get all permissions "
                "granted to each of their groups."
            ),
            required=False,
        )
        user_permissions = forms.ModelMultipleChoiceField(
            auth.models.Permission.objects.all(),
            label=_("permissions"),
            help_text=_("Specific permissions for this user."),
            required=False,
        )

    form = UserAddForm()

    def get_layout(self):
        return layout.grid.Grid(
            layout.components.forms.Form(
                self.form,
                *(R(C(F(field))) for field in self.fields),
                *(
                    R(C(F(field, widgetclass=MenuPicker)))
                    for field in ("groups", "user_permissions")
                ),
                R(C(layout.forms.helpers.Submit(_("Create this user")))),
            )
        )


class GroupBrowseView(BrowseView):
    columns = [
        "id",
        "name",
        DataTableColumn(
            _("Members"),
            hg.BaseElement(
                hg.Iterator(
                    hg.C("row").user_set.values(),
                    "member",
                    hg.If(
                        hg.F(lambda context: context["member_index"] < 3),
                        hg.DIV(
                            hg.C("member.first_name"),
                            " ",
                            hg.C("member.last_name"),
                            " (",
                            hg.C("member.username"),
                            ")",
                            style="margin-bottom: 0.25rem;",  # for ones that may have a long name
                        ),
                    ),
                ),
                hg.If(
                    hg.F(lambda context: len(context["row"].user_set.values()) >= 3),
                    hg.SPAN(
                        hg.F(
                            lambda context: f"... and {len(context['row'].permissions.values()) - 3} more"
                        ),
                        style="font-style: italic;" "font-weight: bold;",
                    ),
                ),
            ),
        ),
        DataTableColumn(
            _("Permissions"),
            hg.BaseElement(
                hg.Iterator(
                    hg.C("row").permissions.values(),
                    "permission",
                    hg.If(
                        hg.F(lambda context: context["permission_index"] < 3),
                        hg.DIV(
                            hg.F(
                                lambda c: contenttypes.models.ContentType.objects.get(
                                    pk=c["permission"]["content_type_id"]
                                ).app_label
                            ),
                            ".",
                            hg.C("permission.codename"),
                            style="margin-bottom: 0.25rem;",  # for ones that may have a long name
                        ),
                    ),
                ),
                hg.If(
                    hg.F(lambda context: len(context["row"].permissions.values()) >= 3),
                    hg.SPAN(
                        hg.F(
                            lambda context: f"... and {len(context['row'].permissions.values()) - 3} more"
                        ),
                        style="font-style: italic;" "font-weight: bold;",
                    ),
                ),
            ),
        ),
    ]
    title = "Groups"
    rowclickaction = BrowseView.gen_rowclickaction("read")
    viewstate_sessionkey = "adminusermanagement"

    class FilterForm(forms.Form):
        members = forms.ModelMultipleChoiceField(
            DjangoUserModel.objects.all(),
            label=_("members"),
            help_text=_("Specific users that belong to this group."),
            required=False,
        )
        permissions = forms.ModelMultipleChoiceField(
            auth.models.Permission.objects.all(),
            label=_("permissions"),
            help_text=_("Specific permissions for this group."),
            required=False,
        )

    def _filterform(self):
        return self.FilterForm(self.request.GET)

    def get_queryset(self):
        form = self._filterform()
        qs = super().get_queryset()

        q = Q()

        if form.is_valid():
            user_pks = [user["id"] for user in form.cleaned_data["members"].values()]
            permission_pks = [
                permission["id"]
                for permission in form.cleaned_data["permissions"].values()
            ]

            if user_pks:
                q &= Q(user__pk__in=user_pks)
            if permission_pks:
                q &= Q(permissions__pk__in=permission_pks)

        qs = qs.filter(q)
        return qs

    def get_settingspanel(self):
        return hg.DIV(
            layout.forms.Form(
                self._filterform(),
                hg.DIV(
                    hg.DIV(
                        hg.DIV(
                            hg.DIV(
                                layout.forms.FormField(
                                    "members",
                                ),
                                layout.forms.FormField(
                                    "permissions",
                                ),
                                style="margin-right: 16px",
                            ),
                            style="display: flex",
                        ),
                    ),
                    style="display: flex; max-height: 50vh; padding: 24px 32px 0 32px",
                ),
                hg.DIV(
                    layout.button.Button(
                        _("Cancel"),
                        buttontype="ghost",
                        onclick="this.parentElement.parentElement.parentElement.parentElement.parentElement.style.display = 'none'",
                    ),
                    layout.button.Button.fromlink(
                        Link(
                            label=_("Reset"),
                            href=self.request.path + "?reset=1",
                            iconname=None,
                        ),
                        buttontype="secondary",
                    ),
                    layout.button.Button(
                        pgettext_lazy("apply filter", "Filter"),
                        type="submit",
                    ),
                    style="display: flex; justify-content: flex-end; margin-top: 24px",
                    _class="bx--modal-footer",
                ),
                method="GET",
            ),
            style="background-color: #fff",
            onclick="updateCheckboxCounter(this)",
        )


class GroupAddView(AddView):
    model = auth.models.Group
    fields = ["name", "permissions"]

    class GroupAddForm(forms.Form):
        name = forms.CharField(
            label=_("name"),
            max_length=150,
            help_text=_("The group name must be unique."),
        )
        user_set = forms.ModelMultipleChoiceField(
            DjangoUserModel.objects.all(),
            label=_("members"),
            required=False,
        )
        permissions = forms.ModelMultipleChoiceField(
            auth.models.Permission.objects.all(),
            label=_("permissions"),
            required=False,
        )

    def post(self, request, *args, **kwargs):
        # need to be run before proceeding to anything else
        redirect = super().post(request, *args, **kwargs)

        form = self.GroupAddForm(request.POST)
        group = self.object

        if form.is_valid():
            for user in form.cleaned_data["user_set"].values():
                group.user_set.add(user["id"])
            group.save()

        return redirect

    def get_layout(self):
        form = self.GroupAddForm()
        return layout.grid.Grid(
            layout.components.forms.Form(
                form,
                R(C(F("name"))),
                *(
                    R(C(F(field, widgetclass=MenuPicker)))
                    for field in ("user_set", "permissions")
                ),
                R(C(layout.forms.helpers.Submit(_("Create this group")))),
            )
        )


class GroupReadView(ReadView):
    model = auth.models.Group
    fields = [
        "id",
        "name",
        "permissions",
    ]

    def get_layout(self):
        return hg.BaseElement(
            hg.H3(
                hg.SPAN(self.object),
                edituser_toolbar(self.request),
            ),
            layout.tile.Tile(
                layout.grid.Grid(
                    R(C(hg.H3(_("Information")))),
                    R(
                        C(
                            *(
                                display_label_and_value(
                                    ObjectFieldLabel(field), ObjectFieldValue(field)
                                )
                                for field in self.fields[:-1]
                            ),
                        ),
                    ),
                    R(
                        C(
                            open_modal_popup_button(
                                self.object,
                                self.model,
                                "ajax_edit_group_info",
                                "md",
                                _("Rename the group"),
                            ),
                        )
                    ),
                ),
                style="padding: 3rem; margin-bottom: 2rem;",
            ),
            layout.tile.Tile(
                layout.grid.Grid(
                    R(C(hg.H3(_("Members")))),
                    R(
                        C(
                            DataTable(
                                columns=[
                                    DataTableColumn(_("ID"), hg.C("row.id")),
                                    DataTableColumn(
                                        _("Username"), hg.C("row.username")
                                    ),
                                    DataTableColumn(
                                        _("First Name"), hg.C("row.first_name")
                                    ),
                                    DataTableColumn(
                                        _("Last Name"), hg.C("row.last_name")
                                    ),
                                    DataTableColumn(
                                        "",
                                        hg.F(
                                            lambda context: Button.from_link(
                                                Link(
                                                    label=context["row"]["username"],
                                                    href=reverse(
                                                        "auth.user.read",
                                                        kwargs={
                                                            "pk": context["row"]["id"]
                                                        },
                                                    ),
                                                ),
                                                buttontype="ghost",
                                                icon="link",
                                                notext=True,
                                            )
                                        ),
                                    ),
                                ],
                                row_iterator=[
                                    {
                                        "id": row["id"],
                                        "username": row["username"],
                                        "first_name": row["first_name"],
                                        "last_name": row["last_name"],
                                    }
                                    for row in self.object.user_set.values()
                                ],
                            )
                        )
                    ),
                    R(
                        C(
                            open_modal_popup_button(
                                self.object,
                                self.model,
                                "ajax_edit_group_user",
                                "lg",
                            )
                        )
                    ),
                ),
                style="padding: 3rem; margin-bottom: 2rem;",
            ),
            layout.tile.Tile(
                layout.grid.Grid(
                    R(C(hg.H3(_("Permissions")))),
                    R(
                        C(
                            DataTable(
                                columns=[
                                    DataTableColumn(
                                        header=_("ID"),
                                        cell=hg.DIV(hg.C("row.id")),
                                    ),
                                    DataTableColumn(
                                        header=_("App"),
                                        cell=hg.DIV(hg.C("row.app_label")),
                                    ),
                                    DataTableColumn(
                                        header=_("Model"),
                                        cell=hg.DIV(hg.C("row.model")),
                                    ),
                                    DataTableColumn(
                                        header=_("Codename"),
                                        cell=hg.DIV(hg.C("row.codename")),
                                    ),
                                    DataTableColumn(
                                        header=_("Permission"),
                                        cell=hg.DIV(hg.C("row.permissions")),
                                    ),
                                ],
                                row_iterator=[
                                    {
                                        "id": row["id"],
                                        "app_label": contenttypes.models.ContentType.objects.get(
                                            pk=row["content_type_id"]
                                        ).app_label,
                                        "model": contenttypes.models.ContentType.objects.get(
                                            pk=row["content_type_id"]
                                        ).model,
                                        "permissions": row["name"],
                                        "codename": row["codename"],
                                    }
                                    for row in self.object.permissions.values()
                                ],
                            )
                        )
                    ),
                    R(
                        C(
                            open_modal_popup_button(
                                self.object,
                                self.model,
                                "ajax_edit_group_permissions",
                                "lg",
                            )
                        )
                    ),
                ),
                style="padding: 3rem;",
            ),
        )


class GroupEditView(EditView):
    model = auth.models.Group

    def get_layout(self):
        return layout.grid.Grid(
            layout.components.forms.Form(hg.C("form"), R(C(F("name")))),
        )


class GroupEditUser(EditView):
    model = auth.models.Group

    class EditUserForm(forms.Form):
        user_set = forms.ModelMultipleChoiceField(
            queryset=DjangoUserModel.objects.all(),
            label=_("Users"),
            widget=forms.SelectMultiple(),
            required=False,
        )

        def __init__(self, group, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["user_set"].initial = DjangoUserModel.objects.filter(
                groups__pk=group.pk
            )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        group = self.object

        form = self.EditUserForm(group, request.POST)
        if form.is_valid():
            user_set_pks = [
                user["id"] for user in form.cleaned_data["user_set"].values()
            ]
            added_user = DjangoUserModel.objects.filter(pk__in=user_set_pks)
            removed_user = group.user_set.filter(~Q(pk__in=user_set_pks))

            for user in added_user.values():
                group.user_set.add(user["id"])
            for user in removed_user.values():
                group.user_set.remove(user["id"])

            group.save()
        else:
            messages.error(
                request,
                _("An unexpected error occured. Please try again."),
            )

        return super().post(request, *args, **kwargs)

    def get_layout(self):
        form = self.EditUserForm(self.object)
        return layout.grid.Grid(
            layout.components.forms.Form(
                form, R(C(F("user_set", widgetclass=MenuPicker)))
            ),
        )


class GroupEditPermission(EditView):
    model = auth.models.Group

    def get_layout(self):
        return layout.grid.Grid(
            layout.components.forms.Form(
                hg.C("form"), R(C(F("permissions", widgetclass=MenuPicker)))
            ),
        )


class UserReadView(ReadView):
    left_fields = [
        "id",
        "username",
        "first_name",
        "last_name",
        "email",
    ]
    right_fields = [
        "date_joined",
        "is_superuser",
        "is_staff",
        "is_active",
    ]

    def get_layout(self):
        return hg.BaseElement(
            hg.H3(
                hg.SPAN(self.object),
                edituser_toolbar(self.request),
            ),
            layout.tile.Tile(
                layout.grid.Grid(
                    R(C(hg.H3("Basic Information"))),
                    R(
                        C(
                            *(
                                display_label_and_value(
                                    ObjectFieldLabel(field), ObjectFieldValue(field)
                                )
                                for field in self.left_fields
                            ),
                        ),
                        C(
                            *(
                                display_label_and_value(
                                    ObjectFieldLabel(field), ObjectFieldValue(field)
                                )
                                for field in self.right_fields
                            ),
                        ),
                    ),
                    R(
                        C(
                            open_modal_popup_button(
                                self.object,
                                self.model,
                                "ajax_edit_user_info",
                                "md",
                            ),
                            open_modal_popup_button(
                                self.object,
                                self.model,
                                "ajax_edit_user_password",
                                "md",
                                _("Change Password"),
                            ),
                        )
                    ),
                ),
                style="padding: 3rem; margin-bottom: 2rem;",
            ),
            layout.tile.Tile(
                layout.grid.Grid(
                    R(C(hg.H3(_("Group")))),
                    R(
                        C(
                            DataTable(
                                columns=[
                                    DataTableColumn(
                                        header=_("ID"), cell=hg.DIV(hg.C("row.id"))
                                    ),
                                    DataTableColumn(
                                        header=_("Group Name"),
                                        cell=hg.DIV(hg.C("row.group")),
                                    ),
                                ],
                                row_iterator=[
                                    {"id": row["id"], "group": row["name"]}
                                    for row in self.object.groups.values()
                                ],
                            )
                        )
                    ),
                    R(
                        C(
                            open_modal_popup_button(
                                self.object,
                                self.model,
                                "ajax_edit_user_group",
                                "lg",
                            )
                        )
                    ),
                ),
                style="padding: 3rem; margin-bottom: 2rem;",
            ),
            layout.tile.Tile(
                layout.grid.Grid(
                    R(C(hg.H3(_("Permissions")))),
                    R(
                        C(
                            DataTable(
                                columns=[
                                    DataTableColumn(
                                        header=_("ID"),
                                        cell=hg.DIV(hg.C("row.id")),
                                    ),
                                    DataTableColumn(
                                        header=_("App"),
                                        cell=hg.DIV(hg.C("row.app_label")),
                                    ),
                                    DataTableColumn(
                                        header=_("Model"),
                                        cell=hg.DIV(hg.C("row.model")),
                                    ),
                                    DataTableColumn(
                                        header=_("Codename"),
                                        cell=hg.DIV(hg.C("row.codename")),
                                    ),
                                    DataTableColumn(
                                        header=_("Permission"),
                                        cell=hg.DIV(hg.C("row.permissions")),
                                    ),
                                ],
                                row_iterator=[
                                    {
                                        "id": row["id"],
                                        "app_label": contenttypes.models.ContentType.objects.get(
                                            pk=row["content_type_id"]
                                        ).app_label,
                                        "model": contenttypes.models.ContentType.objects.get(
                                            pk=row["content_type_id"]
                                        ).model,
                                        "permissions": row["name"],
                                        "codename": row["codename"],
                                    }
                                    for row in self.object.user_permissions.values()
                                ],
                            )
                        )
                    ),
                    R(
                        C(
                            open_modal_popup_button(
                                self.object,
                                self.model,
                                "ajax_edit_user_permissions",
                                "lg",
                            )
                        )
                    ),
                ),
                style="padding: 3rem;",
            ),
        )


class UserEditPassword(EditView):
    model = DjangoUserModel

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = self.object

        form = auth.forms.SetPasswordForm(user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
        else:
            raise ValidationError(
                _("The password fields might mismatch. Please try again."),
                code="password_mismatch",
            )

        return super().post(request, *args, **kwargs)

    def get_layout(self):
        R = layout.grid.Row
        C = layout.grid.Col
        F = layout.forms.FormField

        form = auth.forms.SetPasswordForm(self.object)
        return layout.grid.Grid(
            layout.components.forms.Form(
                form,
                layout.grid.Grid(
                    R(C(F("new_password1"))),
                    R(C(F("new_password2"))),
                ),
            ),
        )


class UserEditView(EditView):
    model = DjangoUserModel
    fields = [
        "is_active",
        "username",
        "first_name",
        "last_name",
        "email",
        "is_superuser",
        "is_staff",
    ]

    def get_layout(self):
        R = layout.grid.Row
        C = layout.grid.Col
        F = layout.forms.FormField
        return layout.grid.Grid(
            layout.components.forms.Form(
                hg.C("form"),
                *(R(C(F(field))) for field in self.fields),
            )
        )


class UserEditGroup(EditView):
    model = DjangoUserModel

    def get_layout(self):
        R = layout.grid.Row
        C = layout.grid.Col
        F = layout.forms.FormField

        return layout.grid.Grid(
            layout.components.forms.Form(
                hg.C("form"),
                R(C(F("groups", widgetclass=MenuPicker))),
            ),
        )


class UserEditPermission(EditView):
    model = DjangoUserModel

    def get_layout(self):
        R = layout.grid.Row
        C = layout.grid.Col
        F = layout.forms.FormField

        return layout.grid.Grid(
            layout.components.forms.Form(
                hg.C("form"), R(C(F("user_permissions", widgetclass=MenuPicker)))
            ),
        )


def display_label_and_value(label, value):
    return R(
        C(
            hg.DIV(
                label,
                style="font-weight: bold;",
            ),
            width=6,
        ),
        C(value),
        style="padding-bottom: 1.5rem;",
    )


def edituser_toolbar(request):
    deletebutton = layout.button.Button(
        _("Delete"),
        buttontype="ghost",
        icon="trash-can",
        notext=True,
        **layout.aslink_attributes(
            hg.F(lambda c: layout.objectaction(c["object"], "delete"))
        ),
    )
    restorebutton = layout.button.Button(
        _("Restore"),
        buttontype="ghost",
        icon="undo",
        notext=True,
        **layout.aslink_attributes(
            hg.F(
                lambda c: layout.objectaction(
                    c["object"], "delete", query={"restore": True}
                )
            )
        ),
    )
    copybutton = layout.button.Button(
        _("Copy"),
        buttontype="ghost",
        icon="copy",
        notext=True,
        **layout.aslink_attributes(
            hg.F(lambda c: layout.objectaction(c["object"], "copy"))
        ),
    )

    return hg.SPAN(
        hg.If(hg.C("object.deleted"), restorebutton, deletebutton),
        copybutton,
        layout.button.PrintPageButton(buttontype="ghost"),
        _class="no-print",
        style="margin-bottom: 1rem; margin-left: 1rem",
        width=3,
    )


# reused from basxconnect
def open_modal_popup_button(heading, model, action, size="xs", btnlabel=_("Edit")):
    return R(
        C(
            modal_with_trigger(
                create_modal(heading, model, action, size),
                layout.button.Button,
                btnlabel,
                buttontype="tertiary",
                icon="edit",
            ),
            style="margin-top: 1.5rem;",
        )
    )


def create_modal(heading, model: Union[type, Lazy], action: str, size="xs"):
    modal = layout.modal.Modal.with_ajax_content(
        heading=heading,
        url=ModelHref(
            model,
            action,
            kwargs={"pk": hg.F(lambda c: c["object"].pk)},
            query={"asajax": True},
        ),
        submitlabel=_("Save"),
        size=size,
    )
    return modal


@aslayout
def componentpreview(request):
    class ConfigForm(forms.Form):
        with_label = forms.BooleanField(required=False)
        with_helptext = forms.BooleanField(required=False)
        with_errors = forms.BooleanField(required=False)
        disabled = forms.BooleanField(required=False)

    CHOICES = (
        ("choice1", "Choice 1"),
        ("choice2", "Choice 2"),
        ("choice3", "Choice 3"),
        ("choice4", "Choice 4"),
    )

    widgets = {
        forms.TextInput: (forms.CharField, {"widget": forms.TextInput}),
        forms.NumberInput: (forms.DecimalField, {"widget": forms.NumberInput}),
        forms.EmailInput: (forms.EmailField, {"widget": forms.EmailInput}),
        forms.URLInput: (forms.URLField, {"widget": forms.URLInput}),
        forms.PasswordInput: (forms.CharField, {"widget": forms.PasswordInput}),
        forms.HiddenInput: (forms.CharField, {"widget": forms.HiddenInput}),
        forms.DateInput: (forms.DateField, {"widget": forms.DateInput}),
        forms.DateTimeInput: (forms.DateTimeField, {"widget": forms.DateTimeInput}),
        forms.TimeInput: (forms.TimeField, {"widget": forms.TimeInput}),
        forms.Textarea: (forms.CharField, {"widget": forms.Textarea}),
        forms.CheckboxInput: (forms.BooleanField, {"widget": forms.CheckboxInput}),
        forms.Select: (forms.ChoiceField, {"widget": forms.Select, "choices": CHOICES}),
        forms.NullBooleanSelect: (
            forms.NullBooleanField,
            {"widget": forms.NullBooleanSelect},
        ),
        forms.SelectMultiple: (
            forms.MultipleChoiceField,
            {"widget": forms.SelectMultiple, "choices": CHOICES},
        ),
        forms.RadioSelect: (
            forms.ChoiceField,
            {"widget": forms.RadioSelect, "choices": CHOICES},
        ),
        forms.CheckboxSelectMultiple: (
            forms.ChoiceField,
            {"widget": forms.CheckboxSelectMultiple, "choices": CHOICES},
        ),
        forms.FileInput: (forms.FileField, {"widget": forms.FileInput}),
        forms.ClearableFileInput: (
            forms.FileField,
            {"widget": forms.ClearableFileInput},
        ),
    }

    HELPTEXT = "This is a piece of helptext, maximized for helpfulness"
    ERRORS = [
        "This is an example of an error",
        "This is a second errors, but actually none of them are real errors, so do not worry",
    ]

    def nicefieldname(cls):
        return re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__)

    configform = ConfigForm(request.GET)
    if not configform.is_valid() or not request.GET:
        config = configform.initial
    config = configform.cleaned_data

    Form = type(
        "Form",
        (forms.Form,),
        {
            nicefieldname(widget): field[0](
                **field[1],
                **({"help_text": HELPTEXT} if config["with_helptext"] else {}),
                disabled=config["disabled"],
            )
            for widget, field in widgets.items()
        },
    )

    return hg.BaseElement(
        hg.STYLE(
            hg.mark_safe(
                """
                #backtotopBtn {
                    position: fixed;
                    right: 0;
                    bottom: 0;
                    z-index: 999;
                    margin-right: 3rem;
                    margin-bottom: 3rem;
                    border-radius: 50%;
                }
                """
            )
        ),
        layout.button.Button.from_link(
            Link(href="#", label=_("Back to top")),
            buttontype="secondary",
            icon="arrow--up",
            notext=True,
            id="backtotopBtn",
        ),
        tabs.Tabs(
            tabs.Tab(
                _("Layout"),
                layout.componentpreview.layout(request),
            ),
            tabs.Tab(
                _("Informational"),
                layout.componentpreview.informational(request),
            ),
            tabs.Tab(
                _("Interactive"),
                layout.componentpreview.interactive(request),
            ),
            tabs.Tab(
                _("Datatable"),
                layout.componentpreview.datatable_layout(request),
            ),
            tabs.Tab(
                _("Form"),
                hg.BaseElement(
                    hg.H3(_("Widget preview")),
                    layout.grid.Grid(
                        layout.grid.Row(
                            layout.grid.Col(
                                hg.H4(_("Widgets")),
                                layout.forms.Form(
                                    Form(),
                                    *[
                                        F(
                                            nicefieldname(w),
                                            no_label=not config["with_label"],
                                            errors=ERRORS
                                            if config["with_errors"]
                                            else None,
                                        )
                                        for w in widgets.keys()
                                    ],
                                ),
                            ),
                            layout.grid.Col(
                                hg.H4(_("Configure preview")),
                                layout.forms.Form(
                                    configform,
                                    F("with_label"),
                                    F("with_helptext"),
                                    F("with_errors"),
                                    F("disabled"),
                                    layout.forms.helpers.Submit(_("Apply")),
                                    method="GET",
                                ),
                            ),
                        ),
                        R(
                            C(
                                hg.H3(_("Tooltips")),
                                hg.H4(_("Definition tooltip")),
                                hg.DIV(
                                    layout.components.tooltip.DefinitionTooltip(
                                        "Definition tooltip (left aligned)",
                                        "Brief definition of the dotted, underlined word above.",
                                        align="left",
                                    )
                                ),
                                hg.DIV(
                                    layout.components.tooltip.DefinitionTooltip(
                                        "Definition tooltip (center aligned)",
                                        "Brief definition of the dotted, underlined word above.",
                                        align="center",
                                    )
                                ),
                                hg.DIV(
                                    layout.components.tooltip.DefinitionTooltip(
                                        "Definition tooltip (right aligned)",
                                        "Brief definition of the dotted, underlined word above.",
                                        align="right",
                                    )
                                ),
                                hg.H4(_("Icon tooltip")),
                                hg.DIV(
                                    layout.components.tooltip.IconTooltip(
                                        "Help",
                                    ),
                                    layout.components.tooltip.IconTooltip(
                                        "Filter",
                                        icon=Icon("filter"),
                                    ),
                                    layout.components.tooltip.IconTooltip(
                                        "Email",
                                        icon="email",
                                    ),
                                ),
                                hg.H4(_("Interactive tooltip")),
                                hg.DIV(
                                    layout.components.tooltip.InteractiveTooltip(
                                        label="Tooltip label",
                                        body=(
                                            _(
                                                "This is some tooltip text. This box shows the maximum amount of text that should "
                                                "appear inside. If more room is needed please use a modal instead."
                                            )
                                        ),
                                        heading="Heading within a Tooltip",
                                        button=(
                                            layout.components.button.Button("Button")
                                        ),
                                        link=Link(href="#", label="link"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )


class TaskResultBrowseView(BrowseView):
    columns = [
        DataTableColumn(
            layout.ObjectFieldLabel("task_id", TaskResult),
            hg.DIV(
                hg.C("row.task_id"),
            ),
            "task_id",
        ),
        DataTableColumn(
            layout.ObjectFieldLabel("task_name", TaskResult),
            hg.DIV(
                hg.C("row.task_name"),
            ),
            "task_name",
        ),
        DataTableColumn(
            _("Date Created"),
            hg.DIV(
                hg.C("row.date_created"),
            ),
            "date_created",
        ),
        DataTableColumn(
            _("Date Completed"),
            hg.DIV(
                hg.C("row.date_done"),
            ),
            "date_done",
        ),
        "status",
        "worker",
        "content_type",
        DataTableColumn(
            _("Metadata"),
            hg.DIV(
                hg.C("row.meta"),
            ),
        ),
    ]
    rowclickaction = BrowseView.gen_rowclickaction("read")
    title = "Background Jobs"


def maintainance_package_layout(request):
    PYPI_API = "https://pypi.python.org/pypi/{}/json"
    PACKAGE_NAMES = ("basx-bread", "basxconnect", "htmlgenerator")

    package_current = []
    package_latest = []
    for package_name in PACKAGE_NAMES:
        current_version = pkg_resources.get_distribution(package_name).version
        newer_version = _("unable to load")

        # load the latest package info from the PyPI API
        pkg_info_req = requests.get(PYPI_API.format(package_name))
        if pkg_info_req.status_code == requests.codes.ok:
            newer_version = pkg_info_req.json()["info"]["version"]

        package_current.append(current_version)
        package_latest.append(newer_version)

    return DataTable(
        columns=[
            DataTableColumn(
                header=_("Package"),
                cell=hg.DIV(hg.C("row.package_name")),
            ),
            DataTableColumn(
                header=_("Current"),
                cell=hg.DIV(hg.C("row.package_current")),
            ),
            DataTableColumn(
                header=_("Latest"),
                cell=(hg.DIV(hg.C("row.package_latest"))),
            ),
        ],
        row_iterator=[
            {
                "package_name": pkg_name,
                "package_current": pkg_current,
                "package_latest": pkg_latest,
            }
            for pkg_name, pkg_current, pkg_latest in zip(
                PACKAGE_NAMES, package_current, package_latest
            )
        ],
    )


def maintenance_database_optimization(request):
    database_path = settings.DATABASES["default"]["NAME"]
    current_db_size = os.stat(database_path).st_size / 1000

    class OptimizeForm(forms.Form):
        previous = forms.DecimalField(
            widget=forms.HiddenInput,
            initial=current_db_size,
        )

    form: OptimizeForm
    ret = hg.BaseElement()
    received_post = False

    if request.method == "POST":
        form = OptimizeForm(request.POST)
        if form.is_valid() and "previous" in form.cleaned_data:
            received_post = True
            connection.cursor().execute("VACUUM;")
            # get the previous size
            previous_size = form.cleaned_data["previous"]
            current_db_size = os.stat(database_path).st_size / 1000

            # try adding some message here.
            messages.info(
                request,
                _("The database size has been minimized from %.2f kB to %.2f kB.")
                % (previous_size, current_db_size),
            )

            ret.append(
                hg.H5(_("Previous Size: %.2f kB") % form.cleaned_data["previous"])
            )

    if not received_post:
        form = OptimizeForm()

    optimize_btn = Form(
        form,
        FormField("previous"),
        Button(
            _("Optimize"),
            type="submit",
        ),
    )

    ret.append(hg.H5(_("Current Size: %.2f kB") % current_db_size))
    ret.append(optimize_btn)

    return ret


def maintenance_search_reindex(request):
    class ReindexForm(forms.Form):
        confirmed = forms.BooleanField(
            widget=forms.HiddenInput,
            initial=True,
        )

    form: ReindexForm
    received_post = False
    logmsg: str = None

    if request.method == "POST":
        form = ReindexForm(request.POST)
        if form.is_valid() and "confirmed" in form.cleaned_data:
            received_post = True

            out = StringIO()
            management.call_command("rebuild_index", interactive=False, stdout=out)
            logmsg = out.getvalue().replace("\n", "<br>")

            # try adding some message here.
            messages.info(request, _("Rebuilt search index"))

    if not received_post:
        form = ReindexForm()

    reindex_btn = Form(
        form,
        FormField("confirmed"),
        Button(
            _("Rebuild"),
            type="submit",
            style="margin-bottom: 1rem;",
        ),
    )

    return hg.BaseElement(
        hg.P(
            _(
                (
                    "After certain kind of database updates the search index may become outdated. "
                    "You can reindex the search index by clicking the button below. "
                    "This should fix most problems releated to search fields."
                )
            ),
            style="margin-bottom: 1rem;",
        ),
        reindex_btn,
        hg.If(
            logmsg,
            hg.BaseElement(
                hg.H6(_("Log from the server"), style="margin-bottom: 0.75rem;"),
                hg.SAMP(hg.mark_safe(logmsg), style="font-family: monospace;"),
            ),
        ),
    )


@aslayout
def systeminformation(request):
    git_status = ""
    try:
        git_status = (
            subprocess.run(  # nosec because we have no user input to subprocess
                ["git", "log", "-n", "5", "--oneline"], capture_output=True, check=True
            ).stdout.decode()
        )
    except subprocess.SubprocessError as e:
        git_status = hg.BaseElement(
            "ERROR",
            hg.BR(),
            str(e),
            hg.BR(),
            getattr(e, "stdout", b"").decode(),
            hg.BR(),
            getattr(e, "stderr", b"").decode(),
        )

    return hg.BaseElement(
        hg.H3(_("System information")),
        hg.H4("Git log"),
        hg.PRE(hg.CODE(git_status)),
        hg.H4("PIP packages", style="margin-top: 2rem"),
        hg.UL(
            hg.Iterator(
                sorted(
                    ["%s==%s" % (i.key, i.version) for i in pkg_resources.working_set]
                ),
                "package",
                hg.LI(hg.C("package")),
            )
        ),
    )
