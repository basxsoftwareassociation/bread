import htmlgenerator
from django.utils.translation import gettext as _

from .form import ErrorList, HelperText
from .icon import Icon


class Select(htmlgenerator.DIV):
    LABEL = 0
    SELECT = 1

    def __init__(
        self,
        fieldname,
        light=False,
        inline=False,
        widgetattributes={},
        **attributes,
    ):
        self.fieldname = fieldname
        attributes["_class"] = attributes.get("_class", "") + " bx--form-item"
        widgetattributes["_class"] = (
            widgetattributes.get("_class", "") + " bx--select-input"
        )

        select_wrapper = htmlgenerator.DIV(
            htmlgenerator.SELECT(**widgetattributes),
            Icon(
                "chevron--down", size=16, _class="bx--select__arrow", aria_hidden="true"
            ),
            _class="bx--select-input__wrapper",
        )
        if inline:
            select_wrapper = htmlgenerator.DIV(
                select_wrapper, _class="bx--select-input--inline__wrapper"
            )
        super().__init__(
            htmlgenerator.DIV(
                htmlgenerator.LABEL(_class="bx--label"),
                select_wrapper,
                _class="bx--select"
                + (" bx--select--inline" if inline else "")
                + (" bx--select--light" if light else ""),
            ),
            **attributes,
        )
        # for easier reference in the render method:
        self.label = self[0][0]
        self.select = self[0][1][0]
        self.inline = inline

    def render(self, context):
        if self.boundfield.field.disabled:
            self[0].attributes["_class"] += " bx--select--disabled"
            self.label.attributes["_class"] += " bx--label--disabled"
        if self.boundfield is not None:
            self.label.attributes["_for"] = self.boundfield.id_for_label
            self.label.append(self.boundfield.label)
            if not self.boundfield.field.required:
                self.label.append(_(" (optional)"))

            for group_name, subgroup, index in self.boundfield.field.widget.optgroups(
                self.boundfield.name,
                self.boundfield.field.widget.get_context(
                    self.boundfield.name, self.boundfield.value(), {}
                )["widget"]["value"],
            ):
                group = self.select
                if group_name:
                    group = htmlgenerator.OPTGROUP(
                        _class="bx--select-optgroup", label=group_name
                    )
                for option in subgroup:
                    group.append(
                        htmlgenerator.OPTION(
                            option["label"],
                            _class="bx--select-option",
                            value=option["value"],
                            **option["attrs"],
                        )
                    )

                if group_name:
                    self.select.append(group)

            if self.boundfield.help_text:
                self[0].append(HelperText(self.boundfield.help_text))
            if self.boundfield.errors:
                self[0].attributes["_class"] += " bx--select--invalid"
                self[0][1].attributes["data-invalid"] = True
                self[0][1].append(
                    Icon(
                        "warning--filled",
                        size=16,
                        _class="bx--select__invalid-icon",
                    )
                )
                if self.inline:
                    self[0][1][0].append(ErrorList(self.boundfield.errors))
                else:
                    self[0][1].append(ErrorList(self.boundfield.errors))
        return super().render(context)
