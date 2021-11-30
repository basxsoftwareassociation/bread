import htmlgenerator as hg
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from ..button import Button

REQUIRED_LABEL = getattr(settings, "REQUIRED_LABEL", " *")


class Submit(hg.DIV):
    def __init__(self, label=None, **attributes):
        super().__init__(
            Button(label or _("Save"), type="submit"),
            _class="bx--form-item",
            **attributes
        )


class Label(hg.If):
    def __init__(self, label, _for=None, required=None, disabled=None, **kwargs):
        super().__init__(
            label,
            hg.LABEL(
                label,
                hg.If(required, REQUIRED_LABEL),
                _for=_for,
                _class=hg.BaseElement(
                    "bx--label",
                    hg.If(disabled, " bx--label--disabled"),
                ),
                **kwargs
            ),
        )


class HelpText(hg.If):
    def __init__(self, helptext, disabled=False):
        super().__init__(
            helptext,
            hg.DIV(
                helptext,
                _class=hg.BaseElement(
                    "bx--form__helper-text",
                    hg.If(disabled, " bx--form__helper-text--disabled"),
                ),
            ),
        )


class ErrorList(hg.If):
    def __init__(self, errors):
        super().__init__(
            errors,
            hg.DIV(
                hg.UL(hg.Iterator(errors or (), "error", hg.LI(hg.C("error")))),
                _class="bx--form-requirement",
            ),
        )
