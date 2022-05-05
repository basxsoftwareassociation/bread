from typing import Iterator, NamedTuple

import htmlgenerator as hg
from django.core.paginator import Paginator
from django.utils.translation import gettext_lazy as _

from bread.utils.urls import link_with_urlparameters

from ..utils import aslink_attributes
from .forms.widgets import Select
from .icon import Icon


class PaginationConfig(NamedTuple):
    paginator: Paginator
    items_per_page_options: Iterator
    page_urlparameter: str = (
        "page"  # URL parameter which holds value for current page selection
    )
    itemsperpage_urlparameter: str = (
        "itemsperpage"  # URL parameter which selects items per page
    )


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
                    choices=[
                        (
                            linkwithitemsperpage(
                                itemsperpage_urlparameter,
                                page_urlparameter,
                                itemsperpage=i,
                            ),
                            _("All") if i == -1 else i,
                        )
                        for i in items_per_page_options
                    ],
                    inline=True,
                    inputelement_attrs={
                        "data_items_per_page": True,
                        "onchange": "document.location = this.value",
                        "onauxclick": "window.open(this.value, '_blank')",
                        "value": linkwithitemsperpage(
                            itemsperpage_urlparameter,
                            page_urlparameter,
                        ),
                    },
                    _class="bx--select__item-count",
                ),
                hg.SPAN(
                    hg.SPAN(
                        hg.format(
                            "{} - {}",
                            get_page(paginator, page_urlparameter).start_index(),
                            get_page(paginator, page_urlparameter).end_index(),
                        ),
                        data_displayed_item_range=True,
                    ),
                    " ",
                    _("of"),
                    " ",
                    hg.SPAN(
                        hg.format(" {} ", paginator.count),
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
                    choices=[
                        (linktopage(page_urlparameter, i), i)
                        for i in paginator.page_range
                    ],
                    inline=True,
                    inputelement_attrs={
                        "data_page_number_input": True,
                        "onchange": "document.location = this.value",
                        "onauxclick": "window.open(this.value, '_blank')",
                        "value": linktopage(
                            page_urlparameter,
                            hg.C("request").GET.get(page_urlparameter, "1"),
                        ),
                    },
                    _class="bx--select__page-number",
                ),
                hg.LABEL(
                    _("of"),
                    " ",
                    paginator.num_pages,
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
                            paginator.num_pages,
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
                            paginator.num_pages,
                        )
                    ),
                ),
                _class="bx--pagination__right",
            ),
            **kwargs,
        )

    @classmethod
    def from_config(cls, pagination_config):
        return cls(
            paginator=pagination_config.paginator,
            items_per_page_options=pagination_config.items_per_page_options,
            page_urlparameter=pagination_config.page_urlparameter,
            itemsperpage_urlparameter=pagination_config.itemsperpage_urlparameter,
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


def linkwithitemsperpage(
    itemsperpage_urlparameter, page_urlparameter, itemsperpage=None
):
    return hg.F(
        lambda c: link_with_urlparameters(
            c["request"],
            **{
                itemsperpage_urlparameter: itemsperpage
                or c["request"].GET.get(itemsperpage_urlparameter),
                page_urlparameter: None,
            },
        )
    )


def get_page(paginator, page_urlparameter):
    def wrapper(context):
        return paginator.get_page(
            int(context["request"].GET.get(page_urlparameter, "1"))
        )

    return hg.F(wrapper)
