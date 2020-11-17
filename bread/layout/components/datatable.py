import plisplate


class DataTable(plisplate.BaseElement):
    def __init__(
        self,
        columns,
        row_iterator,
        valueproviderclass,
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
            plisplate.TABLE(
                plisplate.THEAD(
                    plisplate.TR(
                        *[
                            plisplate.TH(
                                plisplate.SPAN(
                                    column[0],
                                    _class="bx--table-header-label",
                                ),
                                **getattr(column[1], "td_attributes", {}),
                            )
                            for column in columns
                        ]
                    )
                ),
                plisplate.TBODY(
                    plisplate.Iterator(
                        row_iterator,
                        valueproviderclass,
                        plisplate.TR(
                            *[
                                plisplate.TD(
                                    column[1], **getattr(column[1], "td_attributes", {})
                                )
                                for column in columns
                            ]
                        ),
                    )
                ),
                _class=" ".join(classes),
            )
        )
