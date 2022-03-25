import os
import re
import subprocess  # nosec because we covered everything
from io import StringIO

import htmlgenerator as hg
import pkg_resources
import requests
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core import management
from django.db import connection
from django.utils.translation import gettext_lazy as _
from django_celery_results.models import TaskResult

from bread import layout
from bread.layout.components import tabs
from bread.layout.components.button import Button
from bread.layout.components.datatable import DataTable, DataTableColumn
from bread.layout.components.forms import Form, FormField
from bread.views import BrowseView

from ..layout.components.icon import Icon
from ..utils import Link, aslayout

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
                disabled=config["disabled"]
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

    return hg.BaseElement()


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
