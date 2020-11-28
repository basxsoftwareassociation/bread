import htmlgenerator
from django.utils.translation import gettext_lazy as _

from .form import ErrorList, HelperText


class Checkbox(htmlgenerator.DIV):
    def __init__(
        self,
        fieldname,
        widgetattributes={},
        **attributes,
    ):
        self.fieldname = fieldname
        attributes["_class"] = (
            attributes.get("_class", "") + " bx--form-item bx--checkbox-wrapper"
        )
        widgetattributes["_class"] = (
            widgetattributes.get("_class", "") + " bx--checkbox"
        )
        widgetattributes["type"] = "checkbox"
        self.input = htmlgenerator.INPUT(**widgetattributes)
        self.label = htmlgenerator.LABEL(self.input, _class="bx--checkbox-label")
        super().__init__(self.label, **attributes)

    def render(self, context):
        if self.boundfield.field.disabled:
            self.label.attributes["_class"] += " bx--label--disabled"
            self.input.attributes["disabled"] = True
        if self.boundfield is not None:
            self.label.attributes["_for"] = self.boundfield.id_for_label
            self.label.append(self.boundfield.label)
            if self.boundfield.field.required:
                self.label.append(_(" (required)"))
            if self.boundfield.help_text:
                self.append(HelperText(self.boundfield.help_text))
            if self.boundfield.errors:
                self.append(ErrorList(self.boundfield.errors))
        return super().render(context)
