import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from .button import Button
from .icon import Icon
from .loading import Loading


class Modal(hg.DIV):
    SIZES = ["xs", "sm", "md", "lg"]

    def __init__(
        self,
        heading,
        *content,
        label="",
        size="sm",
        buttons=(),
        id=None,
        with_form=False,
        **attributes,
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
        self.id = hg.html_id(self, prefix="modal-") if id is None else id
        self.openerattributes = {"data_modal_target": hg.format("#{}", self.id)}
        self.contentcontainer = hg.DIV(
            *content,
            _class="bx--modal-content"
            + (" bx--modal-content--with-form" if with_form else ""),
            tabindex=0,
        )
        super().__init__(
            hg.DIV(
                hg.DIV(
                    hg.P(
                        label,
                        _class="bx--modal-header__label",
                    ),
                    hg.P(
                        heading,
                        _class="bx--modal-header__heading",
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
                hg.DIV(_class="bx--modal-content--overflow-indicator"),
                hg.DIV(
                    *buttons,
                    _class="bx--modal-footer",
                )
                if buttons
                else "",
                _class=f"bx--modal-container  bx--modal-container--{size}",
            ),
            data_modal=True,
            id=self.id,
            role="dialog",
            aria_modal="true",
            tabindex="-1",
            **attributes,
        )

    @classmethod
    def with_ajax_content(
        cls, heading, url, label="", size="xs", submitlabel=None, id=None, **attributes
    ):
        """
        Same arguments as Modal() except ``url`` replaces ``content`` and ``submitlabel`` replaces ``buttons``

        url: string or htmlgenerator.Lazy
        submitlabel: string or an htmlgenerator element which will be displayed on the submit button.
                     A value of None means no submit button should be displayed.
        """
        buttons = (Button(_("Cancel"), buttontype="ghost", data_modal_close=True),)
        if submitlabel:
            buttons += (Button(submitlabel, type="submit"),)

        modal = cls(
            heading,
            hg.DIV(
                Loading(),
                style="opacity: 0.5; background-color: #EEE; text-align: center;",
            ),
            label="",
            buttons=buttons,
            size=size,
            id=id,
            with_form=bool(submitlabel),
            **attributes,
        )
        if submitlabel:
            buttons[1].attributes["hx_post"] = url
            # note: we always use multipart forms, avoids some issues
            # see ./forms/__init__.py:Form.__init__
            buttons[1].attributes["hx_encoding"] = "multipart/form-data"
            buttons[1].attributes["hx_target"] = hg.format(
                "#{} .bx--modal-content", modal.id
            )
            buttons[1].attributes["hx_include"] = hg.format(
                "#{} .bx--modal-content", modal.id
            )

        modal.openerattributes["hx_get"] = url
        modal.openerattributes["hx_target"] = hg.format(
            "#{} .bx--modal-content", modal.id
        )
        return modal


def modal_with_trigger(modal: Modal, triggerclass: type, *args, **kwargs):
    return hg.BaseElement(
        triggerclass(*args, **{**kwargs, **modal.openerattributes}), modal
    )
