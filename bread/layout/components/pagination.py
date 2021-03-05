import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from ..base import aslink_attributes
from .icon import Icon
from .select import Select


def linktopage(page_urlparameter, page):
    def wrapper(context, element):
        urlparams = context["request"].GET.copy()
        urlparams[page_urlparameter] = hg.resolve_lazy(page, context, element)
        return context["request"].path + (
            f"?{urlparams.urlencode()}" if urlparams else ""
        )

    return hg.F(wrapper)


def linktorelativepage(page_urlparameter, direction, maxnum):
    """direction: number of pages to jump, e.g. -1 or 1"""

    def wrapper(context, element):
        try:
            currentpage = int(context["request"].GET.get(page_urlparameter, "1"))
        except ValueError:
            currentpage = 1
        nextpage = currentpage + hg.resolve_lazy(direction, context, element)
        urlparams = context["request"].GET.copy()
        if 0 < nextpage <= hg.resolve_lazy(maxnum, context, element):
            urlparams[page_urlparameter] = nextpage
        return context["request"].path + (
            f"?{urlparams.urlencode()}" if urlparams else ""
        )

    return hg.F(wrapper)


def linkwithitemsperpage(itemsperpage_urlparameter, itemsperpage, page_urlparameter):
    def wrapper(context, element):
        urlparams = context["request"].GET.copy()
        urlparams[itemsperpage_urlparameter] = itemsperpage
        if page_urlparameter in urlparams:
            del urlparams[page_urlparameter]
        return context["request"].path + (
            f"?{urlparams.urlencode()}" if urlparams else ""
        )

    return hg.F(wrapper)


def get_page(paginator, page_urlparameter):
    def wrapper(context, element):
        page = int(context["request"].GET.get(page_urlparameter, "1"))
        return paginator.get_page(page)

    return hg.F(wrapper)


class Pagination(hg.DIV):
    def __init__(
        self,
        paginator,
        items_per_page_options,
        page_urlparameter="page",
        itemsperpage_urlparameter="itemsperpage",
        **kwargs,
    ):
        select1_id = hg.html_id(self)
        select2_id = select1_id + "-n"
        kwargs["_class"] = kwargs.get("_class", "") + " bx--pagination"
        kwargs["data_pagination"] = True
        super().__init__(
            hg.DIV(
                hg.LABEL(
                    _("Items per page:"),
                    _class="bx--pagination__text",
                    _for=select1_id,
                ),
                Select(
                    [
                        (
                            None,
                            [
                                {
                                    "label": i,
                                    "value": linkwithitemsperpage(
                                        itemsperpage_urlparameter, i, page_urlparameter
                                    ),
                                    "attrs": {
                                        "selected": hg.F(
                                            lambda c, e, i=i: c["request"].GET.get(
                                                itemsperpage_urlparameter
                                            )
                                            == str(i)
                                        )
                                    },
                                }
                                for i in items_per_page_options
                            ],
                        )
                    ],
                    inline=True,
                    widgetattributes={
                        "data_items_per_page": True,
                        "onclick": "document.location = this.value",
                        "onauxclick": "window.open(this.value, '_blank')",
                    },
                    _class="bx--select__item-count",
                ),
                hg.SPAN(
                    hg.SPAN(
                        hg.getattr_lazy(
                            get_page(paginator, page_urlparameter), "start_index"
                        ),
                        " - ",
                        hg.getattr_lazy(
                            get_page(paginator, page_urlparameter), "end_index"
                        ),
                        data_displayed_item_range=True,
                    ),
                    " ",
                    _("of"),
                    " ",
                    hg.SPAN(
                        " ",
                        hg.getattr_lazy(paginator, "count"),
                        " ",
                        data_total_items=True,
                    ),
                    " ",
                    _("items"),
                    _class="bx--pagination__text",
                ),
                _class="bx--pagination__left",
            ),
            hg.DIV(
                Select(
                    hg.F(
                        lambda c, e: [
                            (
                                None,
                                [
                                    {
                                        "label": i,
                                        "value": linktopage(page_urlparameter, i),
                                        "attrs": {
                                            "selected": hg.F(
                                                lambda c, e, i=i: c["request"].GET.get(
                                                    page_urlparameter, "1"
                                                )
                                                == str(i)
                                            ),
                                        },
                                    }
                                    for i in hg.resolve_lazy(paginator, c, e).page_range
                                ],
                            )
                        ]
                    ),
                    inline=True,
                    widgetattributes={
                        "data_page_number_input": True,
                        "onclick": "document.location = this.value",
                        "onauxclick": "window.open(this.value, '_blank')",
                    },
                    _class="bx--select__page-number",
                ),
                hg.LABEL(
                    _("of"),
                    " ",
                    hg.getattr_lazy(paginator, "num_pages"),
                    " ",
                    _("pages"),
                    _class="bx--pagination__text",
                    _for=select2_id,
                ),
                hg.BUTTON(
                    Icon("caret--left", size=20, _class="bx--pagination__nav-arrow"),
                    _class="bx--pagination__button bx--pagination__button--backward",
                    tabindex="0",
                    type="button",
                    data_page_backward=True,
                    **aslink_attributes(
                        linktorelativepage(
                            page_urlparameter,
                            -1,
                            hg.getattr_lazy(paginator, "num_pages"),
                        )
                    ),
                ),
                hg.BUTTON(
                    Icon("caret--right", size=20, _class="bx--pagination__nav-arrow"),
                    _class="bx--pagination__button bx--pagination__button--forward",
                    tabindex="0",
                    type="button",
                    data_page_forward=True,
                    **aslink_attributes(
                        linktorelativepage(
                            page_urlparameter,
                            1,
                            hg.getattr_lazy(paginator, "num_pages"),
                        )
                    ),
                ),
                _class="bx--pagination__right",
            ),
            **kwargs,
        )
