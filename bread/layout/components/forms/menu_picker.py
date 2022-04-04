import htmlgenerator as hg
from django.forms import widgets

from bread import layout
from bread.layout.components.button import Button
from bread.layout.components.datatable import DataTable, DataTableColumn
from bread.layout.components.forms.widgets import BaseWidget, Checkbox


class MenuPicker(BaseWidget):
    django_widget = widgets.CheckboxSelectMultiple

    def __init__(
        self,
        name: str = None,
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
                        "_class": "bread--menupicker__selectall",
                        "data_menuid": widgetid,
                        "onclick": "menuPickerSelectAllClick(this)",
                    }
                ),
                Checkbox(
                    inputelement_attrs={
                        "name": hg.C("row").data["name"],
                        "value": hg.C("row").data["value"],
                    }
                ),
                td_attributes={"data_order": hg.C("row_index")},
            ),
        )

        checkbox_column_selected = checkbox_column_base + (
            DataTableColumn("Selected", hg.DIV(hg.C("row").data["label"])),
        )
        checkbox_column_unselected = checkbox_column_base + (
            DataTableColumn("Unselected", hg.DIV(hg.C("row").data["label"])),
        )

        checkboxes = boundfield.subwidgets

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
            layout.grid.Grid(
                layout.grid.Row(
                    # selected
                    layout.grid.Col(
                        DataTable(
                            columns=checkbox_column_selected,
                            row_iterator=hg.Iterator(
                                checkboxes,
                                "row",  # for backward-compatibility with datatable
                                hg.If(
                                    hg.C("row").data["selected"],
                                    DataTable.row(checkbox_column_selected),
                                ),
                            ),
                            _class="bx--data-table bx--data-table--sort bread--menupicker__selected-table ",
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
                                onclick="menuPickerAdd(this)",
                                style="text-align: center; margin: 0.5rem;",
                            ),
                            Button(
                                _class="bread--menupicker__remove",
                                data_menuid=widgetid,
                                icon="subtract--alt",
                                onclick="menuPickerRemove(this)",
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
                        DataTable(
                            columns=checkbox_column_unselected,
                            row_iterator=hg.Iterator(
                                checkboxes,
                                "row",  # for backward-compatibility with datatable
                                hg.If(
                                    hg.C("row").data["selected"],
                                    None,
                                    DataTable.row(checkbox_column_unselected),
                                ),
                            ),
                            _class="bx--data-table bx--data-table--sort bread--menupicker__unselected-table ",
                        ),
                        breakpoint="lg",
                        width="7",
                    ),
                ),
            ),
            _class="bread--menupicker",
            id=widgetid,
            onload="menuPickerLoad(this);",
            **attributes,
        )
