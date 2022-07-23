import datetime

import htmlgenerator as hg
from django.utils.translation import gettext as _

from .button import Button
from .icon import Icon

KIND_ICON_MAPPING = {
    "error": "error--filled",
    "info": "information--filled",
    "info-square": "information--square--filled",
    "success": "checkmark--filled",
    "warning": "warning--filled",
    "warning-alt": "warning--alt--filled",
}


class InlineNotification(hg.DIV):
    def __init__(
        self,
        message,
        details,
        action=None,
        kind="info",
        lowcontrast=False,
        hideclosebutton=False,
        **attributes,
    ):
        """
        action: typle with (action_name, javascript_onclick), e.g. ("Open Google", "windows.location='https://google.com'")
        kind: can be one of "error" "info", "info-square", "success", "warning", "warning-alt"
        """
        if action is not None and (len(action) != 2):
            raise ValueError(
                "action must be a tuple with: (action_name, javascript_onclick)"
            )

        attributes["data-notification"] = True
        attributes["_class"] = hg.BaseElement(
            attributes.get("_class", ""),
            " bx--inline-notification bx--inline-notification--",
            kind,
            hg.If(lowcontrast, " bx--inline-notification--low-contrast"),
        )
        attributes["role"] = "alert"

        children = [
            hg.DIV(
                Icon(
                    hg.F(lambda c: KIND_ICON_MAPPING[hg.resolve_lazy(kind, c)]),
                    size=20,
                    _class="bx--inline-notification__icon",
                ),
                hg.DIV(
                    hg.P(message, _class="bx--inline-notification__title"),
                    hg.P(details, _class="bx--inline-notification__subtitle"),
                    _class="bx--inline-notification__text-wrapper",
                ),
                _class="bx--inline-notification__details",
            ),
        ]
        if action is not None:
            children.append(
                Button(
                    action[0],
                    onclick=action[1],
                    buttontype="ghost",
                    small=True,
                    _class="bx--inline-notification__action-button",
                )
            )
        children.append(
            hg.If(
                hideclosebutton,
                None,
                hg.BUTTON(
                    Icon(
                        "close", size=20, _class="bx--inline-notification__close-icon"
                    ),
                    data_notification_btn=True,
                    _class="bx--inline-notification__close-button",
                    aria_label="close",
                ),
            )
        )
        super().__init__(*children, **attributes)


class ToastNotification(hg.DIV):
    def __init__(
        self,
        message,
        details,
        kind="info",
        lowcontrast=False,
        hideclosebutton=False,
        hidetimestamp=False,
        autoremove=4.0,
        **attributes,
    ):
        """
        kind: can be one of "error" "info", "info-square", "success", "warning", "warning-alt"
        autoremove: remove notification after ``autoremove`` seconds
        """
        self.hidetimestamp = hidetimestamp

        attributes["data-notification"] = True
        attributes["_class"] = hg.BaseElement(
            attributes.get("_class", ""),
            " bx--toast-notification bx--toast-notification--",
            kind,
            hg.If(lowcontrast, " bx--toast-notification--low-contrast"),
        )
        attributes["role"] = "alert"

        attributes["style"] = hg.BaseElement(
            attributes.get("style", ""),
            ";opacity: 0; animation: ",
            hg.F(lambda c: autoremove * (c["message_index"] + 1)),
            "s ease-in-out notification",
        )
        attributes["onload"] = hg.BaseElement(
            attributes.get("onload", ""),
            ";setTimeout(() => this.style.display = 'None', ",
            hg.F(lambda c: (autoremove * 1000 * (c["message_index"] + 1))),
            ")",
        )

        timestampelem = (
            [hg.P(_("Time stamp"), " ", _class="bx--toast-notification__caption")]
            if not hidetimestamp
            else []
        )
        children = [
            Icon(
                hg.F(lambda c: KIND_ICON_MAPPING[hg.resolve_lazy(kind, c)]),
                size=20,
                _class="bx--toast-notification__icon",
            ),
            hg.DIV(
                hg.DIV(message, _class="bx--toast-notification__title"),
                hg.DIV(details, _class="bx--toast-notification__subtitle"),
                *timestampelem,
                _class="bx--toast-notification__details",
            ),
        ]
        children.append(
            hg.If(
                hideclosebutton,
                None,
                hg.BUTTON(
                    Icon("close", size=20, _class="bx--toast-notification__close-icon"),
                    data_notification_btn=True,
                    _class="bx--toast-notification__close-button",
                    aria_label="close",
                ),
            )
        )
        super().__init__(*children, **attributes)

    def render(self, context):
        if not self.hidetimestamp:
            self[1][2].append(
                "[" + datetime.datetime.now().time().isoformat()[:8] + "]"
            )
        return super().render(context)
