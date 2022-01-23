import json

import htmlgenerator as hg
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from djangoql.schema import DjangoQLSchema
from djangoql.serializers import DjangoQLSchemaSerializer

from bread.layout.components.icon import Icon
from bread.layout.components.search import _search_icon


class BrowseViewSearch(hg.DIV):
    def __init__(
        self,
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
            # "id": "search__" + hg.html_id(self),
            "name": "q",
            "onfocus": "this.setSelectionRange(this.value.length, this.value.length);",
            # "type": "text",
            # "value": hg.F(
            #     lambda c: html.escape(c["request"].GET.get(search_urlparameter, ""))
            # ),
            **(widgetattributes or {}),
        }

        # if backend:
        #     if resultcontainerid is None:
        #         resultcontainerid = f"search-result-{hg.html_id((self, backend.url))}"
        #     widgetattributes["hx_get"] = backend.url
        #     widgetattributes["hx_trigger"] = "changed, click, keyup changed delay:500ms"
        #     widgetattributes["hx_target"] = hg.format("#{}", resultcontainerid)
        #     widgetattributes["hx_indicator"] = hg.format(
        #         "#{}-indicator", resultcontainerid
        #     )
        #     widgetattributes["name"] = backend.query_parameter

        # self.close_button = _close_button(resultcontainerid, widgetattributes)
        # self.close_button.attributes[
        #     "onclick"
        # ] = "this.closest('form').querySelector('input').value = ''; this.closest('form').submit()"

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
        advanced_input = hg.TEXTAREA(
            defaultvalue,
            rows=1,
            id=advanced_inputid,
            style="padding-top: 1rem;",
            placeholder=_("Advanced Search (Press Backspace again to exit)"),
            **widgetattributes,
        )
        advanced_icon = Icon(
            "script",
            size=16,
            _class="bx--search-magnifier",
            id="searchinputicon_advanced",
            aria_hidden="true",
        )

        super().__init__(
            hg.DIV(
                hg.LABEL(_("Search"), _class="bx--label", _for=normal_inputid),
                # hg.INPUT(**widgetattributes),
                hg.DIV(
                    normal_input,
                    advanced_input,
                    id="searchinputcontainer",
                    style="width: 100%;",
                ),
                hg.DIV(
                    normal_icon,
                    advanced_icon,
                    id="searchinputicon",
                ),
                # self.close_button,
                # hg.If(backend is not None, _loading_indicator(resultcontainerid)),
                **kwargs,
            ),
            # hg.If(
            #     backend is not None and show_result_container,
            #     _result_container(resultcontainerid, resultcontainer_onload_js, width),
            # ),
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
                    let djangoqlCompletion = document.querySelector('.djangoql-completion');
                    if (normalInput.value.length > 0) {{
                        if (normalInput.value[0] === '=') {{
                            inputContainer.removeChild(normalInput);
                            iconContainer.removeChild(normalIcon);
                            advancedInput.value = advancedInput.value.slice(1);
                        }} else {{
                            inputContainer.removeChild(advancedInput);
                            iconContainer.removeChild(advancedIcon);
                        }}
                    }}
                    normalInput.addEventListener('input', e => {{
                        if (e.target.value.length > 0) {{
                            if (e.target.value[0] === '=') {{
                                inputContainer.removeChild(normalInput);
                                inputContainer.appendChild(advancedInput);
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
                                }});
                                document.querySelector('.djangoql-completion').style.marginLeft = '3rem';
                            }}
                        }}
                    }});
                    advancedInput.addEventListener('keydown', e => {{
                        if (e.target.value.length === 0 && e.key === 'Backspace') {{
                            inputContainer.appendChild(normalInput);
                            inputContainer.removeChild(advancedInput);
                            iconContainer.appendChild(normalIcon);
                            iconContainer.removeChild(advancedIcon);
                            document.body.removeChild(document.querySelector('.djangoql-completion'));
                            normalInput.value = e.target.value;
                            normalInput.focus();
                        }}
                    }});
                    advancedInput.closest('form').addEventListener('submit', e => {{
                        if (inputContainer.contains(advancedInput))
                            advancedInput.value = '=' + advancedInput.value;
                        this.closest('form').submit();
                    }});
                }});
                """,
                    normal_inputid,
                    advanced_inputid,
                    hg.F(
                        lambda context: json.dumps(
                            DjangoQLSchemaSerializer().serialize(
                                DjangoQLSchema(context["object_list"][0]._meta.model)
                            )
                        )
                    ),
                    "q",
                    reverse("reporthelp"),
                    autoescape=False,
                )
            ),
            style=hg.If(disabled, hg.BaseElement("display: none")),
        )
