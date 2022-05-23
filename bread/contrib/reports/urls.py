import htmlgenerator as hg
from django.urls import path
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from bread import menu, views
from bread.utils import urls
from bread.utils.links import Link, ModelHref
from bread.views.browse import delete
from bread.views.edit import bulkcopy, generate_copyview

from .models import Report
from .views import EditView, ReadView, exceldownload

urlpatterns = [
    *urls.default_model_paths(
        Report,
        browseview=views.BrowseView._with(
            columns=["name", "created"],
            rowclickaction=views.BrowseView.gen_rowclickaction("read"),
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
                Link(
                    href=ModelHref.from_object(hg.C("row"), "edit"),
                    iconname="edit",
                    label=_("Edit"),
                ),
                Link(
                    href=ModelHref.from_object(hg.C("row"), "excel"),
                    iconname="document",
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
        copyview=generate_copyview(
            Report, labelfield="name", copy_related_fields=("columns",)
        ),
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
            iconname="document",
        ),
        menu.Group(_("Reports"), iconname="document"),
    )
)
