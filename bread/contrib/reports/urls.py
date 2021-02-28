import htmlgenerator as hg
from django.urls import path
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from bread import menu, views
from bread.utils import urls

from .models import Report


class EditView(views.EditView):
    fields = ["filter"]

    def layout(self, request):
        ret = super().layout(request)
        ret.append(hg.C("object.preview"))
        return ret


urlpatterns = [
    *urls.default_model_paths(
        Report,
        browseview=views.BrowseView._with(rowclickaction="read"),
        addview=views.AddView._with(fields=["model"]),
        editview=EditView,
        readview=EditView,
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
