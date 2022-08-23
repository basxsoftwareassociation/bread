import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from basxbread import layout
from basxbread.utils import Link, ModelHref
from basxbread.views import BrowseView

from . import models


class TermsBrowseView(BrowseView):
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
        vocabulary_slug = self.request.GET.get("vocabulary_slug")
        if vocabulary_slug:
            qs = qs.filter(vocabulary__slug=vocabulary_slug)
        return qs


class VocabularyBrowseView(BrowseView):
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
