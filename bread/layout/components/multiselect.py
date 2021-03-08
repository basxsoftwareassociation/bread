import htmlgenerator as hg

from .helpers import ErrorListElement, HelpTextElement, LabelElement
from .icon import Icon


class MultiSelect(hg.DIV):
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

        widgetattributes = widgetattributes or {}
        widgetattributes.setdefault("id", hg.html_id(self))

        select_wrapper = hg.SELECT(
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
                                value=hg.C("option.value"),
                                lazy_attributes=hg.C("option.attrs"),
                            ),
                        ),
                        label=hg.C("optgroup.0"),
                    ),
                    hg.Iterator(
                        hg.C("optgroup.1"),
                        "option",
                        hg.OPTION(
                            hg.C("option.label"),
                            value=hg.C("option.value"),
                            lazy_attributes=hg.C("option.attrs"),
                        ),
                    ),
                ),
            ),
            **widgetattributes,
        )

        super().__init__(
            LabelElement(
                label,
                _for=widgetattributes["id"],
                required=required,
                disabled=disabled,
            ),
            select_wrapper,
            HelpTextElement(help_text),
            ErrorListElement(errors),
            **attributes,
        )


class MultiSelect1(hg.DIV):
    def __init__(
        self,
        optgroups,
        widgetattributes=None,
        label=None,
        help_text=None,
        errors=None,
        disabled=None,
        required=None,
        **kwargs,
    ):
        widgetattributes = widgetattributes or {}
        widgetattributes["_class"] = (
            widgetattributes.get("_class", "") + " bx--checkbox"
        )
        searchfield_id = hg.html_id(self)
        label_id = searchfield_id + "-label"

        super().__init__(
            LabelElement(
                label,
                _for=searchfield_id,
                required=required,
                disabled=disabled,
                id=label_id,
            ),
            hg.DIV(
                hg.DIV(
                    hg.DIV(
                        hg.F(
                            lambda c, e: len(
                                [
                                    i
                                    for group in hg.resolve_lazy(optgroups, c, e)
                                    for i in group[1]
                                    if i.get("selected")
                                ]
                            )
                        ),
                        Icon("close", size=16),
                        role="button",
                        _class="bx--list-box__selection bx--list-box__selection--multi bx--tag--filter",
                        tabindex="0",
                    ),
                    hg.INPUT(
                        id=searchfield_id,
                        _class="bx--text-input bx--text-input--empty",
                        aria_autocomplete="list",
                        aria_labelledby=label_id,
                        autocomplete="off",
                        value="",
                    ),
                    hg.DIV(
                        Icon("chevron--down", size=16), _class="bx--list-box__menu-icon"
                    ),
                    role="button",
                    type="button",
                    data_toggle="true",
                    aria_haspopup="true",
                    aria_labelledby=label_id,
                    _class="bx--list-box__field",
                    tabindex="-1",
                ),
                hg.DIV(
                    hg.Iterator(
                        optgroups,
                        "optgroup",
                        hg.Iterator(
                            hg.C("optgroup.1"),
                            "option",
                            hg.DIV(
                                hg.DIV(
                                    hg.DIV(
                                        hg.LABEL(
                                            hg.INPUT(
                                                type="checkbox",
                                                readonly=True,
                                                lazy_attributes=hg.C("option.attrs"),
                                                **widgetattributes,
                                            ),
                                            hg.SPAN(_class="bx--checkbox-appearance"),
                                            hg.SPAN(
                                                hg.C("option.label"),
                                                _class="bx--checkbox-label-text",
                                            ),
                                            title=hg.C("option.label"),
                                            _class="bx--checkbox-label",
                                        ),
                                        _class="bx--form-item bx--checkbox-wrapper",
                                    ),
                                    _class="bx--list-box__menu-item__option",
                                ),
                                role="option",
                                aria_selected=hg.C("option.selected"),
                                _class="bx--list-box__menu-item",
                            ),
                        ),
                    ),
                    _class="bx--list-box__menu",
                    role="listbox",
                ),
                role="combobox",
                aria_expanded="false",
                aria_haspopup="listbox",
                aria_labelledby=label_id,
                _class="bx--multi-select bx--list-box bx--combo-box bx--multi-select--filterable",
            ),
            HelpTextElement(help_text),
            ErrorListElement(errors),
            _class="bx--list-box__wrapper",
        )
