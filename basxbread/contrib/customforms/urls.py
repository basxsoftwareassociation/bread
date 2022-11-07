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
                menu.Link(
                    href=utils.ModelHref.from_object(
                        hg.C("row"), "use", return_to_current=False
                    ),
                    label=_("Add form entry"),
                    iconname="new-tab",
                ),
            ),
        ),
        editview=breadviews.EditView._with(
            fields=[
                "title",
                "model",
                "pk_fields",
                layout.forms.Formset.as_inline_datatable(
                    "customformfields", ["fieldname", "label", "help_text"]
                ),
            ]
        ),
        use=views.formview,
    ),
]

menu.registeritem(
    menu.Item(
        group=models.CustomForm._meta.verbose_name_plural,
        link=menu.Link(
            href=utils.ModelHref(models.CustomForm, "browse"),
            label=models.CustomForm._meta.verbose_name_plural,
            iconname="license--draft",
        ),
    )
)
