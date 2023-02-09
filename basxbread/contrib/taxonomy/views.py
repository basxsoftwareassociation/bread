import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from basxbread import layout
from basxbread.utils import Link, ModelHref, link_with_urlparameters
from basxbread.views import BrowseView

from . import models


class TermsBrowseView(BrowseView):
    columns = [
        layout.datatable.DataTableColumn(
            models.Term._meta.get_field("term").verbose_name,
            hg.If(
                hg.C("row").disabled,
                hg.SPAN(hg.C("row").term, style="text-decoration: line-through;"),
                hg.C("row").term,
            ),
        ),
        "slug",
    ]

    def get_layout(self):
        ret = super().get_layout()
        has_disabled = "disabled" in self.request.GET
        url = link_with_urlparameters(
            self.request, **{"disabled": None if has_disabled else "true"}
        )
        ret[0].append(
            hg.DIV(
                hg.A(
                    hg.If(has_disabled, _("Hide disabled"), _("Show disabled")),
                    href=url,
                ),
                style="margin-top: 1rem",
            )
        )
        return ret

    def get(self, *args, **kwargs):
        vocabulary = models.Vocabulary.objects.filter(
            slug=self.request.GET.get("vocabulary_slug")
        ).first()
        if vocabulary:
            self.primary_button = layout.button.Button.from_link(
                Link(
                    href=ModelHref(
                        models.Term,
                        "add",
                        query={"vocabulary": vocabulary.id},
                        return_to_current=True,
                    ),
                    label=_("Add %s") % models.Term._meta.verbose_name,
                ),
                icon=layout.icon.Icon("add", size=20),
            )
        return super().get(*args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        if "disabled" in self.request.GET:
            qs = self.model.objects.including_disabled()
        vocabulary_slug = self.request.GET.get("vocabulary_slug")
        if vocabulary_slug:
            qs = qs.filter(vocabulary__slug=vocabulary_slug)

        return qs


class VocabularyBrowseView(BrowseView):
    columns = ["name", "slug", "termcount"]
    rowactions = [
        BrowseView.editlink(),
        Link(
            href=ModelHref(
                models.Term, "browse", query={"vocabulary_slug": hg.C("row").slug}
            ),
            label=_("Terms of vocabulary"),
            iconname="tree-view--alt",
        ),
    ]
