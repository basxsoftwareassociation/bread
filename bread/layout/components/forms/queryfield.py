import json

import htmlgenerator as hg
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from djangoql.schema import DjangoQLSchema
from djangoql.serializers import DjangoQLSchemaSerializer

from bread.layout.components.icon import Icon


class BrowseViewSearch(hg.DIV):
    def __init__(
        self,
        model=None,
        advancedmode=False,
        size="xl",
        defaultvalue="",
        placeholder=None,
        widgetattributes=None,
        disabled=False,
        **kwargs,
    ):
        kwargs["_class"] = kwargs.get("_class", "") + f" bx--search bx--search--{size}"
        kwargs["data_search"] = True
        kwargs["role"] = "search"
        width = kwargs.get("width", None)
        if width:
            kwargs["style"] = kwargs.get("style", "") + f"width:{width};"

        widgetattributes = {
            "autocomplete": "off",
            "autofocus": True,
            "_class": "bx--search-input",
            "name": "q",
            "onfocus": "this.setSelectionRange(this.value.length, this.value.length);",
            **(widgetattributes or {}),
        }

        normal_placeholder = placeholder or _("Search")
        normal_icon = Icon(
            "search",
            size=16,
            _class="bx--search-magnifier",
            id="searchinputicon_normal",
            aria_hidden="true",
        )
        advanced_inputid = "advanced_search__" + hg.html_id(self)
        advanced_placeholder = _("Advanced Search (Press Backspace again to exit)")
        advanced_input = hg.If(
            model,
            hg.TEXTAREA(
                defaultvalue,
                rows=1,
                id=advanced_inputid,
                style="padding-top: 1rem;",
                placeholder=normal_placeholder,
                **widgetattributes,
            ),
        )
        advanced_icon = hg.If(
            model,
            Icon(
                "script",
                size=16,
                _class="bx--search-magnifier",
                id="searchinputicon_advanced",
                aria_hidden="true",
            ),
        )
        advanced_mode = hg.INPUT(
            type="hidden",
            id="searchinput_advancedmode",
            name="advancedmode",
            value="off",
        )

        super().__init__(
            hg.DIV(
                hg.DIV(
                    advanced_input,
                    advanced_mode,
                    id="searchinputcontainer",
                    style="width: 100%;",
                ),
                hg.DIV(
                    normal_icon,
                    advanced_icon,
                    id="searchinputicon",
                ),
                _close_button(None, {"value": defaultvalue}),
                **kwargs,
            ),
            hg.If(
                model,
                hg.BaseElement(
                    hg.SCRIPT(
                        hg.format(
                            """
                document.addEventListener("DOMContentLoaded", () => {{
                    window.advancedSearchEnabled = false;
                    const advancedInput = document.getElementById('{}');
                    const iconContainer = document.getElementById('searchinputicon');
                    const normalIcon = document.getElementById('searchinputicon_normal');
                    const advancedIcon = document.getElementById('searchinputicon_advanced');
                    const advancedMode = document.getElementById('searchinput_advancedmode');
                    const switchToNormal = () => {{
                        advancedSearchEnabled = false;
                        advancedMode.value = 'off';
                        iconContainer.appendChild(normalIcon);
                        iconContainer.removeChild(advancedIcon);
                        const djangoqlCompletion = document.querySelector('.djangoql-completion');
                        if (djangoqlCompletion)
                            document.body.removeChild(djangoqlCompletion);
                        advancedInput.placeholder = '{}';
                        advancedInput.focus();
                    }};
                    const switchToAdvanced = () => {{
                        window.advancedSearchEnabled = true;
                        advancedMode.value = 'on';
                        iconContainer.removeChild(normalIcon);
                        iconContainer.appendChild(advancedIcon);
                        DjangoQL.DOMReady(() => {{
                            new DjangoQL({{
                                introspections: {},
                                selector: "textarea[name='{}']",
                                syntaxHelp: '{}',
                                autoResize: false
                            }});
                            if (advancedInput.value.length > 0) {{
                                if (advancedInput.value[0] == '=')
                                    advancedInput.value = advancedInput.value.slice(1);
                            }}
                            advancedInput.placeholder = '{}';
                            advancedInput.focus();
                            advancedInput.click();
                            document.querySelector('.djangoql-completion').style.marginLeft = '3rem';
                        }});
                    }};
                    // actions here depend on whether the advancedmode is on.
                    {}
                    advancedInput.addEventListener('input', e => {{
                        if (!window.advancedSearchEnabled) {{
                            if (e.target.value.length > 0) {{
                                if (e.target.value[0] === '=') {{
                                    switchToAdvanced();
                                }}
                            }}
                        }}
                    }});
                    advancedInput.addEventListener('keydown', e => {{
                        if (window.advancedSearchEnabled) {{
                            if (e.target.selectionStart === 0 && e.target.selectionEnd === 0 && e.key === 'Backspace') {{
                                switchToNormal();
                            }}
                        }}
                    }});
                    document.querySelector('.bx--content .bx--search-close').addEventListener('click', () => {{
                        switchToNormal();
                        advancedInput.value = '';
                    }});
                }});
                """,
                            advanced_inputid,
                            normal_placeholder,
                            hg.F(
                                lambda context: json.dumps(
                                    DjangoQLSchemaSerializer().serialize(
                                        DjangoQLSchema(model)
                                    )
                                )
                            ),
                            "q",
                            reverse("reporthelp"),
                            advanced_placeholder,
                            hg.If(
                                advancedmode, "switchToAdvanced();", "switchToNormal();"
                            ),
                            autoescape=False,
                        )
                    ),
                    hg.LINK(
                        rel="stylesheet",
                        type="text/css",
                        href=staticfiles_storage.url("djangoql/css/completion.css"),
                    ),
                    hg.SCRIPT(src=staticfiles_storage.url("djangoql/js/completion.js")),
                ),
            ),
            style=hg.If(disabled, hg.BaseElement("display: none")),
        )


def _close_button(resultcontainerid, widgetattributes):
    kwargs = {
        "_class": hg.BaseElement(
            "bx--search-close",
            hg.If(widgetattributes.get("value"), None, " bx--search-close--hidden"),
        ),
        "title": _("Clear search input"),
        "aria_label": _("Clear search input"),
        "type": "button",
    }

    return hg.BUTTON(Icon("close", size=20, _class="bx--search-clear"), **kwargs)
