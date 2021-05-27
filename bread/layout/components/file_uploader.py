import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from .helpers import REQUIRED_LABEL, ErrorList
from .icon import Icon

# TODO: make delete-field working correctly


class FileUploader(hg.DIV):
    def __init__(
        self,
        fieldname,
        light=False,
        widgetattributes={},
        boundfield=None,
        **attributes,
    ):
        self.fieldname = fieldname
        attributes["_class"] = attributes.get("_class", "") + " bx--form-item"
        widgetattributes["_class"] = (
            widgetattributes.get("_class", "") + " bx--file-input bx--visually-hidden"
        )
        widgetattributes["type"] = "file"
        self.boundfield = boundfield

        self.label = hg.STRONG(_class="bx--file--label")
        self.help_text = hg.P(_class="bx--label-description")
        self.uploadbutton = hg.LABEL(
            hg.SPAN(_("Select file"), role="button"),
            tabindex=0,
            _class="bx--btn bx--btn--primary",
            data_file_drop_container=True,
        )
        self.input = hg.INPUT(
            **widgetattributes,
            onload="""document.addEventListener('change', (e) => {
                this.parentElement.querySelector('[data-file-container]').innerHTML = ''; var widget = new CarbonComponents.FileUploader(this.parentElement); widget._displayFilenames(); widget.setState('edit');
            })""",
        )
        self.container = hg.DIV(data_file_container=True, _class="bx--file-container")
        self.wrapper = hg.DIV(
            self.uploadbutton,
            self.input,
            self.container,
            _class="bx--file",
            data_file=True,
        )
        super().__init__(
            self.label,
            self.help_text,
            self.wrapper,
            **attributes,
        )

    def render(self, context):
        if self.boundfield is not None:
            if self.boundfield.field.disabled:
                self.uploadbutton.attributes["disabled"] = True
                self.input.attributes["disabled"] = True
            self.uploadbutton.attributes["_for"] = self.boundfield.id_for_label
            self.label.append(self.boundfield.label)
            if self.boundfield.field.required:
                self.label.append(REQUIRED_LABEL)
            if self.boundfield.help_text:
                self.help_text.append(self.boundfield.help_text)
            if self.boundfield.errors:
                self.input.attributes["data_invalid"] = True
                self.wrapper.append(ErrorList(self.boundfield.errors))
            if self.boundfield.value():
                self.container.append(
                    hg.SPAN(
                        hg.P(self.boundfield.value(), _class="bx--file-filename"),
                        hg.SPAN(
                            hg.BUTTON(
                                Icon("close", size=16),
                                _class="bx--file-close",
                                type="button",
                                aria_label="close",
                            ),
                            data_for=self.boundfield.id_for_label,
                            _class="bx--file__state-container",
                        ),
                        _class="bx--file__selected-file",
                    )
                )
        return super().render(context)
