import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from bread.menu import Link
from bread.utils import filter_fieldlist, pretty_modelname
from bread.utils.urls import reverse_model

from ..base import (ModelContext, ModelFieldLabel, ModelFieldValue, ModelName,
                    ObjectContext)
from .button import Button
from .icon import Icon
from .overflow_menu import OverflowMenu
from .search import Search


class DataTable(hg.BaseElement):
    def __init__(
        self,
        columns,
        row_iterator,
        valueproviderclass=hg.ValueProvider,
        spacing="default",
        zebra=False,
    ):
        """columns: tuple(header_expression, row_expression)
        if the header_expression/row_expression has an attribute td_attributes it will be used as attributes for the TH/TD elements (necessary because sometimes the content requires additional classes on the parent element)
        spacing: one of "default", "compact", "short", "tall"
        valueproviderclass: A class which implements ValueProvider which will be passed to the Iterator
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
                        hg.TR(
                            *[
                                hg.TD(cell, **getattr(cell, "td_attributes", {}))
                                for header, cell in columns
                            ]
                        ),
                        valueproviderclass,
                    )
                ),
                _class=" ".join(classes),
            )
        )

    @staticmethod
    def full(title, datatable, primary_button, helper_text=None):
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
                    hg.DIV(Search(), _class="bx--toolbar-search-container-expandable"),
                    primary_button,
                    _class="bx--toolbar-content",
                ),
                _class="bx--table-toolbar",
            ),
            datatable,
            _class="bx--data-table-container",
            data_table=True,
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
        if title is None:
            title = ModelName(plural=True)

        backquery = {"next": backurl} if backurl else {}
        if addurl is None:
            addurl = reverse_model(queryset.model, "add", query=backquery)

        if object_actions is None:
            object_actions = [
                Link.from_objectaction("edit", _("Edit"), "edit", query=backquery),
                Link.from_objectaction(
                    "delete", _("Delete"), "trash-can", query=backquery
                ),
            ]

        object_actions_menu = OverflowMenu(
            object_actions,
            menucontext=ObjectContext,
            iteratorclass=ObjectContext.Binding(hg.Iterator),
            flip=True,
            item_attributes={"_class": "bx--table-row--menu-option"},
        )
        # the data-table object will check child elements for td_attributes to fill in attributes for TD-elements
        object_actions_menu.td_attributes = {"_class": "bx--table-column-menu"}
        action_menu_header = hg.BaseElement()
        action_menu_header.td_attributes = {"_class": "bx--table-column-menu"}
        return ModelContext(
            queryset.model,
            DataTable.full(
                title,
                DataTable(
                    [
                        (ModelFieldLabel(field), ModelFieldValue(field))
                        for field in list(filter_fieldlist(queryset.model, fields))
                    ]
                    + [(None, object_actions_menu)],
                    # querysets are cache, the call to all will make a new query is used in every request
                    hg.F(lambda c, e: queryset.all()),
                    ObjectContext,
                ),
                Button(
                    _("Add %s") % pretty_modelname(queryset.model),
                    icon=Icon("add", size=20),
                    onclick=f"document.location = '{addurl}'",
                ),
            ),
        )
