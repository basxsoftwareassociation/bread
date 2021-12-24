import re

import htmlgenerator as hg
from django import forms
from django.contrib.auth.decorators import user_passes_test
from django.utils.translation import gettext_lazy as _
from django_celery_results.models import TaskResult

from bread import layout
from bread.layout import admin
from bread.layout.components.datatable import DataTableColumn
from bread.utils.urls import aslayout
from bread.views import BrowseView

R = layout.grid.Row
C = layout.grid.Col
F = layout.forms.FormField

TR = layout.datatable.DataTable.row
TD = layout.datatable.DataTableColumn


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
                admin.maintainance_package_layout(request),
            ),
            C(
                hg.H4(_("Optimize database")),
                admin.maintenance_database_optimization(request),
                hg.H4(_("Rebuild search index"), _style="margin-top: 3rem;"),
                admin.maintenance_search_reindex(request),
            ),
        )
    )

    return ret


@aslayout
def widgetpreview(request):
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
                disabled=config["disabled"]
            )
            for widget, field in widgets.items()
        },
    )

    return hg.BaseElement(
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
                                errors=ERRORS if config["with_errors"] else None,
                            )
                            for w in widgets.keys()
                        ]
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
            )
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
