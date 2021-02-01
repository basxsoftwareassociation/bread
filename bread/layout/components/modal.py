import htmlgenerator as hg

from .icon import Icon


class Modal(hg.DIV):
    def __init__(
        self, heading, *content, label="", size="md", buttons=(), id=None, **attributes
    ):
        """
        heading: Modal title
        content: content elements of the modal, can be empty
        label: small informative label above heading
        size: one of ["xs", "sm", "md", "lg"]
        buttons: buttons displayed on bottom of modal, last button has default focus
                 the attribute "data_modal_close" can be set on an button in order to make it a cancel button
        """
        assert size in ["xs", "sm", "md", "lg"]
        if buttons and "data_modal_primary_focus" not in buttons[-1].attributes:
            buttons[-1].attributes["data_modal_primary_focus"] = True
        self.id = id or hg.html_id(self, prefix="modal-")
        super().__init__(
            hg.DIV(
                hg.DIV(
                    hg.P(
                        label,
                        _class="bx--modal-header__label bx--type-delta",
                    ),
                    hg.P(
                        heading,
                        _class="bx--modal-header__heading bx--type-beta",
                    ),
                    hg.BUTTON(
                        Icon(
                            "close",
                            size=16,
                            _class="bx--modal-close__icon",
                            aria_hidden="true",
                        ),
                        _class="bx--modal-close",
                        type="button",
                        data_modal_close=True,
                    ),
                    _class="bx--modal-header",
                ),
                hg.DIV(*content, _class="bx--modal-content", tabindex="0"),
                hg.DIV(
                    *buttons,
                    _class="bx--modal-footer",
                )
                if buttons
                else "",
                _class=f"bx--modal-container  bx--modal-container--{size}",
            ),
            #  Note: focusable span allows for focus wrap feature within Modals ,
            hg.SPAN(tabindex="0"),
            data_modal=True,
            id=self.id,
            _class="bx--modal",
            role="dialog",
            aria_modal="true",
            tabindex="-1",
        )

    def withopenbutton(self, button):
        button.attributes["data_modal_target"] = f"#{self.id}"
        return hg.DIV(button, self)
