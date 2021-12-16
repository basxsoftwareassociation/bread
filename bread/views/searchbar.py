import htmlgenerator as hg
from django.apps import apps
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from haystack.query import SearchQuerySet
from haystack.utils import Highlighter
from htmlgenerator import mark_safe

from bread import layout as layout
from bread.utils import get_field_queryset, reverse_model

from ..settings import required as settings

R = layout.grid.Row
C = layout.grid.Col

ITEM_CLASS = "search_result_item"
ITEM_LABEL_CLASS = "search_result_label"
ITEM_VALUE_CLASS = "search_result_value"


def search(request, app: str, model: str):
    query = request.GET.get("q")

    highlight = CustomHighlighter(query)
    if not query or len(query) < settings.MIN_CHARACTERS_DYNAMIC_SEARCH:
        return HttpResponse("")

    model = apps.get_model(app, model)
    query_set = get_field_queryset(model._meta.fields, (query,))
    print(query_set)
    query_set = model.objects.filter(query_set)
    print(query_set)

    def onclick(item):
        link = reverse_model(
            item,
            "edit",
            kwargs={"pk": item.pk},
        )
        return f"document.location = '{link}'"

    ret = _display_results(query_set, highlight, onclick)
    return HttpResponse(
        hg.DIV(
            ret,
            _class="raised",
            style="margin-bottom: 1rem; padding: 16px 0 48px 48px; background-color: #fff",
        ).render({})
    )


def _display_results(query_set, highlight, onclick):
    if not query_set:
        return _("No results")

    def _display_as_list_item(item):
        if item is None:
            # this happens if we have entries in the search-backend which have been deleted
            return hg.BaseElement()

        return hg.LI(
            hg.SPAN(
                mark_safe(highlight.highlight(item.pk)),
                style="width: 48px; display: inline-block",
                _class=ITEM_VALUE_CLASS,
            ),
            hg.SPAN(
                str(item),
                _class=ITEM_LABEL_CLASS,
                style="dispay:none;",
            ),
            " ",
            # mark_safe(highlight.highlight(item.search_index_snippet())),
            style="cursor: pointer; padding: 8px 0;",
            onclick=onclick(item),
            onmouseenter="this.style.backgroundColor = 'lightgray'",
            onmouseleave="this.style.backgroundColor = 'initial'",
            _class=ITEM_CLASS,
        )

    result_list = [
        _display_as_list_item(search_result)
        for search_result in query_set[:25]
        # if search_result and search_result.object
    ]

    return hg.UL(
        hg.LI(_("%s items found") % len(query_set), style="margin-bottom: 20px"),
        *result_list,
    )


class CustomHighlighter(Highlighter):
    def find_window(self, highlight_locations):
        return (0, self.max_length)
