import htmlgenerator as hg

from ..icon import Icon
from .helpers import REQUIRED_LABEL, ErrorList, HelpText, Label


class TextArea(hg.DIV):
    def __init__(
        self,
        fieldname,
        placeholder="",
        rows=None,
        cols=None,
        widgetattributes={},
        boundfield=None,
        **attributes,
    ):
        self.fieldname = fieldname
        attributes["_class"] = attributes.get("_class", "") + " bx--form-item"

        widgetattributes["_class"] = (
            widgetattributes.get("_class", "") + " bx--text-area bx--text-area--v2"
        )
        if rows:
            widgetattributes["rows"] = rows
        if cols:
            widgetattributes["cols"] = cols

        super().__init__(
            Label(boundfield.field.label),
            hg.DIV(
                hg.TEXTAREA(placeholder=placeholder, **widgetattributes),
                _class="bx--text-area__wrapper",
            ),
            **attributes,
        )

        # for easier reference
        self.label = self[0]
        self.input = self[1][0]

        if boundfield.field.disabled:
            # self.label.attributes["_class"] += " bx--label--disabled"
            self.input.attributes["disabled"] = True
        if boundfield is not None:
            # self.label.attributes["_for"] = boundfield.id_for_label
            # self.label.append(boundfield.label)
            if boundfield.field.required:
                self.label.append(REQUIRED_LABEL)

            self.input.append(self.input.attributes.pop("value", ""))

            if boundfield.help_text:
                self.append(HelpText(boundfield.help_text))
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
                self.append(ErrorList(boundfield.errors))
