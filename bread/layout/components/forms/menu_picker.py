import htmlgenerator as hg

from bread import layout
from bread.layout.components.button import Button
from bread.layout.components.datatable import DataTable, DataTableColumn
from bread.layout.components.forms.widgets import (
    BaseWidget,
    Checkbox,
    _gen_optgroup,
    _optgroups_from_choices,
)


class MenuPicker(BaseWidget):
    """
    A tool that let users select multiple items from a list of available items.
    This tool might be the good replacement for filters when the number of items
    is large.
    """

    def __init__(
        self,
        available_items: dict,
        selected_items: dict = None,
        max_visible_rows: int = 5,
        label=None,
        help_text=None,
        errors=None,
        inputelement_attrs=None,
        boundfield=None,
        choices=None,
        **attributes,
    ):
        """
        Constructor based on hg.DIV, that will be rendered to an HTML element
        that functions as a menu picker.

        Parameters
        ----------
        available_items : dict
            a list containing tuples in the form
            {
                'input_name1': {
                    'value1': 'label_for_value1',
                    'value2': 'label_for_value1',
                    ...
                },
                'input_name2': {
                    'value3': 'label_for_value3',
                    'value4': 'label_for_value4',
                    ...
                },
                ...
            }
            note that the key order depends on the insertion order.
        selected_items : dict, optional
            a list (or dict) in accordance with `available_items` but for pre-selected
            items that need to be displayed as selected by default. `selected_items`
            has to be defined in the same form as `available_items`
        """

        inputelement_attrs = inputelement_attrs or {}
        optgroups = (
            _optgroups_from_choices(
                choices,
                name=inputelement_attrs.get("name"),
                value=inputelement_attrs.get("value"),
            )
            if choices
            else _gen_optgroup(boundfield)
        )

        id = hg.html_id(self, "bread--menupicker")
        selected_items = selected_items or {}
        unselected_items = {}
        for name in available_items:
            unselected_items[name] = available_items[name].copy()
            if name in selected_items:
                for key in selected_items[name]:
                    if key in unselected_items[name]:
                        del unselected_items[name][key]

        checkbox_column = (
            DataTableColumn(
                Checkbox(
                    inputelement_attrs={
                        "_class": "bread--menupicker__selectall",
                        "readonly": True,
                    }
                ),
                Checkbox(
                    inputelement_attrs={
                        "name": hg.C("row.name"),
                        "value": hg.C("row.value"),
                        "readonly": True,
                    }
                ),
                td_attributes={"data_order": hg.C("row.order")},
            ),
        )

        super().__init__(
            # menu_picker is required to be in form in order to make this works.
            hg.Iterator(
                [
                    {"name": n, "value": v}
                    for n, vdict in selected_items.items()
                    for v in vdict
                ],
                "item",
                hg.INPUT(
                    type="hidden", name=hg.C("item.name"), value=hg.C("item.value")
                ),
            ),
            layout.grid.Grid(
                layout.grid.Row(
                    # selected
                    layout.grid.Col(
                        DataTable(
                            columns=checkbox_column
                            + (DataTableColumn("Selected", hg.DIV(hg.C("row.label"))),),
                            row_iterator=[
                                {
                                    "name": name,
                                    "value": value,
                                    "label": label,
                                    "order": i,
                                }
                                for i, (name, value, label) in enumerate(
                                    (n, v, l)
                                    for n, vdict in selected_items.items()
                                    for v, l in vdict.items()
                                )
                            ],
                            _class="bx--data-table bx--data-table--sort bread--menupicker__selected-table ",
                        ),
                        breakpoint="lg",
                        width=7,
                    ),
                    layout.grid.Col(
                        hg.DIV(
                            Button(
                                _class="bread--menupicker__add",
                                data_menuid=id,
                                icon="add--alt",
                                onclick="window.menuPickerAdd(this)",
                                style="text-align: center; margin: 0.5rem;",
                            ),
                            Button(
                                _class="bread--menupicker__remove",
                                icon="subtract--alt",
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
                    layout.grid.Col(
                        DataTable(
                            columns=checkbox_column
                            + (
                                DataTableColumn(
                                    "Unselected", hg.DIV(hg.C("row.label"))
                                ),
                            ),
                            row_iterator=[
                                {
                                    "name": name,
                                    "value": value,
                                    "label": label,
                                    "order": i,
                                }
                                for i, (name, value, label) in enumerate(
                                    (n, v, l)
                                    for n, vdict in unselected_items.items()
                                    for v, l in vdict.items()
                                )
                            ],
                            _class="bx--data-table bx--data-table--sort bread--menupicker__unselected-table ",
                        ),
                        breakpoint="lg",
                        width=7,
                    ),
                ),
            ),
            _class="bread--menupicker",
            id=id,
        )