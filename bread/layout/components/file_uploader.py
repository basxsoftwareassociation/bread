import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from .helpers import ErrorList

# TODO: not finished, does not really well integrate with django FileField in the current state


class FileUploader(hg.DIV):
    def __init__(
        self,
        fieldname,
        light=False,
        widgetattributes={},
        **attributes,
    ):
        self.fieldname = fieldname
        attributes["_class"] = attributes.get("_class", "") + " bx--form-item"
        widgetattributes["_class"] = (
            widgetattributes.get("_class", "") + " bx--file-input bx--visually-hidden"
        )
        widgetattributes["type"] = "file"

        self.label = hg.STRONG(_class="bx--file--label")
        self.help_text = hg.P(_class="bx--label-description")
        self.uploadbutton = hg.LABEL(
            hg.SPAN(_("Add files"), role="button"),
            tabindex=0,
            _class="bx--btn bx--btn--primary",
            data_file_drop_container=True,
        )
        self.input = hg.INPUT(
            **widgetattributes,
            # onload="document.addEventListener('change', () => new CarbonComponents.FileUploader(this.parentNode).setState('edit'))",
        )
        self.wrapper = hg.DIV(
            self.uploadbutton,
            self.input,
            hg.DIV(data_file_container=True, _class="bx--file-container"),
            _class="bx--file",
            data_file=True,
        )
        super().__init__(
            self.label,
            self.help_text,
            self.wrapper,
            **attributes,
        )
        """
        <strong class="bx--file--label">Upload</strong>
        <p class="bx--label-description">only .jpg files at 500mb or less</p>
        <label tabindex="0" aria-disabled="false" class="bx--btn bx--btn--primary" for="id24"><span role="button">Add files</span></label>
        <input class="bx--visually-hidden" id="id24" type="file" tabindex="-1" accept=".jpg,.png">
        <div class="bx--file-container"></div>
        """

    def render(self, context):
        if self.boundfield is not None:
            if self.boundfield.field.disabled:
                self.uploadbutton.attributes["disabled"] = True
                self.input.attributes["disabled"] = True
            self.uploadbutton.attributes["_for"] = self.boundfield.id_for_label
            self.label.append(self.boundfield.label)
            if self.boundfield.field.required:
                self.label.append(_(" (required)"))
            if self.boundfield.help_text:
                self.help_text.append(self.boundfield.help_text)
            if self.boundfield.errors:
                self.append(ErrorList(self.boundfield.errors))
        return super().render(context)
