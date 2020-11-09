from django.utils.translation import gettext as _

import plisplate

from .icon import Icon

FORM_NAME_SCOPED = "__plispate_form__"


class Select(plisplate.DIV):
    LABEL = 0
    SELECT = 1

    def __init__(
        self, fieldname, light=False, inline=False, **attributes,
    ):
        self.fieldname = fieldname
        attributes["_class"] = attributes.get("_class", "") + " bx--form-item"

        select_wrapper = plisplate.DIV(
            plisplate.SELECT(_class="bx--select-input"),
            Icon(
                "chevron--down", size=16, _class="bx--select__arrow", aria_hidden="true"
            ),
            _class="bx--select-input__wrapper",
        )
        if inline:
            select_wrapper = plisplate.DIV(
                select_wrapper, _class="bx--select-input--inline__wrapper"
            )
        super().__init__(
            plisplate.DIV(
                plisplate.LABEL(_class="bx--label"),
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
        boundfield = context[FORM_NAME_SCOPED][self.fieldname]

        if boundfield.field.disabled:
            self.label.attributes["_class"] += " bx--label--disabled"
            self.select.attributes["disabled"] = True
        if boundfield is not None:
            self.label.attributes["_for"] = boundfield.id_for_label
            self.label.append(boundfield.label)
            if not boundfield.field.required:
                self.label.append(_(" (optional)"))
            else:
                self.select.attributes["required"] = True
            if boundfield.auto_id:
                self.select.attributes["id"] = boundfield.auto_id
            self.select.attributes["name"] = boundfield.html_name

            for group_name, subgroup, index in boundfield.field.widget.optgroups(
                boundfield.name,
                boundfield.field.widget.get_context(
                    boundfield.name, boundfield.value(), {}
                )["widget"]["value"],
            ):
                group = self.select
                if group_name:
                    group = plisplate.OPTGROUP(
                        _class="bx--select-optgroup", label=group_name
                    )
                for option in subgroup:
                    group.append(
                        plisplate.OPTION(
                            option["label"],
                            _class="bx--select-option",
                            value=option["value"],
                            **option["attrs"],
                        )
                    )

                if group_name:
                    self.select.append(group)

            if boundfield.help_text:
                self[0].append(
                    plisplate.DIV(boundfield.help_text, _class="bx--form__helper-text")
                )
            if boundfield.errors:
                self[0].attributes["_class"] += " bx--select--invalid"
                self[0][1].attributes["data-invalid"] = True
                self[0][1].append(
                    Icon("warning--filled", size=16, _class="bx--select__invalid-icon",)
                )
                errormsg = plisplate.DIV(
                    plisplate.UL(*[plisplate.LI(e) for e in boundfield.errors]),
                    _class="bx--form-requirement",
                )
                if self.inline:
                    self[0][1][0].append(errormsg)
                else:
                    self[0][1].append(errormsg)
        return super().render(context)
