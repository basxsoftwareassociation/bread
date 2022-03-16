from typing import Iterable, Union

import htmlgenerator as hg

from bread import layout
from bread.layout.components.datatable import DataTable, DataTableColumn
from bread.layout.components.forms.widgets import Checkbox


class MenuPicker(hg.DIV):
    """
    A tool that let users select multiple items from a list of available items.
    This tool might be the good replacement for filters when the number of items
    is large.
    """

    def __init__(
        self,
        available_items: dict,
        selected_items: dict = None,
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
            has to be defined in this form.
            {
                'input_name1': {'value1', 'value2', ...},
                'input_name2': {'value3', 'value4', ...},
                ...
            }
            **however, the same form as `available_items` is also accepted as well
            if necessary.**
        """

        input_name: str
        available_items: Union[Iterable, dict]
        selected_items: Union[Iterable, dict]

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
                                    for n, vdict in available_items.items()
                                    for v, l in vdict.items()
                                )
                            ],
                            _class="bread--menupicker__selected-table",
                        ),
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
                                {"name": name, "value": value, "label": label}
                                for name, value_dict in available_items.items()
                                for value, label in value_dict.items()
                            ],
                            _class="bread--menupicker__unselected-table",
                        ),
                    ),
                ),
            ),
            _class="bread--menupicker",
        )
