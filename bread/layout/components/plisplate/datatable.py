import plisplate


class DataTable(plisplate.DIV):
    def __init__(
        self, columns, row_iterator, valueproviderclass, spacing="default", zebra=False,
    ):
        """columns: tuple(header_expression, row_expression)
        spacing: one of "default", "compact", "short", "tall"
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
                                    column[0], _class="bx--table-header-label",
                                )
                            )
                            for column in columns
                        ]
                    )
                ),
                plisplate.TBODY(
                    plisplate.Iterator(
                        row_iterator,
                        valueproviderclass,
                        plisplate.TR(*[plisplate.TD(column[1]) for column in columns]),
                    )
                ),
                _class=" ".join(classes),
            )
        )
