import htmlgenerator as hg

from .helpers import ErrorListElement, HelpTextElement, LabelElement
from .icon import Icon


class Select(hg.DIV):
    def __init__(
        self,
        optgroups,
        light=False,
        inline=False,
        widgetattributes=None,
        label=None,
        help_text=None,
        errors=None,
        disabled=None,
        required=None,
        **attributes,
    ):
        """
        optgroups: list of 2-tuples: (group_name, group_items)
                   group_items: list of objects with attributes ['label', 'value', 'attrs'], attrs is a dict with html attributes

        """

        _class = attributes.pop("_class", "")
        widgetattributes = widgetattributes or {}
        widgetattributes["_class"] = (
            widgetattributes.get("_class", "") + " bx--select-input"
        )
        widgetattributes.setdefault("id", hg.html_id(self))

        select_wrapper = hg.DIV(
            hg.SELECT(
                hg.Iterator(
                    optgroups,
                    "optgroup",
                    hg.If(
                        hg.C("optgroup.0"),
                        hg.OPTGROUP(
                            hg.Iterator(
                                hg.C("optgroup.1"),
                                "option",
                                hg.OPTION(
                                    hg.C("option.label"),
                                    _class="bx--select-option",
                                    value=hg.C("option.value"),
                                    lazy_attributes=hg.C("option.attrs"),
                                ),
                            ),
                            _class="bx--select-optgroup",
                            label=hg.C("optgroup.0"),
                        ),
                        hg.Iterator(
                            hg.C("optgroup.1"),
                            "option",
                            hg.OPTION(
                                hg.C("option.label"),
                                _class="bx--select-option",
                                value=hg.C("option.value"),
                                lazy_attributes=hg.C("option.attrs"),
                            ),
                        ),
                    ),
                ),
                **widgetattributes,
            ),
            Icon(
                "chevron--down", size=16, _class="bx--select__arrow", aria_hidden="true"
            ),
            hg.If(
                errors,
                Icon(
                    "warning--filled",
                    size=16,
                    _class="bx--select__invalid-icon",
                ),
            ),
            _class="bx--select-input__wrapper",
            data_invalid=hg.If(errors, True),
        )

        super().__init__(
            LabelElement(
                label,
                _for=widgetattributes["id"],
                required=required,
                disabled=disabled,
            ),
            hg.If(
                inline,
                hg.DIV(
                    select_wrapper,
                    ErrorListElement(errors),
                    _class="bx--select-input--inline__wrapper",
                ),
                select_wrapper,
            ),
            HelpTextElement(help_text),
            hg.If(
                inline, None, ErrorListElement(errors)
            ),  # not displayed if this is inline
            _class=hg.BaseElement(
                _class,
                " bx--select",
                hg.If(inline, " bx--select--inline"),
                hg.If(light, " bx--select--light"),
                hg.If(errors, " bx--select--invalid"),
                hg.If(disabled, " bx--select--disabled"),
            ),
            **attributes,
        )
