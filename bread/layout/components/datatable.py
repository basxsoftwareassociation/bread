import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from ...utils import filter_fieldlist, pretty_modelname
from ..base import (
    ModelContext,
    ModelFieldLabel,
    ModelFieldValue,
    ModelName,
    ObjectContext,
)
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
                                    column[0],
                                    _class="bx--table-header-label",
                                ),
                                **getattr(column[1], "td_attributes", {}),
                            )
                            for column in columns
                        ]
                    )
                ),
                hg.TBODY(
                    hg.Iterator(
                        row_iterator,
                        hg.TR(
                            *[
                                hg.TD(
                                    column[1], **getattr(column[1], "td_attributes", {})
                                )
                                for column in columns
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
        header = [hg.H4(title)]
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
    def from_queryset(queryset, fields=["__all__"], title=None, addurl=None):
        from ...admin import site

        if title is None:
            title = ModelName(plural=True)
        if addurl is None:
            addurl = site.get_default_admin(queryset.model).reverse("add")

        def get_object_actions(element, context):

            return site.get_default_admin(element.object).object_actions(
                context["request"], element.object
            )

        object_actions_menu = OverflowMenu(
            hg.F(get_object_actions),
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
                    queryset,
                    ObjectContext,
                ),
                Button(
                    _("Add %s") % pretty_modelname(queryset.model),
                    icon=Icon("add", size=20),
                    onclick=f"document.location = '{addurl}'",
                ),
            ),
        )
