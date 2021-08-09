import datetime

import htmlgenerator as hg
from django.contrib.staticfiles.storage import staticfiles_storage
from django.db import models
from django.shortcuts import get_object_or_404
from django.urls import path
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from bread import formatters
from bread import layout as _layout
from bread import menu, views
from bread.utils import filter_fieldlist, generate_excel, urls, xlsxresponse
from bread.utils.links import Link
from bread.views.browse import delete
from bread.views.edit import bulkcopy

from ...layout.components.datatable import DataTableColumn, sortingname_for_column
from .models import Report


class EditView(views.EditView):
    def get_layout(self):
        F = _layout.form.FormField
        ret = hg.BaseElement(
            hg.LINK(
                rel="stylesheet",
                type="text/css",
                href=staticfiles_storage.url("djangoql/css/completion.css"),
            ),
            hg.SCRIPT(src=staticfiles_storage.url("djangoql/js/completion.js")),
            hg.H3(self.object),
            _layout.form.Form.wrap_with_form(
                hg.C("form"),
                hg.BaseElement(
                    hg.DIV(
                        _("Base model"),
                        ": ",
                        hg.C("object.model"),
                        style="margin: 2rem 0 2rem 0",
                    ),
                    F("name"),
                    F("filter"),
                    F("custom_queryset"),
                    _layout.form.FormsetField.as_datatable(
                        "columns",
                        ["column", "name"],
                        formsetfield_kwargs={
                            "extra": 1,
                            "can_order": True,
                        },
                    ),
                ),
            ),
            hg.C("object.preview"),
        )
        return ret

    def get_success_url(self):
        return self.request.get_full_path()


class ReadView(views.ReadView):
    def get_layout(self):

        # ordering, copied from bread.views.browse.BrowseView.get_queryset
        qs = self.object.queryset
        order = self.request.GET.get("ordering")
        if order:
            if order.endswith("__int"):
                order = order[: -len("__int")]
                qs = qs.order_by(
                    models.functions.Cast(order[1:], models.IntegerField()).desc()
                    if order.startswith("-")
                    else models.functions.Cast(order, models.IntegerField())
                )
            else:
                qs = qs.order_by(
                    models.functions.Lower(order[1:]).desc()
                    if order.startswith("-")
                    else models.functions.Lower(order)
                )

        columns = []
        for col in self.object.columns.all():
            sortingname = None
            try:
                sortingname_for_column(self.object.model.model_class(), col.column),
            except AttributeError:
                pass
            columns.append(
                DataTableColumn(col.name, _layout.FC(f"row.{col.column}"), sortingname)
            )
        if not columns:
            columns = [
                DataTableColumn.from_modelfield(col, self.object.model.model_class())
                for col in filter_fieldlist(
                    self.object.model.model_class(), ["__all__"]
                )
            ]

        # generate a nice table
        return _layout.datatable.DataTable(
            columns=columns, row_iterator=qs
        ).with_toolbar(
            title=self.object.name,
            helper_text=f"{self.object.queryset.count()} {self.object.model.model_class()._meta.verbose_name_plural}",
            primary_button=_layout.button.Button.fromaction(
                Link(
                    urls.reverse_model(self.object, "excel", {"pk": self.object.pk}),
                    label=_("Excel"),
                    iconname="download",
                )
            ),
        )


def exceldownload(request, pk: int):
    report = get_object_or_404(Report, pk=pk)

    columns = {
        column.name: lambda row, c=column.column: formatters.format_value(
            hg.resolve_lookup(row, c)
        )
        for column in report.columns.all()
    }
    if not columns:
        columns = {
            column: lambda row, c=column: formatters.format_value(
                hg.resolve_lookup(row, c)
            )
            for column in filter_fieldlist(report.model.model_class(), ["__all__"])
        }

    workbook = generate_excel(report.queryset, columns)
    workbook.title = report.name

    return xlsxresponse(
        workbook, workbook.title + f"-{datetime.date.today().isoformat()}"
    )


urlpatterns = [
    *urls.default_model_paths(
        Report,
        browseview=views.BrowseView._with(
            columns=["name", "created"],
            rowclickaction="read",
            bulkactions=[
                views.browse.BulkAction(
                    "delete", label=_("Delete"), iconname="trash-can", action=delete
                ),
                views.browse.BulkAction(
                    "copy",
                    label=_("Copy"),
                    iconname="copy",
                    action=lambda request, qs: bulkcopy(
                        request, qs, labelfield="name", copy_related_fields=("columns",)
                    ),
                ),
            ],
            rowactions=[
                menu.Action(
                    js=hg.BaseElement(
                        "document.location = '",
                        hg.F(lambda c: _layout.objectaction(c["row"], "edit")),
                        "'",
                    ),
                    iconname="edit",
                    label=_("Edit"),
                ),
                menu.Action(
                    js=hg.BaseElement(
                        "document.location = '",
                        hg.F(
                            lambda c: urls.reverse_model(
                                Report, "excel", kwargs={"pk": c["row"].pk}
                            )
                        ),
                        "'",
                    ),
                    iconname="download",
                    label=_("Excel"),
                ),
            ],
        ),
        addview=views.AddView._with(
            fields=["name", "model"],
            get_success_url=lambda s: urls.reverse_model(
                Report, "edit", kwargs={"pk": s.object.pk}
            ),
        ),
        editview=EditView,
        readview=ReadView,
    ),
    urls.autopath(
        exceldownload,
        urls.model_urlname(Report, "excel"),
    ),
    path(
        "reporthelp/",
        TemplateView.as_view(template_name="djangoql/syntax_help.html"),
        name="reporthelp",
    ),
]

menu.registeritem(
    menu.Item(
        Link(
            urls.reverse_model(Report, "browse"),
            label=_("Reports"),
            iconname="download",
        ),
        menu.Group(_("Reports"), iconname="download"),
    )
)
