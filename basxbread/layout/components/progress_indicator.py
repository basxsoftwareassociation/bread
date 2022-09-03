import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from .icon import Icon


class ProgressStep(hg.LI):
    STATUS = {
        "warning": "warning",
        "current": "circle--filled",
        "complete": "checkmark--outline",
        "incomplete": "radio-button",
    }

    def __init__(
        self, label, status, optional=False, tooltip=None, disabled=False, **kwargs
    ):
        if status not in ProgressStep.STATUS and not isinstance(status, hg.Lazy):
            raise ValueError(f"{status} must be one of {ProgressStep.STATUS}")
        kwargs["_class"] = hg.format(
            "{} bx--progress-step bx--progress-step--{} {}",
            kwargs.get("_class", ""),
            status,
            hg.If(disabled, "bx--progress-step--disabled"),
        )
        kwargs["aria_disabled"] = hg.If(disabled, "true")
        elements = [
            hg.F(
                lambda c: Icon(ProgressStep.STATUS[hg.resolve_lazy(status, c)], size=16)
            ),
            hg.P(label, tabindex=0, _class="bx--progress-label"),
            hg.SPAN(_class="bx--progress-line"),
        ]

        if optional:
            elements.insert(2, hg.P(_("Optional"), _class="bx--progress-optional"))

        if tooltip is not None:
            tooltipid = hg.html_id(tooltip, "tooltip-label")
            elements[1].attributes["aria-describedby"] = tooltipid
            elements.insert(
                2,
                hg.DIV(
                    hg.SPAN(_class="bx--tooltip__caret"),
                    hg.P(tooltip, _class="bx--tooltip__text"),
                    id=tooltipid,
                    role="tooltip",
                    data_floating_menu_direction="bottom",
                    _class="bx--tooltip",
                    data_avoid_focus_on_open=True,
                ),
            )

        super().__init__(*elements, **kwargs)


class ProgressIndicator(hg.UL):
    def __init__(self, steps, vertical=False, **kwargs):
        """steps: lazy object or iterator of tuples in the form (step_name, step_status)"""
        kwargs["data_progress"] = True
        kwargs["data_progress_current"] = True
        kwargs["_class"] = (
            kwargs.get("_class", "")
            + " bx--progress"
            + (" bx--progress--vertical" if vertical else "")
        )
        super().__init__(
            hg.Iterator(steps, "step", ProgressStep(hg.C("step")[0], hg.C("step")[1])),
            **kwargs,
        )
