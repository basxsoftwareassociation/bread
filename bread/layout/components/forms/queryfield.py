import json

import htmlgenerator as hg
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
        # print("defaultvalue =", defaultvalue)
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
            # "id": "search__" + hg.html_id(self),
            "name": "q",
            "onfocus": "this.setSelectionRange(this.value.length, this.value.length);",
            # "type": "text",
            # "value": hg.F(
            #     lambda c: html.escape(c["request"].GET.get(search_urlparameter, ""))
            # ),
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
                **kwargs,
            ),
            hg.If(
                model,
                hg.SCRIPT(
                    hg.format(
                        """
                document.addEventListener("DOMContentLoaded", () => {{
                    let inputContainer = document.getElementById('searchinputcontainer');
                    let normalInput = document.getElementById('{}');
                    let advancedInput = document.getElementById('{}');
                    let iconContainer = document.getElementById('searchinputicon');
                    let normalIcon = document.getElementById('searchinputicon_normal');
                    let advancedIcon = document.getElementById('searchinputicon_advanced');
                    let advancedMode = document.getElementById('searchinput_advancedmode');
                    let djangoqlCompletion = document.querySelector('.djangoql-completion');
                    // actions here depend on whether the advancedmode is on.
                    {}
                    normalInput.addEventListener('input', e => {{
                        if (e.target.value.length > 0) {{
                            if (e.target.value[0] === '=') {{
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
                                    advancedInput.value = e.target.value.slice(1);
                                    advancedInput.focus();
                                    advancedInput.click();
                                    document.querySelector('.djangoql-completion').style.marginLeft = '3rem';
                                }});
                            }}
                        }}
                    }});
                    advancedInput.addEventListener('keydown', e => {{
                        if (e.target.value.length === 0 && e.key === 'Backspace') {{
                            inputContainer.appendChild(normalInput);
                            inputContainer.removeChild(advancedInput);
                            advancedMode.value = 'off';
                            iconContainer.appendChild(normalIcon);
                            iconContainer.removeChild(advancedIcon);
                            document.body.removeChild(document.querySelector('.djangoql-completion'));
                            normalInput.value = advancedInput.value;
                            normalInput.focus();
                        }}
                    }});
                }});
                """,
                        normal_inputid,
                        advanced_inputid,
                        hg.If(
                            advancedmode,
                            hg.format(
                                """
                            inputContainer.removeChild(normalInput);
                            iconContainer.removeChild(normalIcon);
                            advancedMode.value = 'on';
                            DjangoQL.DOMReady(() => {{
                                new DjangoQL({{
                                    introspections: {},
                                    selector: "textarea[name='{}']",
                                    syntaxHelp: '{}',
                                    autoResize: false
                                }});
                                document.querySelector('.djangoql-completion').style.marginLeft = '3rem';
                            }});
                            """,
                                hg.F(
                                    lambda context: json.dumps(
                                        DjangoQLSchemaSerializer().serialize(
                                            DjangoQLSchema(model)
                                        )
                                    )
                                ),
                                "q",
                                reverse("reporthelp"),
                                advanced_inputid,
                                autoescape=False,
                            ),
                            hg.mark_safe(
                                """
                            inputContainer.removeChild(advancedInput);
                            iconContainer.removeChild(advancedIcon);
                            advancedMode.value = 'off';
                            """
                            ),
                        ),
                        hg.F(
                            lambda context: json.dumps(
                                DjangoQLSchemaSerializer().serialize(
                                    DjangoQLSchema(model)
                                )
                            )
                        ),
                        "q",
                        reverse("reporthelp"),
                        advanced_inputid,
                        autoescape=False,
                    )
                ),
            ),
            style=hg.If(disabled, hg.BaseElement("display: none")),
        )
