from django.utils.translation import gettext_lazy as _

from basxbread import menu
from basxbread.utils import Link, default_model_paths, reverse_model
from basxbread.views import AddView, DeleteView, EditView

from .models import Term, Vocabulary
from .views import TermsBrowseView, VocabularyBrowseView

urlpatterns = [
    *default_model_paths(
        Vocabulary,
        addview=AddView._with(fields=["name", "slug"]),
        editview=EditView._with(fields=["name"]),
        browseview=VocabularyBrowseView,
    ),
    *default_model_paths(
        Term,
        addview=AddView._with(fields=["term", "vocabulary", "slug"]),
        editview=EditView._with(
            fields=["term", "disabled"], queryset=Term.objects.including_disabled()
        ),
        deleteview=DeleteView._with(softdeletefield="disabled"),
        browseview=TermsBrowseView,
    ),
]


menu.registeritem(
    menu.Item(
        Link(
            reverse_model(Vocabulary, "browse"),
            label=_("Taxonomy"),
        ),
        menu.settingsgroup,
    )
)
