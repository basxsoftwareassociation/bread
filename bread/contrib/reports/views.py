import datetime

import htmlgenerator as hg
from django.contrib.staticfiles.storage import staticfiles_storage
from django.db import models
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from bread import formatters
from bread import layout as _layout
from bread import layout as layout
from bread import views
from bread.utils import filter_fieldlist, generate_excel, xlsxresponse
from bread.utils.links import ModelHref

from ...layout.components.datatable import DataTableColumn, sortingname_for_column
from .models import Report


class EditView(views.EditView):
    def get_layout(self):
        modelclass = self.object.model.model_class()
        if modelclass is None:
            return _layout.notification.InlineNotification(
                "Error",
                f"Model '{self.object.model}' does no longer exist.",
                kind="error",
            )
        column_helper = get_attribute_description_modal(modelclass)

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
                    _layout.button.Button(
                        _("Help"),
                        buttontype="ghost",
                        style="margin-top: 1rem",
                        **column_helper.openerattributes,
                    ),
                    column_helper,
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
        if not qs:
            return _layout.notification.InlineNotification(
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
            primary_button=_layout.button.Button(
                label=_("Excel"), icon="download"
            ).as_href(ModelHref(self.object, "excel")),
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


def get_attribute_description_modal(obj):
    columns = []
    fields = {f.name: f for f in obj._meta.get_fields()}
    for i in set(dir(obj) + list(vars(obj))):
        try:
            desc = _get_attribute_description(obj, i, fields)
            if desc is not None and desc[3]:
                f = desc[3]._meta.get_fields()
                additional_attrs = list(
                    filter(
                        None,
                        (
                            _get_attribute_description(desc[3], a, f)
                            for a in set(dir(desc[3]) + list(vars(desc[3])))
                        ),
                    )
                )
                desc = (
                    desc[0],
                    desc[1],
                    desc[2],
                    hg.BaseElement(
                        hg.UL(
                            hg.Iterator(
                                additional_attrs,
                                "attr",
                                hg.LI(
                                    hg.format("{}.{}", i, hg.C("attr.0")),
                                    style="font-weight: 700",
                                ),
                            )
                        ),
                    ),
                )
            if desc is not None:
                columns.append(desc)
        except Exception as e:
            columns.append((i, _("Unknown"), e))
    return layout.modal.Modal(
        _("Available columns"),
        hg.DIV(
            hg.DIV(_("Bold text marks valid column names")),
            layout.datatable.DataTable(
                columns=[
                    layout.datatable.DataTableColumn(
                        _("Column name"),
                        hg.SPAN(hg.C("row.0"), style="font-weight: 700"),
                    ),
                    layout.datatable.DataTableColumn(
                        _("Description"), hg.F(lambda c: c["row"][2])
                    ),
                    layout.datatable.DataTableColumn(
                        _("Type"), hg.F(lambda c: c["row"][1])
                    ),
                    layout.datatable.DataTableColumn(
                        _("Extended columns"), hg.C("row.3")
                    ),
                ],
                row_iterator=sorted(columns),
            ),
        ),
    )


def _get_attribute_description(obj, attr, modelfields):
    # returns tuple(field_name, type_name, description, model)
    if attr.startswith("_"):  # leading underscore is "private" by convention in python
        return None
    if callable(getattr(obj, attr, None)):
        return None

    if attr in modelfields:
        if hasattr(modelfields[attr], "related_model") and getattr(
            modelfields[attr], "related_model"
        ):
            return (
                attr,
                f"{type(modelfields[attr]).__name__} -> {modelfields[attr].related_model._meta.verbose_name}",
                getattr(modelfields[attr], "verbose_name", None),
                modelfields[attr].related_model,
            )
        else:
            return (
                attr,
                type(modelfields[attr]).__name__,
                modelfields[attr].verbose_name,
                None,
            )
    if hasattr(getattr(obj, attr, None), "related") and getattr(
        getattr(obj, attr, None), "related"
    ):
        return (
            attr,
            f"{type(getattr(obj, attr, None)).__name__} -> {getattr(obj, attr, None).related.related_model._meta.verbose_name}",
            getattr(getattr(obj, attr, None), "verbose_name", None),
            getattr(obj, attr, None).related.related_model,
        )
    return (
        attr,
        type(getattr(obj, attr, None)).__name__,
        getattr(getattr(obj, attr, None), "verbose_name", None),
        None,
    )
