import datetime

import htmlgenerator as hg
from django.shortcuts import get_object_or_404
from django.urls import path
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from bread import formatters
from bread import layout as _layout
from bread import menu, views
from bread.utils import generate_excel, urls, xlsxresponse

from .models import Report


class EditView(views.EditView):
    def get_layout(self):
        F = _layout.form.FormField
        ret = hg.BaseElement(
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


def exceldownload(request, report_pk: int):
    report = get_object_or_404(Report, pk=report_pk)
    columns = {
        column.name: lambda row, c=column.column: formatters.format_value(
            hg.resolve_lookup(row, c)
        )
        for column in report.columns.all()
    }

    workbook = generate_excel(report.filter.queryset, columns)
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
                menu.Link(
                    urls.reverse_model(Report, "bulkdelete"),
                    icon="trash-can",
                ),
                menu.Link(urls.reverse_model(Report, "bulkcopy"), icon="copy"),
            ],
            rowactions=[
                menu.Action(
                    js=hg.BaseElement(
                        "document.location = '",
                        hg.F(
                            lambda c, e: urls.reverse_model(
                                Report, "excel", kwargs={"report_pk": c["row"].pk}
                            )
                        ),
                        "'",
                    ),
                    icon="download",
                    label=_("Excel"),
                ),
            ],
            backurl="#",
        ),
        addview=views.AddView._with(fields=["name", "model"]),
        editview=EditView,
        readview=EditView,
    ),
    urls.generate_path(
        views.BulkDeleteView.as_view(model=Report),
        urls.model_urlname(Report, "bulkdelete"),
    ),
    urls.generate_path(
        views.generate_bulkcopyview(
            Report, labelfield="name", copy_related_fields=("columns",)
        ),
        urls.model_urlname(Report, "bulkcopy"),
    ),
    urls.generate_path(
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
        menu.Link(urls.reverse_model(Report, "browse"), label=_("Reports")),
        menu.Group(_("Reports"), icon="download"),
    )
)
