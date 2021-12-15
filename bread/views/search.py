import htmlgenerator as hg
from django.db.models.loading import get_model
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from haystack.query import SearchQuerySet
from haystack.utils import Highlighter
from htmlgenerator import mark_safe

from bread import layout as layout
from bread.settings import required as settings
from bread.utils import aslayout, reverse_model

R = layout.grid.Row
C = layout.grid.Col

ITEM_CLASS = "search_result_item"
ITEM_LABEL_CLASS = "search_result_label"
ITEM_VALUE_CLASS = "search_result_value"


@aslayout
def generic_search(request, model):
    query = request.GET.get("q")

    highlight = CustomHighlighter(query)
    if not query or len(query) < settings.MIN_CHARACTERS_DYNAMIC_SEARCH:
        return HttpResponse("")

    model = get_model("basxconnect", model)
    query_set = (
        SearchQuerySet().models([model]).autocomplete(name_auto=query).filter(query)
    )

    def onclick(item):
        link = reverse_model(
            item,
            "edit",
            kwargs={"pk": item.pk},
        )
        return f"document.location = '{link}'"

    ret = _display_results(query_set, highlight, onclick)
    return HttpResponse(
        hg.BaseElement(
            hg.STYLE(
                mark_safe(
                    f"""
                    .{ITEM_CLASS}:hover {{
                        background-color: lightgray;
                    }}
                    """
                )
            ),
            hg.DIV(
                ret,
                _class="raised",
                style="margin-bottom: 1rem; padding: 16px 0 48px 48px; background-color: #fff",
            ),
        ).render({})
    )


def _display_results(query_set, highlight, onclick):
    if query_set.count() == 0:
        return _("No results")

    def _display_as_list_item(item):
        if item is None:
            # this happens if we have entries in the search-backend which have been deleted
            return hg.BaseElement()
        return hg.LI(
            hg.SPAN(
                mark_safe(highlight.highlight(item.personnumber)),
                style="width: 48px; display: inline-block",
                _class=ITEM_VALUE_CLASS,
            ),
            hg.SPAN(
                item.name,
                _class=ITEM_LABEL_CLASS,
                style="dispay:none;",
            ),
            " ",
            mark_safe(highlight.highlight(item.search_index_snippet())),
            style="cursor: pointer; padding: 8px 0;",
            onclick=onclick(item),
            # onmouseenter="this.style.backgroundColor = 'lightgray'",
            # onmouseleave="this.style.backgroundColor = 'initial'",
            _class=ITEM_CLASS,
        )

    result_list = [
        _display_as_list_item(search_result.object)
        for search_result in query_set[:25]
        if search_result and search_result.object
    ]

    return hg.UL(
        hg.LI(_("%s items found") % len(query_set), style="margin-bottom: 20px"),
        *result_list,
    )


class CustomHighlighter(Highlighter):
    def find_window(self, highlight_locations):
        return 0, self.max_length
