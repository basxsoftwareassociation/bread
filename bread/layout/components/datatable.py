import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from bread.menu import Action, Link
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
        rowvariable="row",
        spacing="default",
        zebra=False,
        canselect=False,
    ):
        """columns: tuple(header_expression, row_expression)
        row_iterator: python iterator of htmlgenerator.Lazy object which returns an iterator
        rowvariable: name of the current object passed to childrens context
        if the header_expression/row_expression has an attribute td_attributes it will be used as attributes for the TH/TD elements (necessary because sometimes the content requires additional classes on the parent element)
        spacing: one of "default", "compact", "short", "tall"
        zebra: alternate row colors
        canselect: show checkboxes on leftmost column to select items
        """
        assert spacing in ["default", "compact", "short", "tall"]
        classes = ["bx--data-table"]
        if spacing != "default":
            classes.append(f"bx--data-table--{spacing}")
        if zebra:
            classes.append("bx--data-table--zebra")
        selecthead = []
        selectcol = []
        checkboxallid = f"datatable-check-{hg.html_id(self)}"
        if canselect:
            selecthead.append(
                hg.TH(
                    hg.INPUT(
                        data_event="select-all",
                        id=checkboxallid,
                        _class="bx--checkbox",
                        type="checkbox",
                        name="checkbox",
                        value="all",
                    ),
                    hg.LABEL(
                        _for=checkboxallid,
                        _class="bx--checkbox-label",
                    ),
                    _class="bx--table-column-checkbox",
                )
            )
            selectcol.append(
                hg.TD(
                    hg.INPUT(
                        data_event="select",
                        id=hg.BaseElement(
                            checkboxallid,
                            "-",
                            hg.F(lambda c, e: hg.html_id(c[rowvariable])),
                        ),
                        _class="bx--checkbox",
                        type="checkbox",
                        name="checkbox",
                        value=hg.If(
                            hg.F(lambda c, e: hasattr(c[rowvariable], "pk")),
                            hg.C(f"{rowvariable}.pk"),
                            hg.C(f"{rowvariable}_index"),
                        ),
                    ),
                    hg.LABEL(
                        _for=hg.BaseElement(
                            checkboxallid,
                            "-",
                            hg.F(lambda c, e: hg.html_id(c[rowvariable])),
                        ),
                        _class="bx--checkbox-label",
                        aria_label="Label name",
                    ),
                    _class="bx--table-column-checkbox",
                )
            )

        super().__init__(
            hg.TABLE(
                hg.THEAD(
                    hg.TR(
                        *(
                            selecthead
                            + [
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
                    )
                ),
                hg.TBODY(
                    hg.Iterator(
                        row_iterator,
                        rowvariable,
                        hg.TR(
                            *(
                                selectcol
                                + [
                                    hg.TD(cell, **getattr(cell, "td_attributes", {}))
                                    for header, cell in columns
                                ]
                            )
                        ),
                    )
                ),
                _class=" ".join(classes),
            )
        )

    def wrap(
        self,
        title,
        helper_text=None,
        primary_button=None,
        searchurl=None,
        queryfieldname=None,
        bulkactions=(),
    ):
        """
        wrap this datatable with title and toolbar
        title: table title
        helper_text: sub title
        primary_button: bread.layout.button.Button instance
        searchurl: url to which values entered in the searchfield should be submitted
        queryfieldname: name of the query field for the searchurl which contains the entered text
        bulkactions: List of bread.menu.Action or bread.menu.Link instances
                     bread.menu.Link will send a post or a get (depending on its "method" attribute) to the target url
                     the sent data will be a form with the selected checkboxes as fields
                     if the head-checkbox has been selected only that field will be selected
        """
        header = [hg.H4(title, _class="bx--data-table-header__title")]
        if helper_text:
            header.append(
                hg.P(helper_text, _class="bx--data-table-header__description")
            )
        resultcontainerid = f"datatable-search-{hg.html_id(self)}"
        bulkactionlist = []
        for action in bulkactions:
            if isinstance(action, Link):
                action = Action(
                    js=hg.BaseElement(
                        "submitbulkaction(this.closest('[data-table]'), '",
                        action.url,
                        f"', method='{getattr(action, 'method', 'GET')}')",
                    ),
                    label=action.label,
                    icon=action.icon,
                    permissions=action._permissions,
                )
                bulkactionlist.append(Button.fromaction(action))
            elif isinstance(action, Action):
                bulkactionlist.append(Button.fromaction(action))
            else:
                RuntimeError(f"bulkaction needs to be {Action} or {Link}")

        return hg.DIV(
            hg.DIV(*header, _class="bx--data-table-header"),
            hg.SECTION(
                hg.DIV(
                    hg.DIV(
                        *(
                            bulkactionlist
                            + [
                                Button(
                                    _("Cancel"),
                                    data_event="action-bar-cancel",
                                    _class="bx--batch-summary__cancel",
                                )
                            ]
                        ),
                        _class="bx--action-list",
                    ),
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
                    hg.DIV(
                        Search().withajaxurl(
                            url=searchurl,
                            queryfieldname=queryfieldname,
                            resultcontainerid=resultcontainerid,
                            resultcontainer=False,
                        ),
                        _class="bx--toolbar-search-container-expandable",
                    )
                    if searchurl
                    else "",
                    primary_button or "",
                    _class="bx--toolbar-content",
                ),
                _class="bx--table-toolbar",
            ),
            hg.DIV(
                hg.DIV(
                    id=resultcontainerid,
                    _style="width: 100%; position: absolute; z-index: 999",
                ),
                style="width: 100%; position: relative",
            ),
            self,
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

        return DataTable(
            [
                (fieldlabel(model, field), FC(f"row.{field}"))
                for field in list(filter_fieldlist(model, fields))
            ]
            + ([(None, object_actions_menu)] if object_actions else []),
            # querysets are cached, the call to all will make sure a new query is used in every request
            hg.F(lambda c, e: queryset),
        ).wrap(
            title,
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
