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
        assert (
            status in ProgressStep.STATUS
        ), f"{status} must be one of {ProgressStep.STATUS}"
        kwargs["class"] = (
            kwargs.get("class", "") + f" bx--progress-step bx--progress-step--{status}"
        )
        if disabled:
            kwargs["aria_disabled"] = "true"
            kwargs["class"] += "  bx--progress-step--disabled"
        elements = [
            Icon(ProgressStep.STATUS[status], size=16),
            hg.P(label, tabindex=0, _class="bx--progress-label"),
            hg.SPAN(_class="bx--progress-line"),
        ]

        if optional:
            elements.insert(2, hg.P(_("Optional"), _class="bx--progress-optional"))

        if tooltip is not None:
            tooltipid = hg.html_id(tooltip, "tooltip-label")
            elements[1]["aria-describedby"] = tooltipid
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
        kwargs["class"] = (
            kwargs.get("class", "")
            + " bx--progress"
            + (" bx--progress--vertical" if vertical else "")
        )
        self.steps = steps
        super().__init__(**kwargs)

    def render(self, context):
        steps = hg.resolve_lazy(self.steps, self, context)
        self.extend((ProgressStep(label, status) for label, status in steps))
        return super().render(context)


"""
<ul data-progress data-progress-current class="bx--progress ">

    <li class="bx--progress-step bx--progress-step--complete "  >
        <svg focusable="false" preserveAspectRatio="xMidYMid meet" style="will-change: transform;" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M8,1C4.1,1,1,4.1,1,8s3.1,7,7,7s7-3.1,7-7S11.9,1,8,1z M8,14c-3.3,0-6-2.7-6-6s2.7-6,6-6s6,2.7,6,6S11.3,14,8,14z"></path><path d="M7 10.8L4.5 8.3 5.3 7.5 7 9.2 10.7 5.5 11.5 6.3z"></path></svg>
      <p tabindex="0" class="bx--progress-label">
          First step
      </p>
      <div id="label-tooltip" role="tooltip" data-floating-menu-direction="bottom" class="bx--tooltip" data-avoid-focus-on-open>
        <span class="bx--tooltip__caret"></span>
        <p class="bx--tooltip__text"></p>
      </div>
        <p class="bx--progress-optional">Optional</p>
      <span class="bx--progress-line"></span>
    </li>
    <li class="bx--progress-step bx--progress-step--current "  >
        <svg>
          <path d="M 7, 7 m -7, 0 a 7,7 0 1,0 14,0 a 7,7 0 1,0 -14,0" ></path>
        </svg>
      <p tabindex="0" class="bx--progress-label" aria-describedby="label-tooltipfddfl7tdjg4">
            Overflow Ex.1
      </p>
      <div id="label-tooltipfddfl7tdjg4" role="tooltip" data-floating-menu-direction="bottom" class="bx--tooltip" data-avoid-focus-on-open>
        <span class="bx--tooltip__caret"></span>
        <p class="bx--tooltip__text">Overflow Ex.1</p>
      </div>
      <span class="bx--progress-line"></span>
    </li>
    <li class="bx--progress-step bx--progress-step--incomplete "  >
          <svg>
            <path d="M8 1C4.1 1 1 4.1 1 8s3.1 7 7 7 7-3.1 7-7-3.1-7-7-7zm0 13c-3.3 0-6-2.7-6-6s2.7-6 6-6 6 2.7 6 6-2.7 6-6 6z"></path>
          </svg>
      <p tabindex="0" class="bx--progress-label" aria-describedby="label-tooltip9rv27he8c08">
            Overflow Ex. 2 Multi Line
      </p>
      <div id="label-tooltip9rv27he8c08" role="tooltip" data-floating-menu-direction="bottom" class="bx--tooltip" data-avoid-focus-on-open>
        <span class="bx--tooltip__caret"></span>
        <p class="bx--tooltip__text">Overflow Ex. 2 Multi Line</p>
      </div>
      <span class="bx--progress-line"></span>
    </li>
    <li class="bx--progress-step bx--progress-step--incomplete "  data-invalid  >
          <svg focusable="false" preserveAspectRatio="xMidYMid meet" style="will-change: transform;" xmlns="http://www.w3.org/2000/svg" class="bx--progress__warning" width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M8,1C4.1,1,1,4.1,1,8s3.1,7,7,7s7-3.1,7-7S11.9,1,8,1z M8,14c-3.3,0-6-2.7-6-6s2.7-6,6-6s6,2.7,6,6S11.3,14,8,14z"></path><path d="M7.5 4H8.5V9H7.5zM8 10.2c-.4 0-.8.3-.8.8s.3.8.8.8c.4 0 .8-.3.8-.8S8.4 10.2 8 10.2z"></path></svg>
      <p tabindex="0" class="bx--progress-label">
          Fourth step
      </p>
      <div id="label-tooltip" role="tooltip" data-floating-menu-direction="bottom" class="bx--tooltip" data-avoid-focus-on-open>
        <span class="bx--tooltip__caret"></span>
        <p class="bx--tooltip__text"></p>
      </div>
      <span class="bx--progress-line"></span>
    </li>
    <li class="bx--progress-step bx--progress-step--incomplete  bx--progress-step--disabled "   aria-disabled="true" >
          <svg>
            <path d="M8 1C4.1 1 1 4.1 1 8s3.1 7 7 7 7-3.1 7-7-3.1-7-7-7zm0 13c-3.3 0-6-2.7-6-6s2.7-6 6-6 6 2.7 6 6-2.7 6-6 6z"></path>
          </svg>
      <p tabindex="0" class="bx--progress-label">
          Fifth step
      </p>
      <div id="label-tooltip" role="tooltip" data-floating-menu-direction="bottom" class="bx--tooltip" data-avoid-focus-on-open>
        <span class="bx--tooltip__caret"></span>
        <p class="bx--tooltip__text"></p>
      </div>
      <span class="bx--progress-line"></span>
    </li>

</ul>
"""
