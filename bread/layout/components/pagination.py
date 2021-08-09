import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from bread.utils.urls import link_with_urlparameters

from ..base import aslink_attributes
from .icon import Icon
from .select import Select


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
                    _("Items per page"),
                    ":",
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
                                            lambda c, i=i: c["request"].GET.get(
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
                        "onchange": "document.location = this.value",
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
                        lambda c: [
                            (
                                None,
                                [
                                    {
                                        "label": i,
                                        "value": linktopage(page_urlparameter, i),
                                        "attrs": {
                                            "selected": hg.F(
                                                lambda c, i=i: c["request"].GET.get(
                                                    page_urlparameter, "1"
                                                )
                                                == str(i)
                                            ),
                                        },
                                    }
                                    for i in hg.resolve_lazy(paginator, c).page_range
                                ],
                            )
                        ]
                    ),
                    inline=True,
                    widgetattributes={
                        "data_page_number_input": True,
                        "onchange": "document.location = this.value",
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
                    disabled=hg.F(
                        lambda c: not paginator.get_page(
                            int(c["request"].GET.get(page_urlparameter, "1"))
                        ).has_previous()
                    ),
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
                    disabled=hg.F(
                        lambda c: not paginator.get_page(
                            int(c["request"].GET.get(page_urlparameter, "1"))
                        ).has_next()
                    ),
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


def linktopage(page_urlparameter, page):
    return hg.F(
        lambda c: link_with_urlparameters(
            c["request"], **{page_urlparameter: hg.resolve_lazy(page, c)}
        )
    )


def linktorelativepage(page_urlparameter, direction, maxnum):
    """direction: number of pages to jump, e.g. -1 or 1"""
    return hg.F(
        lambda c: link_with_urlparameters(
            c["request"],
            **{
                page_urlparameter: int(c["request"].GET.get(page_urlparameter, "1"))
                + hg.resolve_lazy(direction, c)
            },
        )
    )


def linkwithitemsperpage(itemsperpage_urlparameter, itemsperpage, page_urlparameter):
    return hg.F(
        lambda c: link_with_urlparameters(
            c["request"],
            **{itemsperpage_urlparameter: itemsperpage, page_urlparameter: None},
        )
    )


def get_page(paginator, page_urlparameter):
    def wrapper(context):
        return paginator.get_page(
            int(context["request"].GET.get(page_urlparameter, "1"))
        )

    return hg.F(wrapper)
