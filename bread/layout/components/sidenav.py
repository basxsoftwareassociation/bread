import htmlgenerator as hg

from bread.menu import Group, Menu

from .icon import Icon


def isactive(itemaccessor):
    return hg.F(lambda c, e: c[itemaccessor].active(c["request"]))


class SideNav(hg.ASIDE):
    def __init__(self, menu: Menu, **kwargs):
        kwargs["_class"] = hg.BaseElement(
            kwargs.get("_class", ""),
            " bx--side-nav bx--side-nav--rail",
            hg.If(
                hg.C(
                    "request.user.preferences.user_interface__navigation_menu_extended"
                ),
                " bx--side-nav--expanded",
            ),
        )
        kwargs["data_side_nav"] = True
        super().__init__(
            hg.NAV(
                hg.UL(
                    hg.Iterator(
                        sorted(menu._registry.values()),
                        "menugroup",
                        hg.LI(
                            hg.If(
                                hg.F(lambda c, e: isinstance(c["menugroup"], Group)),
                                hg.BaseElement(
                                    hg.BUTTON(
                                        hg.DIV(
                                            Icon(hg.C("menugroup.icon"), size=16),
                                            _class="bx--side-nav__icon",
                                        ),
                                        hg.SPAN(
                                            hg.C("menugroup.label"),
                                            _class="bx--side-nav__submenu-title",
                                        ),
                                        hg.DIV(
                                            Icon("chevron-down", size=16),
                                            _class="bx--side-nav__icon bx--side-nav__submenu-chevron",
                                        ),
                                        _class="bx--side-nav__submenu",
                                        type="button",
                                        aria_haspopup="true",
                                        aria_expanded=isactive("menugroup"),
                                    ),
                                    hg.UL(
                                        hg.Iterator(
                                            hg.C("menugroup.items"),
                                            "menuitem",
                                            hg.LI(
                                                hg.A(
                                                    hg.SPAN(
                                                        hg.C("menuitem.link.label"),
                                                        _class="bx--side-nav__link-text",
                                                    ),
                                                    _class=hg.BaseElement(
                                                        "bx--side-nav__link",
                                                        hg.If(
                                                            isactive("menuitem"),
                                                            " bx--side-nav__link--current",
                                                        ),
                                                    ),
                                                    href=hg.C("menuitem.link.url"),
                                                ),
                                                _class=hg.BaseElement(
                                                    "bx--side-nav__menu-item",
                                                    hg.If(
                                                        isactive("menuitem"),
                                                        " bx--side-nav__menu-item--current",
                                                    ),
                                                ),
                                                role="none",
                                            ),
                                        ),
                                        _class="bx--side-nav__menu",
                                    ),
                                ),
                                hg.A(
                                    hg.DIV(
                                        Icon(hg.C("menugroup.link.icon"), size=16),
                                        _class="bx--side-nav__icon",
                                    ),
                                    hg.SPAN(
                                        hg.C("menugroup.link.label"),
                                        _class="bx--side-nav__link-text",
                                    ),
                                    _class=hg.BaseElement(
                                        "bx--side-nav__link",
                                        hg.If(
                                            isactive("menugroup"),
                                            " bx--side-nav__link--current",
                                        ),
                                    ),
                                    href=hg.C("menugroup.link.url"),
                                ),
                            ),
                            _class=hg.BaseElement(
                                "bx--side-nav__item",
                                hg.If(
                                    isactive("menugroup"), " bx--side-nav__item--active"
                                ),
                            ),
                        ),
                    ),
                    _class="bx--side-nav__items",
                ),
                _class="bx--side-nav__navigation",
                role="navigation",
            ),
            **kwargs
        )


"""
<aside class="bx--side-nav bx--side-nav--rail{% if request.user.preferences.user_interface__navigation_menu_extended %} bx--side-nav--expanded{% endif %}" data-side-nav>
    <nav class="bx--side-nav__navigation" role="navigation" aria-label="Side navigation">
        <ul class="bx--side-nav__items">
            {% for menugroup, icon, group_active, items in menu %}

            <li class="bx--side-nav__item{% if group_active %} bx--side-nav__item--active{% else %}{% endif %}">
                {% if items|length == 1 %}
                    <a class="bx--side-nav__link{% if items.0.1 %} bx--side-nav__link--current{% endif %}" href="{{ items.0.2 }}">
                        {% if icon %}<div class="bx--side-nav__icon">{% carbon_icon icon 32 %}</div>{% endif %}
                        <span class="bx--side-nav__link-text">{{ items.0.0.link.label }}</span>
                    </a>
                {% else %}
                    <button class="bx--side-nav__submenu" type="button" aria-haspopup="true" aria-expanded="{{ group_active|yesno:"true,false" }}">
                        {% if icon %}<div class="bx--side-nav__icon">{% carbon_icon icon 32 %}</div>{% endif %}
                            <span class="bx--side-nav__submenu-title">{{ menugroup }}</span>
                            <div class="bx--side-nav__icon bx--side-nav__submenu-chevron">
                                {% carbon_icon "chevron--down" 32 %}
                            </div>
                        </button>
                        <ul class="bx--side-nav__menu">
                            {% for item, active, itemurl in items %}
                                <li class="bx--side-nav__menu-item{% if active %} bx--side-nav__menu-item--current{% endif %}" role="none">
                                    <a class="bx--side-nav__link{% if active %} bx--side-nav__link--current{% endif %}" href="{{ itemurl }}">
                                        <span class="bx--side-nav__link-text">{{ item.link.label }}</span>
                                    </a>
                                </li>
                            {% endfor %}
                        </ul>
                    {% endif %}
                </li>
            {% endfor %}
        </ul>

        <footer class="bx--side-nav__footer">
                <button
                    class="bx--side-nav__toggle"
                    role="button"
                    title="Close the side navigation menu"
                    hx-post="{% url "preferences:user" %}"

                    hx-include="#navigation-settings-form input"
                    hx-select="body body" {# do not select anything #}
                    hx-swap="afterbegin"
                >
                    <div class="bx--side-nav__icon">
                      {% carbon_icon "close" 20 class="bx--side-nav__icon--collapse bx--side-nav-collapse-icon" aria_hidden="true" %}
                      {% carbon_icon "chevron--right" 20 class="bx--side-nav__icon--expand bx--side-nav-expand-icon" aria_hidden="true" %}
                    </div>
                    <span class="bx--assistive-text">
                      Toggle the expansion state of the navigation
                    </span>
                </button>
                <div id="navigation-settings-form" style="display: none">
                    {% csrf_token %}
                    <input
                        type="checkbox"
                        name="user_interface__navigation_menu_extended"
                        id="id_user_interface__navigation_menu_extended"
                        {% if not request.user.preferences.user_interface__navigation_menu_extended %}checked{% endif %}
                    >
                </div>
        </footer>
    </nav>
</aside>
"""
