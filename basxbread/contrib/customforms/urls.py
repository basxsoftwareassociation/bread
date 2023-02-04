import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from basxbread import layout, menu, utils
from basxbread import views as breadviews

from . import models, views

urlpatterns = [
    *utils.default_model_paths(
        models.CustomForm,
        browseview=breadviews.BrowseView._with(
            columns=["__all__", "customformfields"],
            rowactions=(
                breadviews.BrowseView.editlink(),
                breadviews.BrowseView.deletelink(),
                utils.Link(
                    href=utils.ModelHref.from_object(
                        hg.C("row"), "use", return_to_current=False
                    ),
                    label=_("Add form entry"),
                    iconname="new-tab",
                ),
            ),
        ),
        addview=breadviews.AddView._with(default_success_page="edit"),
        editview=breadviews.EditView._with(
            fields=[
                "title",
                "model",
                "pk_fields",
                layout.forms.Formset.as_inline_datatable(
                    "customformfields", ["fieldname", "label", "help_text"]
                ),
            ],
            default_success_page="edit",
        ),
        use=views.formview,
    ),
    *utils.default_model_paths(
        models.PDFImport,
        browseview=breadviews.BrowseView._with(
            rowactions=(
                breadviews.BrowseView.editlink(),
                breadviews.BrowseView.deletelink(),
                utils.Link(
                    href=utils.ModelHref.from_object(
                        hg.C("row"), "use", return_to_current=False
                    ),
                    label=_("Import new PDF"),
                    iconname="new-tab",
                ),
            ),
        ),
        addview=breadviews.AddView._with(
            fields=["pdf", "customform"], default_success_page="edit"
        ),
        editview=breadviews.EditView._with(
            fields=[
                "pdf",
                "customform",
                layout.forms.Formset.as_inline_datatable(
                    "fields", ["pdf_field_name", "customform_field"]
                ),
            ],
            default_success_page="edit",
        ),
        use=views.pdfimportview,
    ),
]

group = menu.Group(
    label=models.CustomForm._meta.verbose_name_plural, iconname="license--draft"
)
menu.registeritem(
    menu.Item(
        group=group,
        link=utils.Link(
            href=utils.ModelHref(models.CustomForm, "browse"),
            label=models.CustomForm._meta.verbose_name_plural,
            permissions=[
                f"{models.CustomForm._meta.app_label}.view_{models.CustomForm._meta.model_name}"
            ],
        ),
    )
)
menu.registeritem(
    menu.Item(
        group=group,
        link=utils.Link(
            href=utils.ModelHref(models.PDFImport, "browse"),
            label=models.PDFImport._meta.verbose_name_plural,
            iconname="document--import",
            permissions=[
                f"{models.PDFImport._meta.app_label}.view_{models.PDFImport._meta.model_name}"
            ],
        ),
    )
)
