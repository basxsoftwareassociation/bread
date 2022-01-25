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

        normal_inputid = "normal_search__" + hg.html_id(self)
        normal_input = hg.INPUT(
            id=normal_inputid,
            type="text",
            value=defaultvalue,
            placeholder=placeholder or _("Search"),
            **widgetattributes,
        )
        normal_icon = Icon(
            "search",
            size=16,
            _class="bx--search-magnifier",
            id="searchinputicon_normal",
            aria_hidden="true",
        )
        advanced_inputid = "advanced_search__" + hg.html_id(self)
        advanced_input = hg.If(
            model,
            hg.TEXTAREA(
                defaultvalue,
                rows=1,
                id=advanced_inputid,
                style="padding-top: 1rem;",
                placeholder=_("Advanced Search (Press Backspace again to exit)"),
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
                    normal_input,
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
                    const inputContainer = document.getElementById('searchinputcontainer');
                    const normalInput = document.getElementById('{}');
                    const advancedInput = document.getElementById('{}');
                    const iconContainer = document.getElementById('searchinputicon');
                    const normalIcon = document.getElementById('searchinputicon_normal');
                    const advancedIcon = document.getElementById('searchinputicon_advanced');
                    const advancedMode = document.getElementById('searchinput_advancedmode');
                    const switchToNormal = () => {{
                        inputContainer.appendChild(normalInput);
                        inputContainer.removeChild(advancedInput);
                        advancedMode.value = 'off';
                        iconContainer.appendChild(normalIcon);
                        iconContainer.removeChild(advancedIcon);
                        const djangoqlCompletion = document.querySelector('.djangoql-completion');
                        if (djangoqlCompletion)
                            document.body.removeChild(djangoqlCompletion);
                        normalInput.value = advancedInput.value;
                        normalInput.focus();
                    }};
                    const switchToAdvanced = () => {{
                        inputContainer.removeChild(normalInput);
                        inputContainer.appendChild(advancedInput);
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
                            if (normalInput.value.length > 0) {{
                                if (normalInput.value[0] == '=')
                                    advancedInput.value = normalInput.value.slice(1);
                                else
                                    advancedInput.value = normalInput.value;
                            }}
                            advancedInput.focus();
                            advancedInput.click();
                            document.querySelector('.djangoql-completion').style.marginLeft = '3rem';
                        }});
                    }};
                    // actions here depend on whether the advancedmode is on.
                    {}
                    normalInput.addEventListener('input', e => {{
                        if (e.target.value.length > 0) {{
                            if (e.target.value[0] === '=') {{
                                switchToAdvanced();
                            }}
                        }}
                    }});
                    advancedInput.addEventListener('keydown', e => {{
                        if (e.target.value.length === 0 && e.key === 'Backspace') {{
                            switchToNormal();
                        }}
                    }});
                    document.querySelector('.bx--content .bx--search-close').addEventListener('click', () => {{
                        switchToNormal();
                        normalInput.value = '';
                    }});
                }});
                """,
                            normal_inputid,
                            advanced_inputid,
                            hg.F(
                                lambda context: json.dumps(
                                    DjangoQLSchemaSerializer().serialize(
                                        DjangoQLSchema(model)
                                    )
                                )
                            ),
                            "q",
                            reverse("reporthelp"),
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
