import htmlgenerator as hg
from django.shortcuts import get_object_or_404
from django.urls import path
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from bread import menu, views
from bread.formatters import render_field
from bread.utils import generate_excel, pretty_modelname, urls, xlsxresponse
from bread.utils.model_helpers import _expand_ALL_constant

from .models import Report


class EditView(views.EditView):
    fields = ["filter"]

    def layout(self, request):
        ret = super().layout(request)
        ret.append(hg.C("object.preview"))
        return ret


def exceldownload(request, report_pk: int):
    report = get_object_or_404(Report, pk=report_pk)
    fields = {
        field: render_field
        for field in _expand_ALL_constant(report.model.model_class(), ["__all__"])
    }

    workbook = generate_excel(report.filter.queryset, fields)
    workbook.title = pretty_modelname(report.model.model_class(), plural=True)

    return xlsxresponse(workbook, workbook.title)


urlpatterns = [
    *urls.default_model_paths(
        Report,
        browseview=views.BrowseView._with(
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
        ),
        addview=views.AddView._with(fields=["model"]),
        editview=EditView,
        readview=EditView,
    ),
    urls.generate_path(
        views.BulkDeleteView.as_view(model=Report),
        urls.model_urlname(Report, "bulkdelete"),
    ),
    urls.generate_path(
        views.generate_bulkcopyview(Report),
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
