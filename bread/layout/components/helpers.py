import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from . import button


class SubmitButton(hg.DIV):
    def __init__(self, *args, **kwargs):
        kwargs["type"] = "submit"
        super().__init__(button.Button(*args, **kwargs), _class="bx--form-item")


# TODO: A more generic approach for the form elements needs to be done
# I think we should replace the ErrorList, HelperText, Label things with the "smarter"
# version LabelElement etc. and add shortcuts to generate them directly from a field
# in the context instead of setting all the values inside the render-methods of the
# widgets. Or something like that. The API for form fields/widgets is currently not
# very great. For a test-implementation see text_input.py


class ErrorList(hg.DIV):
    def __init__(self, errors):
        super().__init__(
            hg.UL(*[hg.LI(e) for e in errors]),
            _class="bx--form-requirement",
        )


class HelperText(hg.DIV):
    def __init__(self, helpertext):
        super().__init__(helpertext, _class="bx--form__helper-text")


class Label(hg.LABEL):
    def __init__(self, *args, **kwargs):
        kwargs["_class"] = kwargs.get("_class", "") + " bx--label"
        super().__init__(*args, **kwargs)


# --------- CURRENTLY NOT USED, KEEP FOR FUTURE EXPLORATION --------------
class LabelElement(hg.If):
    def __init__(self, label, _for, required, disabled=False):
        super().__init__(
            label,
            Label(
                label,
                hg.If(required, _(" (required)")),
                _for=_for,
                _class=hg.BaseElement(
                    "bx--label",
                    hg.If(disabled, " bx--label--disabled"),
                ),
            ),
        )


class HelpTextElement(hg.If):
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


class ErrorListElement(hg.If):
    def __init__(self, errors):
        super().__init__(
            errors,
            hg.DIV(
                hg.UL(hg.Iterator(errors or (), "error", hg.C("error"))),
                _class="bx--form-requirement",
            ),
        )
