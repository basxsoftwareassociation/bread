import os
from io import StringIO

import htmlgenerator as hg
import pkg_resources
import requests
from django import forms
from django.conf import settings
from django.contrib import messages
from django.core import management
from django.db import connection
from django.utils.translation import gettext_lazy as _

from bread import layout
from bread.layout.components.button import Button
from bread.layout.components.datatable import DataTable, DataTableColumn
from bread.layout.components.forms import Form, FormField

PYPI_API = "https://pypi.python.org/pypi/{}/json"
PACKAGE_NAMES = ("basx-bread", "basxconnect", "htmlgenerator")

R = layout.grid.Row
C = layout.grid.Col


def maintainance_package_layout(request):
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
