import htmlgenerator as hg


# TODO: add method to connect Context-Switcher
class ContentSwitcher(hg.DIV):
    def __init__(self, *labels, selected=0, **wrapperkwargs):
        """
        labels: tuples in the form (label, button-attributes)
                button-attributes will be applied to the generated button for a context label
                data_target can be a CSS-selector of a panel for the according context
        """

        wrapperkwargs["_class"] = (
            wrapperkwargs.get("_class", "") + " bx--content-switcher"
        )
        super().__init__(
            *[
                hg.BUTTON(
                    hg.SPAN(label, _class="bx--content-switcher__label"),
                    _class="bx--content-switcher-btn"
                    + (" bx--content-switcher--selected" if i == selected else ""),
                    role="tab",
                    type="button",
                    **kwargs,
                )
                for i, (label, kwargs) in enumerate(labels)
            ],
            data_content_switcher=True,
            role="tablist",
            **wrapperkwargs,
        )
