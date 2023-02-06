import datetime

import htmlgenerator as hg
from django.core.paginator import Paginator
from django.db import models
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from basxbread import formatters, layout, views
from basxbread.utils import filter_fieldlist, generate_excel, xlsxresponse
from basxbread.utils.links import ModelHref

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
        column_helper = layout.modal.Modal(
            _("Field explorer"), layout.fieldexplorer.field_help(modelclass), size="lg"
        )

        F = layout.forms.FormField

        fieldstable = layout.forms.Formset.as_datatable(
            hg.C("form")["columns"].formset,
            fieldname="columns",
            title=hg.C("form")["columns"].label,
            fields=["header", "column", "cell_template", "allow_html"],
            formsetfield_kwargs={
                "extra": 1,
                "can_order": True,
            },
        )
        fieldstable[1][0].insert(
            1,
            layout.button.Button(
                _("Help"), buttontype="ghost", **column_helper.openerattributes
            ),
        )
        fieldstable.append(hg.DIV(style="height: 1rem"))
        ret = hg.BaseElement(
            views.header(),
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
                fieldstable,
                layout.tile.ExpandableTile(
                    hg.H4(_("Extended settings")),
                    hg.DIV(
                        F("custom_queryset"),
                        F("pagination"),
                    ),
                ),
                layout.forms.helpers.Submit(style="margin-top: 1rem"),
                column_helper,
            ),
            hg.C("object.preview"),
        )
        return ret

    def get_success_url(self):
        return self.request.get_full_path()


class ReadView(views.ReadView):
    def get_layout(self):
        # ordering, copied from basxbread.views.browse.BrowseView.get_queryset
        if self.object.model.model_class() is None:
            return layout.notification.InlineNotification(
                "Error",
                f"Model '{self.object.model}' does no longer exist.",
                kind="error",
            )

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
        paginator = Paginator(qs, self.object.pagination)

        columns = []
        for col in self.object.columns.all():
            sortingname = None
            try:
                sortingname = layout.datatable.sortingname_for_column(
                    self.object.model.model_class(), col.column
                )
            except AttributeError:
                pass
            columns.append(
                layout.datatable.DataTableColumn(
                    header=col.header,
                    cell=col.render_element("row"),
                    sortingname=sortingname,
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
        pagination_config = layout.pagination.PaginationConfig(
            paginator=paginator,
            items_per_page_options=[self.object.pagination],
        )
        # generate a nice table
        return hg.BaseElement(
            views.header(),
            layout.datatable.DataTable(
                columns=columns,
                row_iterator=paginator.get_page(
                    self.request.GET.get(pagination_config.page_urlparameter)
                )
                if self.object.pagination
                else qs,
            ).with_toolbar(
                title=self.object.name,
                helper_text=f"{self.object.queryset.count()} "
                f"{self.object.model.model_class()._meta.verbose_name_plural}",
                primary_button=layout.button.Button(
                    label=_("Excel"), icon="download"
                ).as_href(ModelHref.from_object(self.object, "excel")),
                pagination_config=pagination_config if self.object.pagination else None,
            ),
        )


def exceldownload(request, pk: int):
    report = get_object_or_404(Report, pk=pk)
    if report.model.model_class() is None:
        return HttpResponseNotFound()

    columns = {
        column.header: lambda row, c=column: hg.render(
            c.render_element("row"), {"row": row}
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
