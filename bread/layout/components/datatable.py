import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from bread.utils import filter_fieldlist, pretty_modelname
from bread.utils.urls import reverse_model

from ..base import FC, fieldlabel
from .button import Button
from .icon import Icon
from .overflow_menu import OverflowMenu
from .search import Search


class DataTable(hg.BaseElement):
    def __init__(
        self,
        columns,
        row_iterator,
        row_variable="row",
        spacing="default",
        zebra=False,
    ):
        """columns: tuple(header_expression, row_expression)
        row_iterator: python iterator of htmlgenerator.Lazy object which returns an iterator
        row_variable: name of the current object passed to childrens context
        if the header_expression/row_expression has an attribute td_attributes it will be used as attributes for the TH/TD elements (necessary because sometimes the content requires additional classes on the parent element)
        spacing: one of "default", "compact", "short", "tall"
        """
        assert spacing in ["default", "compact", "short", "tall"]
        classes = ["bx--data-table"]
        if spacing != "default":
            classes.append(f"bx--data-table--{spacing}")
        if zebra:
            classes.append("bx--data-table--zebra")
        super().__init__(
            hg.TABLE(
                hg.THEAD(
                    hg.TR(
                        *[
                            hg.TH(
                                hg.SPAN(
                                    header,
                                    _class="bx--table-header-label",
                                ),
                                **getattr(header, "td_attributes", {}),
                            )
                            for header, cell in columns
                        ]
                    )
                ),
                hg.TBODY(
                    hg.Iterator(
                        row_iterator,
                        row_variable,
                        hg.TR(
                            *[
                                hg.TD(cell, **getattr(cell, "td_attributes", {}))
                                for header, cell in columns
                            ]
                        ),
                    )
                ),
                _class=" ".join(classes),
            )
        )

    @staticmethod
    def full(
        title, datatable, primary_button=None, search_urlname=None, helper_text=None
    ):
        header = [hg.H4(title, _class="bx--data-table-header__title")]
        if helper_text:
            header.append(
                hg.P(helper_text, _class="bx--data-table-header__description")
            )

        return hg.DIV(
            hg.DIV(*header, _class="bx--data-table-header"),
            hg.SECTION(
                hg.DIV(
                    hg.DIV(_class="bx--action-list"),
                    hg.DIV(
                        hg.P(
                            hg.SPAN(0, data_items_selected=True),
                            _(" items selected"),
                            _class="bx--batch-summary__para",
                        ),
                        _class="bx--batch-summary",
                    ),
                    _class="bx--batch-actions",
                    aria_label=_("Table Action Bar"),
                ),
                hg.DIV(
                    hg.DIV(Search(), _class="bx--toolbar-search-container-expandable")
                    if search_urlname
                    else "",
                    primary_button or "",
                    _class="bx--toolbar-content",
                ),
                _class="bx--table-toolbar",
            ),
            datatable,
            _class="bx--data-table-container",
            data_table=True,
        )

    @staticmethod
    def from_model(
        model,
        queryset=None,
        fields=["__all__"],
        object_actions=None,
        title=None,
        addurl=None,
        backurl=None,
    ):
        if title is None:
            title = pretty_modelname(model, plural=True)

        backquery = {"next": backurl} if backurl else {}
        if addurl is None:
            addurl = reverse_model(model, "add", query=backquery)

        object_actions_menu = OverflowMenu(
            object_actions,
            flip=True,
            item_attributes={"_class": "bx--table-row--menu-option"},
        )
        # the data-table object will check child elements for td_attributes to fill in attributes for TD-elements
        object_actions_menu.td_attributes = {"_class": "bx--table-column-menu"}
        action_menu_header = hg.BaseElement()
        action_menu_header.td_attributes = {"_class": "bx--table-column-menu"}
        queryset = model.objects.all() if queryset is None else queryset

        return DataTable.full(
            title,
            DataTable(
                [
                    (fieldlabel(model, field), FC(f"row.{field}"))
                    for field in list(filter_fieldlist(model, fields))
                ]
                + ([(None, object_actions_menu)] if object_actions else []),
                # querysets are cached, the call to all will make sure a new query is used in every request
                hg.F(lambda c, e: queryset),
            ),
            Button(
                _("Add %s") % pretty_modelname(model),
                icon=Icon("add", size=20),
                onclick=f"document.location = '{addurl}'",
            ),
        )

    @staticmethod
    def from_queryset(
        queryset,
        fields=["__all__"],
        object_actions=None,
        title=None,
        addurl=None,
        backurl=None,
    ):
        return DataTable.from_model(
            queryset.model,
            queryset=queryset,
            fields=fields,
            object_actions=object_actions,
            title=title,
            addurl=addurl,
            backurl=backurl,
        )
