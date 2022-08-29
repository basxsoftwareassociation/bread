from basxbread import menu
from basxbread.utils import Link, default_model_paths, reverse_model
from basxbread.views import AddView, BrowseView, EditView

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
        editview=EditView._with(fields=["term"]),
        browseview=TermsBrowseView._with(
            rowclickaction=BrowseView.gen_rowclickaction("edit", return_to_current=True)
        ),
    ),
]


menu.registeritem(
    menu.Item(
        Link(
            reverse_model(Vocabulary, "browse"),
            Vocabulary._meta.verbose_name_plural,
        ),
        menu.settingsgroup,
    )
)
