import htmlgenerator as hg

from bread import layout
from bread.layout.components.button import Button
from bread.layout.components.datatable import DataTable, DataTableColumn
from bread.layout.components.forms.widgets import BaseWidget, Checkbox


class MenuPicker(BaseWidget):
    """
    This widget is based on the existing widget for CheckboxSelectMultiple,
    that solve a problem when there are a large number of items to choose from
    """

    def __init__(
        self,
        max_height=20,  # the maximum height of the widget (in rem)
        label=None,
        help_text=None,
        errors=None,
        inputelement_attrs=None,
        boundfield=None,
        **attributes,
    ):
        inputelement_attrs = inputelement_attrs or {}
        widgetid = hg.html_id(self, "bread--menupicker")

        checkbox_column_base = (
            DataTableColumn(
                Checkbox(
                    inputelement_attrs={
                        "data_menuid": widgetid,
                        "onclick": "menuPickerSelectAllClick(this, event)",
                    },
                    _class="bread--menupicker__selectall",
                ),
                Checkbox(
                    inputelement_attrs={
                        "data_menuid": widgetid,
                        "data_name": hg.C("row").data["name"],
                        "data_value": hg.C("row").data["value"],
                    }
                ),
                td_attributes={"data_order": hg.C("row_index")},
            ),
        )

        column_style = "cursor: pointer;"
        column_context_label = hg.DIV(
            hg.C("row").data["label"],
            style=column_style,
        )

        checkbox_column_selected = checkbox_column_base + (
            DataTableColumn("Selected", column_context_label),
        )
        checkbox_column_unselected = checkbox_column_base + (
            DataTableColumn("Unselected", column_context_label),
        )

        checkboxes = boundfield.subwidgets

        def menupickerrow(columns):
            """Modified from DataTable.row(columns) with some additional features."""
            return hg.TR(
                *[
                    hg.TD(col.cell, lazy_attributes=col.td_attributes)
                    for col in columns
                ],
                style="cursor: pointer;",
                onclick="menuPickerRowClick(this, event)",
            )

        super().__init__(
            hg.Iterator(
                checkboxes,
                "item",
                hg.If(
                    hg.C("item").data["selected"],
                    hg.INPUT(
                        type="hidden",
                        name=hg.C("item").data["name"],
                        value=hg.C("item").data["value"],
                    ),
                ),
            ),
            hg.FIELDSET(
                label,
                errors,
                layout.grid.Grid(
                    layout.grid.Row(
                        # selected
                        layout.grid.Col(
                            hg.DIV(
                                DataTable(
                                    columns=checkbox_column_selected,
                                    row_iterator=hg.Iterator(
                                        checkboxes,
                                        "row",  # for backward-compatibility with datatable
                                        hg.If(
                                            hg.C("row").data["selected"],
                                            menupickerrow(checkbox_column_selected),
                                        ),
                                    ),
                                    _class="bx--data-table bx--data-table--sort bread--menupicker__table bread--menupicker__selected-table ",
                                    spacing="short",
                                    zebra=True,
                                ),
                                style=f"max-height: {max_height}rem;",
                                _class="bread--menupicker__table-container",
                            ),
                            breakpoint="lg",
                            width="7",
                        ),
                        layout.grid.Col(
                            hg.DIV(
                                Button(
                                    _class="bread--menupicker__add",
                                    data_menuid=widgetid,
                                    icon="add--alt",
                                    onclick="menuPickerAdd(this, event)",
                                    style="text-align: center; margin: 0.5rem;",
                                ),
                                Button(
                                    _class="bread--menupicker__remove",
                                    data_menuid=widgetid,
                                    icon="subtract--alt",
                                    onclick="menuPickerRemove(this, event)",
                                    style="text-align: center; margin: 0.5rem;",
                                ),
                                style=(
                                    "display: flex;"
                                    "flex-wrap: wrap;"
                                    "align-content: center;"
                                    "justify-content: space-evenly;"
                                    "align-items: center;"
                                    "padding: 1rem 0;"
                                ),
                            ),
                            breakpoint="lg",
                            width=2,
                        ),
                        # unselected
                        layout.grid.Col(
                            hg.DIV(
                                DataTable(
                                    columns=checkbox_column_unselected,
                                    row_iterator=hg.Iterator(
                                        checkboxes,
                                        "row",  # for backward-compatibility with datatable
                                        hg.If(
                                            hg.C("row").data["selected"],
                                            None,
                                            menupickerrow(checkbox_column_unselected),
                                        ),
                                    ),
                                    _class="bx--data-table bx--data-table--sort bread--menupicker__table bread--menupicker__unselected-table ",
                                    spacing="short",
                                    zebra=True,
                                ),
                                style=f"max-height: {max_height}rem;",
                                _class="bread--menupicker__table-container",
                            ),
                            breakpoint="lg",
                            width="7",
                        ),
                    ),
                    gutter=False,
                ),
                help_text,
            ),
            _class="bread--menupicker",
            id=widgetid,
            **attributes,
        ),
