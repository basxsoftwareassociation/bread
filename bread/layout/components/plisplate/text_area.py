from django.utils.translation import gettext as _

import plisplate

from .form import FORM_NAME_SCOPED
from .icon import Icon


class TextArea(plisplate.DIV):
    def __init__(
        self,
        fieldname,
        placeholder="",
        rows=None,
        cols=None,
        light=False,
        widgetattributes={},
        **attributes,
    ):
        self.fieldname = fieldname
        attributes["_class"] = attributes.get("_class", "") + " bx--form-item"

        widgetattributes["_class"] = (
            widgetattributes.get("_class", "")
            + f" bx--text-area bx--text-area--v2 {'bx--text-area--light' if light else ''}",
        )
        if rows:
            widgetattributes["rows"] = rows
        if cols:
            widgetattributes["cols"] = cols

        super().__init__(
            plisplate.LABEL(_class="bx--label"),
            plisplate.DIV(
                plisplate.TEXTAREA(placeholder=placeholder, **widgetattributes),
                _class="bx--text-area__wrapper",
            ),
            **attributes,
        )
        # for easier reference in the render method:
        self.label = self[0]
        self.input = self[1][0]

    def render(self, context):
        boundfield = context[FORM_NAME_SCOPED][self.fieldname]

        if boundfield.field.disabled:
            self.label.attributes["_class"] += " bx--label--disabled"
            self.input.attributes["disabled"] = True
        if boundfield is not None:
            self.label.attributes["_for"] = boundfield.id_for_label
            self.label.append(boundfield.label)
            if not boundfield.field.required:
                self.label.append(_(" (optional)"))
            if boundfield.help_text:
                self.append(
                    plisplate.DIV(boundfield.help_text, _class="bx--form__helper-text")
                )
            if boundfield.errors:
                self[1].attributes["data-invalid"] = True
                self.input.attributes["_class"] += " bx--text-area--invalid"
                self[1].append(
                    Icon(
                        "warning--filled",
                        size=16,
                        _class="bx--text-area__invalid-icon",
                    )
                )
                self.append(
                    plisplate.DIV(
                        plisplate.UL(*[plisplate.LI(e) for e in boundfield.errors]),
                        _class="bx--form-requirement",
                    )
                )
        return super().render(context)
