import htmlgenerator as hg

from .helpers import ErrorList, HelpText, Label


class FormField(hg.DIV):
    def __init__(
        self,
        label=None,
        help_text=None,
        error_list=None,
        inputelement_attrs=None,
        **attributes
    ):
        self.label = Label(
            label,
            required=inputelement_attrs.get("required"),
            disabled=inputelement_attrs.get("disabled"),
        )
        self.input = hg.INPUT(**(inputelement_attrs or {}))
        self.help_text = HelpText(
            help_text, disabled=inputelement_attrs.get("disabled")
        )
        self.error_list = ErrorList(error_list)
        super().__init__(
            self.label, self.input, self.help_text, self.error_list, **attributes
        )

    def with_fieldwrapper(self):
        return hg.DIV(self, _class="bx--form-item")

    @classmethod
    def from_formfield(
        cls, fieldname, form="form", inputelement_attrs=None, **attributes
    ):
        if isinstance(form, str):
            form = hg.C(form)
        return cls(
            label=form[fieldname].label,
            help_text=form.fields(fieldname),
            error_list=form[fieldname].errors,
            inputelement_attrs=inputelement_attrs,
            **attributes
        )
