from django.utils.translation import gettext as _

import plisplate

from .form import FORM_NAME_SCOPED, ErrorList, HelperText


class Checkbox(plisplate.DIV):
    def __init__(
        self, fieldname, widgetattributes={}, **attributes,
    ):
        self.fieldname = fieldname
        attributes["_class"] = (
            attributes.get("_class", "") + " bx--form-item bx--checkbox-wrapper"
        )
        widgetattributes["_class"] = (
            widgetattributes.get("_class", "") + " bx--checkbox"
        )
        widgetattributes["type"] = "checkbox"
        self.input = plisplate.INPUT(**widgetattributes)
        self.label = plisplate.LABEL(self.input, _class="bx--checkbox-label")
        super().__init__(self.label, **attributes)

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
                self.append(HelperText(boundfield.help_text))
            if boundfield.errors:
                self.append(ErrorList(boundfield.errors))
        return super().render(context)
