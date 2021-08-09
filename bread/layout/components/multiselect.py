import htmlgenerator as hg

from .helpers import ErrorListElement, HelpTextElement, LabelElement
from .icon import Icon
from .tag import Tag


class MultiSelect(hg.DIV):
    def __init__(
        self,
        optgroups,
        label=None,
        help_text=None,
        errors=None,
        disabled=None,
        required=None,
        # light=False, # TODO?
        # inline=False, # TODO?
        **attributes,
    ):
        """
        optgroups: list of 2-tuples: (group_name, group_items)
                   group_items: list of objects with attributes ['label', 'value', 'attrs'], attrs is a dict with html attributes

        """

        def countselected(context):
            options = [o for og in hg.resolve_lazy(optgroups, context) for o in og[1]]
            return len([o for o in options if o and o["selected"]])

        searchfieldid = hg.html_id(self)
        super().__init__(
            LabelElement(
                label,
                _for=searchfieldid,
                required=required,
                disabled=disabled,
            ),
            hg.If(
                disabled,
                hg.DIV(
                    hg.Iterator(
                        optgroups,
                        "optiongroup",
                        hg.Iterator(
                            hg.C("optiongroup.1"),
                            "option",
                            hg.If(hg.C("option.selected"), Tag(hg.C("option.label"))),
                        ),
                    )
                ),
                hg.DIV(
                    hg.DIV(
                        hg.If(
                            errors,
                            Icon(
                                "warning--filled",
                                size=16,
                                _class="bx--list-box__invalid-icon",
                            ),
                        ),
                        hg.DIV(
                            hg.F(countselected),
                            Icon(
                                "close",
                                focusable="false",
                                size=15,
                                role="img",
                                onclick="clearMultiselect(this.parentElement.parentElement.parentElement)",
                            ),
                            role="button",
                            _class="bx--list-box__selection bx--list-box__selection--multi bx--tag--filter",
                            tabindex="0",
                            title="Clear all selected items",
                        ),
                        hg.INPUT(
                            id=searchfieldid,
                            _class="bx--text-input",
                            placeholder="Filter...",
                            onclick="this.parentElement.nextElementSibling.style.display = 'block'",
                            onkeyup="filterOptions(this.parentElement.parentElement)",
                        ),
                        hg.DIV(
                            Icon(
                                "chevron--down", size=16, role="img", focusable="false"
                            ),
                            _class="bx--list-box__menu-icon",
                            onclick="this.parentElement.nextElementSibling.style.display = this.parentElement.nextElementSibling.style.display == 'none' ? 'block' : 'none';",
                        ),
                        role="button",
                        _class="bx--list-box__field",
                        tabindex="0",
                        onload="window.addEventListener('click', (e) => {this.nextElementSibling.style.display = 'none'})",
                    ),
                    hg.FIELDSET(
                        hg.LEGEND(
                            "Description of form elements within the fieldset",
                            _class="bx--assistive-text",
                        ),
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
                                                    _class="bx--checkbox",
                                                    value=hg.C("option.value"),
                                                    lazy_attributes=hg.C(
                                                        "option.attrs"
                                                    ),
                                                    onchange="updateMultiselect(this.closest('.bx--multi-select'))",
                                                    checked=hg.C("option.selected"),
                                                    name=hg.C("option.name"),
                                                ),
                                                hg.SPAN(
                                                    _class="bx--checkbox-appearance"
                                                ),
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
                                    _class="bx--list-box__menu-item",
                                ),
                            ),
                        ),
                        _class="bx--list-box__menu",
                        role="listbox",
                        style="display: none",
                    ),
                    _class=hg.BaseElement(
                        "bx--multi-select bx--list-box bx--multi-select--selected bx--combo-box bx--multi-select--filterable",
                        hg.If(disabled, " bx--list-box--disabled"),
                    ),
                    data_invalid=hg.If(errors, True),
                ),
            ),
            HelpTextElement(help_text),
            ErrorListElement(errors),
            _class="bx--list-box__wrapper",
            onclick="event.stopPropagation()",
            **attributes,
        )
