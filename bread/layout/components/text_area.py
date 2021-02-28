import htmlgenerator as hg

from .helpers import REQUIRED_LABEL, ErrorList, HelperText, Label
from .icon import Icon


class TextArea(hg.DIV):
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
            + f" bx--text-area bx--text-area--v2 {'bx--text-area--light' if light else ''}"
        )
        if rows:
            widgetattributes["rows"] = rows
        if cols:
            widgetattributes["cols"] = cols

        super().__init__(
            Label(),
            hg.DIV(
                hg.TEXTAREA(placeholder=placeholder, **widgetattributes),
                _class="bx--text-area__wrapper",
            ),
            **attributes,
        )
        # for easier reference in the render method:
        self.label = self[0]
        self.input = self[1][0]

    def render(self, context):
        if self.boundfield.field.disabled:
            self.label.attributes["_class"] += " bx--label--disabled"
            self.input.attributes["disabled"] = True
        if self.boundfield is not None:
            self.label.attributes["_for"] = self.boundfield.id_for_label
            self.label.append(self.boundfield.label)
            if self.boundfield.field.required:
                self.label.append(REQUIRED_LABEL)

            self.input.append(self.input.attributes.pop("value", ""))

            if self.boundfield.help_text:
                self.append(HelperText(self.boundfield.help_text))
            if self.boundfield.errors:
                self[1].attributes["data-invalid"] = True
                self.input.attributes["_class"] += " bx--text-area--invalid"
                self[1].append(
                    Icon(
                        "warning--filled",
                        size=16,
                        _class="bx--text-area__invalid-icon",
                    )
                )
                self.append(ErrorList(self.boundfield.errors))
        return super().render(context)
