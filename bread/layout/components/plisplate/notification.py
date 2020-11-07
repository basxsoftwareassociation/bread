import datetime

from django.utils.translation import gettext as _

import plisplate

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


class InlineNotification(plisplate.DIV):
    def __init__(
        self,
        title,
        subtitle,
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
        assert (
            kind in KIND_ICON_MAPPING
        ), f"kind '{kind}' does not exists, must be one of {KIND_ICON_MAPPING.keys()}"
        assert action is None or (
            len(action) == 2
        ), "action must be a tuple with: (action_name, javascript_onclick)"

        attributes["data-notification"] = True
        attributes["_class"] = (
            attributes.get("_class", "")
            + f" bx--inline-notification bx--inline-notification--{kind}"
        )
        if lowcontrast:
            attributes["_class"] += "  bx--inline-notification--low-contrast"
        attributes["role"] = "alert"

        children = [
            plisplate.DIV(
                Icon(
                    KIND_ICON_MAPPING[kind],
                    size=20,
                    _class="bx--inline-notification__icon",
                ),
                plisplate.DIV(
                    plisplate.P(title, _class="bx--inline-notification__title"),
                    plisplate.P(subtitle, _class="bx--inline-notification__subtitle"),
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
                    type="ghost",
                    small=True,
                    _class="bx--inline-notification__action-button",
                )
            )
        if not hideclosebutton:
            children.append(
                plisplate.BUTTON(
                    Icon(
                        "close", size=20, _class="bx--inline-notification__close-icon"
                    ),
                    data_notification_btn=True,
                    _class="bx--inline-notification__close-button",
                    aria_label="close",
                )
            )
        super().__init__(*children, **attributes)


class ToastNotification(plisplate.DIV):
    def __init__(
        self,
        title,
        subtitle,
        kind="info",
        lowcontrast=False,
        hideclosebutton=False,
        hidetimestamp=False,
        **attributes,
    ):
        """
        kind: can be one of "error" "info", "info-square", "success", "warning", "warning-alt"
        """
        assert (
            kind in KIND_ICON_MAPPING
        ), f"kind '{kind}' does not exists, must be one of {KIND_ICON_MAPPING.keys()}"
        self.hidetimestamp = hidetimestamp

        attributes["data-notification"] = True
        attributes["_class"] = (
            attributes.get("_class", "")
            + f" bx--toast-notification bx--toast-notification--{kind}"
        )
        if lowcontrast:
            attributes["_class"] += "  bx--toast-notification--low-contrast"
        attributes["role"] = "alert"

        timestampelem = (
            [plisplate.P(_("Time stamp "), _class="bx--toast-notification__caption")]
            if not hidetimestamp
            else []
        )
        children = [
            Icon(
                KIND_ICON_MAPPING[kind], size=20, _class="bx--toast-notification__icon",
            ),
            plisplate.DIV(
                plisplate.H3(title, _class="bx--toast-notification__title"),
                plisplate.P(subtitle, _class="bx--toast-notification__subtitle"),
                *timestampelem,
                _class="bx--toast-notification__details",
            ),
        ]
        if not hideclosebutton:
            children.append(
                plisplate.BUTTON(
                    Icon("close", size=20, _class="bx--toast-notification__close-icon"),
                    data_notification_btn=True,
                    _class="bx--toast-notification__close-button",
                    aria_label="close",
                )
            )
        super().__init__(*children, **attributes)

    def render(self, context):
        if not self.hidetimestamp:
            self[1][2].append(
                "[" + datetime.datetime.now().time().isoformat()[:8] + "]"
            )
        return super().render(context)
