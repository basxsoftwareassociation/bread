import datetime

import htmlgenerator as hg
from django.db import models
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from bread import formatters, layout, views
from bread.utils import filter_fieldlist, generate_excel, xlsxresponse
from bread.utils.links import ModelHref

from .models import Report


class EditView(views.EditView):
    def get_layout(self):
        modelclass = self.object.model.model_class()
        if modelclass is None:
            return layout.notification.InlineNotification(
                "Error",
                f"Model '{self.object.model}' does no longer exist.",
                kind="error",
            )
        column_helper = layout.get_attribute_description_modal(modelclass)

        F = layout.forms.FormField
        ret = hg.BaseElement(
            hg.H3(self.object),
            layout.forms.Form(
                hg.C("form"),
                hg.DIV(
                    _("Base model"),
                    ": ",
                    hg.C("object.model"),
                    style="margin: 2rem 0 2rem 0",
                ),
                F("name"),
                F(
                    "filter",
                    inputelement_attrs={"rows": 1},
                    style="width: 100%",
                ),
                F("custom_queryset"),
                layout.forms.FormsetField.as_datatable(
                    "columns",
                    ["column", "name"],
                    formsetfield_kwargs={
                        "extra": 1,
                        "can_order": True,
                    },
                ),
                layout.button.Button(
                    _("Help"),
                    buttontype="ghost",
                    style="margin-top: 1rem",
                    **column_helper.openerattributes,
                ),
                layout.forms.helpers.Submit(),
                column_helper,
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
        if not qs:
            return layout.notification.InlineNotification(
                "Error",
                f"Model '{self.object.model}' does no longer exist.",
                kind="error",
            )

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
                layout.datatable.sortingname_for_column(
                    self.object.model.model_class(), col.column
                ),
            except AttributeError:
                pass
            columns.append(
                layout.datatable.DataTableColumn(
                    col.name, layout.FC(f"row.{col.column}"), sortingname
                )
            )
        if not columns:
            columns = [
                layout.datatable.DataTableColumn.from_modelfield(
                    col, self.object.model.model_class()
                )
                for col in filter_fieldlist(
                    self.object.model.model_class(), ["__all__"]
                )
            ]

        # generate a nice table
        return layout.datatable.DataTable(
            columns=columns, row_iterator=qs
        ).with_toolbar(
            title=self.object.name,
            helper_text=f"{self.object.queryset.count()} "
            f"{self.object.model.model_class()._meta.verbose_name_plural}",
            primary_button=layout.button.Button(
                label=_("Excel"), icon="download"
            ).as_href(ModelHref.from_object(self.object, "excel")),
        )


def exceldownload(request, pk: int):
    report = get_object_or_404(Report, pk=pk)
    if report.model.model_class() is None:
        return HttpResponseNotFound()

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
