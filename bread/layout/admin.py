import os

import htmlgenerator as hg
import pkg_resources
import requests
from django import forms
from django.conf import settings
from django.contrib import messages
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

    if request.method == "POST":
        form = OptimizeForm(request.POST)

        if form.is_valid():
            connection.cursor().execute("VACUUM;")
            # get the previous size
            previous_size = form.cleaned_data["previous"]
            current_db_size = os.stat(database_path).st_size / 1000

            # try adding some message here.
            messages.info(
                request,
                _(
                    "The database size has been minimized from %.2f kB to %.2f kB."
                    % (previous_size, current_db_size)
                ),
            )
    else:
        form = OptimizeForm()

    optimize_btn = Form(
        form, FormField("previous"), Button(_("Optimize"), type="submit")
    )

    return hg.BaseElement(
        hg.H5(f"Current Size: {current_db_size : .2f} kB"),
        optimize_btn,
    )
