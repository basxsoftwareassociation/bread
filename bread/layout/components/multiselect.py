import htmlgenerator as hg

from .helpers import ErrorListElement, HelpTextElement, LabelElement
from .icon import Icon


class MultiSelect(hg.DIV):
    def __init__(
        self,
        optgroups,
        widgetattributes=None,
        label=None,
        help_text=None,
        errors=None,
        disabled=None,
        required=None,
        **kwargs
    ):
        widgetattributes = widgetattributes or {}
        widgetattributes["_class"] = (
            widgetattributes.get("_class", "") + " bx--text-input"
        )
        widgetattributes.setdefault("id", hg.html_id(self))
        widgetattributes.setdefault("id", hg.html_id(self))
        super().__init__(
            LabelElement(
                label,
                _for=widgetattributes["id"],
                required=required,
                disabled=disabled,
            ),
            hg.DIV(
                hg.DIV(
                    hg.DIV(
                        "1",
                        Icon("close", size=16),
                        role="button",
                        _class="bx--list-box__selection bx--list-box__selection--multi bx--tag--filter",
                        tabindex="0",
                    ),
                    hg.INPUT(**widgetattributes),
                    hg.DIV(
                        Icon("chevron--down", size=16), _class="bx--list-box__menu-icon"
                    ),
                    role="button",
                    _class="bx--list-box__field",
                    tabindex="0",
                ),
                hg.FIELDSET(
                    hg.LEGEND(
                        "Description of form elements within the fieldset",
                        _class="bx--assistive-text",
                    ),
                    hg.DIV(
                        hg.DIV(
                            hg.DIV(
                                hg.LABEL(
                                    hg.INPUT(
                                        type="checkbox",
                                        name="Option 1",
                                        readonly=True,
                                        _class="bx--checkbox",
                                        id="downshift-1-item-0",
                                        value="on",
                                        checked=True,
                                    ),
                                    hg.SPAN(_class="bx--checkbox-appearance"),
                                    hg.SPAN(
                                        "Option 1",
                                        _class="bx--checkbox-label-text",
                                    ),
                                    title="Option 1",
                                    _class="bx--checkbox-label",
                                ),
                                _class="bx--form-item" + " " + "bx--checkbox-wrapper",
                            ),
                            _class="bx--list-box__menu-item__option",
                        ),
                        _class="bx--list-box__menu-item",
                    ),
                    _class="bx--list-box__menu",
                    role="listbox",
                ),
                _class="bx--multi-select bx--list-box bx--combo-box bx--multi-select--filterable",
            ),
            HelpTextElement(help_text),
            ErrorListElement(errors),
            _class="bx--list-box__wrapper",
        )
