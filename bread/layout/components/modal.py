import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from .button import Button
from .icon import Icon
from .loading import Loading


class Modal(hg.DIV):
    SIZES = ["xs", "sm", "md", "lg"]

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

        In order to open the modal just pass self.openerattributes as kwargs to another html element, e.g. a button

            modal = modal.Modal("My Modal", "Hello world")
            button.Button("Model", **modal.openerattributes)

        """
        if size not in Modal.SIZES:
            raise ValueError(
                f"argument 'size' has value {size} but needs to be one of {Modal.SIZES}"
            )
        if buttons and "data_modal_primary_focus" not in buttons[-1].attributes:
            buttons[-1].attributes["data_modal_primary_focus"] = True
        attributes["_class"] = attributes.get("_class", "") + " bx--modal"
        self.id = id or hg.html_id(self, prefix="modal-")
        self.openerattributes = {"data_modal_target": f"#{self.id}"}
        self.contentcontainer = hg.DIV(
            *content, _class="bx--modal-content", tabindex="0"
        )
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
                self.contentcontainer,
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
            role="dialog",
            aria_modal="true",
            tabindex="-1",
            **attributes,
        )

    @classmethod
    def with_ajax_content(
        cls, heading, url, label="", size="md", submitlabel=None, id=None, **attributes
    ):
        """
        Same arguments as Modal() except ``url`` replaces ``content`` and ``submitlabel`` replaces ``buttons``

        url: string or htmlgenerator.Lazy
        submitlabel: string or an htmlgenerator element which will be displayed on the submit button.
                     A value of None means no submit button should be displayed.
        """
        buttons = (Button(_("Cancel"), buttontype="ghost", data_modal_close=True),)
        if submitlabel:
            buttons += (
                Button(
                    submitlabel,
                    type="submit",
                ),
            )

        modal = cls(
            heading,
            hg.CENTER(Loading(), style="opacity: 0.5; background-color: #EEE"),
            label="",
            buttons=buttons,
            size="md",
            id=None,
            **attributes,
        )
        if submitlabel:
            buttons[1].attributes["hx_post"] = url
            buttons[1].attributes["hx_target"] = f"#{modal.id} .bx--modal-content"

        modal.openerattributes["hx_get"] = url
        modal.openerattributes["hx_target"] = f"#{modal.id} .bx--modal-content"
        return modal
