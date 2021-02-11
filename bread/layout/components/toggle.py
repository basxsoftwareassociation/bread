import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from .helpers import REQUIRED_LABEL, ErrorList, HelperText, Label


class Toggle(hg.DIV):
    def __init__(
        self,
        fieldname,
        offlabel=_("On"),
        onlabel=_("Off"),
        widgetattributes={},
        **attributes,
    ):
        self.fieldname = fieldname
        attributes["_class"] = attributes.get("_class", "") + " bx--form-item"
        widgetattributes["_class"] = (
            widgetattributes.get("_class", "") + " bx--toggle-input"
        )
        widgetattributes["type"] = "checkbox"
        self.input = hg.INPUT(**widgetattributes)
        self.label = Label(
            hg.SPAN(
                hg.SPAN(offlabel, _class="bx--toggle__text--off", aria_hidden="true"),
                hg.SPAN(onlabel, _class="bx--toggle__text--on", aria_hidden="true"),
                _class="bx--toggle__switch",
            ),
            _class="bx--toggle-input__label",
        )
        super().__init__(self.input, self.label, **attributes)

    def render(self, context):
        if hasattr(self, "boundfield"):
            if self.boundfield is not None:
                if self.boundfield.field.disabled:
                    self.label.attributes["_class"] += " bx--label--disabled"
                    self.input.attributes["disabled"] = True
                self.label.attributes["_for"] = self.boundfield.id_for_label
                self.label.insert(0, self.boundfield.label)
                if self.boundfield.field.required:
                    self.label.append(REQUIRED_LABEL)
                if self.boundfield.help_text:
                    self.append(HelperText(self.boundfield.help_text))
                if self.boundfield.errors:
                    self.append(ErrorList(self.boundfield.errors))
        return super().render(context)


"""
<div class="bx--form-item">
  <input class="bx--toggle-input" id="toggle0" type="checkbox">
  <label class="bx--toggle-input__label" for="toggle0" aria-label="example toggle with state indicator text">
    <span class="bx--toggle__switch">
      <span class="bx--toggle__text--off" aria-hidden="true">Off</span>
      <span class="bx--toggle__text--on" aria-hidden="true">On</span>
    </span>
  </label>
</div>

<div class="bx--form-item">
  <input class="bx--toggle-input" id="toggle1" type="checkbox">
  <label class="bx--toggle-input__label" for="toggle1">
    Toggle with visible label
    <span class="bx--toggle__switch">
      <span class="bx--toggle__text--off" aria-hidden="true">Off</span>
      <span class="bx--toggle__text--on" aria-hidden="true">On</span>
    </span>
  </label>
</div>

<div class="bx--form-item">
  <input class="bx--toggle-input" id="toggle3" type="checkbox" disabled>
  <label class="bx--toggle-input__label" for="toggle3"
    aria-label="example disabled toggle with state indicator text">
    <span class="bx--toggle__switch">
      <span class="bx--toggle__text--off" aria-hidden="true">Off</span>
      <span class="bx--toggle__text--on" aria-hidden="true">On</span>
    </span>
  </label>
</div>

<div class="bx--form-item">
  <input class="bx--toggle-input" id="toggle4" type="checkbox" disabled>
  <label class="bx--toggle-input__label" for="toggle4">
    Toggle with visible label
    <span class="bx--toggle__switch">
      <span class="bx--toggle__text--off" aria-hidden="true">Off</span>
      <span class="bx--toggle__text--on" aria-hidden="true">On</span>
    </span>
  </label>
</div>
"""
