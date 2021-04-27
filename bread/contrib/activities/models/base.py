import logging
import math

from django.db import models
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class ActivityBase(models.Model):
    """
    This class represents a single UML Activity Diagram.
    In order to persist state for an instance of an activity Django models can be used.
    The diagram itself is defined in a class-variable of type dict named ``DIAGRAM``.
    The keys of ``DIAGRAM`` represent source nodes and the values the target nodes.
    Keys always need to be of type :py:class:`bread.contrib.acitivities.models.Node`.
    Values must be of type :py:class:`bread.contrib.acitivities.models.Node`.
    Exceptions are entries with a Fork node as key and entries with a DecisionBase node as key.
    They require tuple(:py:class:`bread.contrib.acitivities.models.Node`) and of type dict{str: :py:class:`bread.contrib.acitivities.models.Node`} as values.
    """

    _STATES = (
        ("ongoing", _("Ongoing")),
        ("completed", _("Completed")),
        ("cancelled", _("Cancelled")),
    )
    started = models.DateTimeField(auto_now_add=True, editable=False)
    completed = models.DateTimeField(null=True, editable=False)
    status = models.CharField(max_length=32, choices=_STATES, default=_STATES[0][0])

    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)
        assert hasattr(cls, "DIAGRAM")
        assert isinstance(cls.DIAGRAM, dict)
        cls.build_graph()

    @classmethod
    def build_graph(cls):
        assert any(isinstance(i, Initial) for i in cls.DIAGRAM.keys())
        assert any(isinstance(i, ActivityFinal) for i in cls.DIAGRAM.values())
        for node, target in cls.DIAGRAM.items():
            if isinstance(node, DecisionBase):
                node.decision_labels = tuple(target.keys())
                target = tuple(target.values())
            assert isinstance(node, Node)
            if not isinstance(target, tuple):
                target = (target,)
            node.outputs += target
            for t in target:
                assert isinstance(t, Node)
                t.inputs += (node,)
        for node, target in cls.DIAGRAM.items():
            node.verify()
            if isinstance(node, DecisionBase):
                target = tuple(target.values())
            if not isinstance(target, tuple):
                target = (target,)
            [t.verify() for t in target]

    @classmethod
    def as_dot(cls, attrs=None):
        default_attrs = {
            "rankdir": "TD",
            "concentrate": "true",
        }
        default_attrs.update(attrs or {})
        dot = [
            f'digraph "{cls._meta.verbose_name}" {{',
            *[f"{k}={v}" for k, v in default_attrs.items()],
            "graph[splines=ortho, nodesep=1]",
            "edge[arrowhead=open]",
        ]
        nodes = set()
        edges = []
        for node, target in cls.DIAGRAM.items():
            nodes.add(node.as_dot())
            if isinstance(target, dict):
                target = tuple(target.values())
            if not isinstance(target, tuple):
                target = (target,)
            for i, t in enumerate(target):
                nodes.add(t.as_dot())
                if isinstance(node, DecisionBase):
                    edges.append((node, t, f"xlabel = {node.decision_labels[i]}"))
                else:
                    edges.append((node, t))

        dot.extend(n for n in nodes)
        dot.extend(
            f"{id(n1)} -> {id(n2)}[{' '.join(attrs)}]" for n1, n2, *attrs in edges
        )
        dot.append("}")
        return "\n".join(dot)

    def done(self):
        def _recursive_check():
            pass

        return any(
            isinstance(i, ActivityFinal) and i.done(self) for i in self.DIAGRAM.values()
        )

    class Meta:
        abstract = True


class Node:
    """
    The base class for all nodes in an Activity Diagram.
    Should normally not need to be directly subclassed.
    Instead subclass ActionBase and DecisionBase.
    """

    def __init__(self, label=None):
        self.inputs = ()
        self.outputs = ()
        self.label = label

    def verify(self):
        assert isinstance(self.inputs, tuple)
        assert isinstance(self.outputs, tuple)
        assert all(isinstance(i, Node) for i in self.inputs + self.outputs)

    def done(self, activity):
        """Returns True if this node can be considered done. This method should never have side effects (changing the database)"""
        return all(i.done(activity) for i in self.inputs)

    def dot_attrs(self):
        return

    def as_dot(self):
        attrs = ", ".join(
            f"{k}={v}" for k, v in {"label": f'"{self}"', **self.dot_attrs()}.items()
        )
        return f"{id(self)}[{attrs}]"

    def __str__(self):
        return self.label or self.__class__.__name__


# Action node and Decision node, need to be sublassed


class ActionBase(Node):
    """
    Represents an action node in an Activity Diagram.
    Should be subclassed with an implementation for ``done()`` and optionally one for ``do()``
    Changes should only happen through the ``do()`` method or user actions.
    """

    def verify(self):
        super().verify()
        assert (
            len(self.inputs) == 1 and len(self.outputs) == 1
        ), f"{self} can only have one input and one output"

    def done(self, activity):
        raise NotImplementedError()

    def do(self, activity):
        pass

    def dot_attrs(self):
        return {"shape": "box", "style": "rounded"}


class DecisionBase(Node):
    """
    Represents an decision node in an Activity Diagram.
    Should be subclassed to implemented the "decide" method
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.decision_labels = ()

    def verify(self):
        super().verify()
        assert len(self.inputs) == 1 and len(self.outputs) == 2
        assert len(self.decision_labels) == len(self.outputs)

    def decide(self, activity):
        """
        Should return a string of one of the ``decision_labels`` keys.
        The execution flow of the diagram will follw the output with the according key.
        """
        raise NotImplementedError()

    def dot_attrs(self):
        return {"shape": "diamond"}


# Fixed Activity Diagram nodes which should in general not be subclassed


class Merge(Node):
    def verify(self):
        super().verify()
        assert len(self.inputs) >= 1 and len(self.outputs) == 1

    def done(self, activity):
        return any(i.done(activity) for i in self.inputs)

    def dot_attrs(self):
        return {"shape": "diamond", "label": '""'}


class Initial(Node):
    def verify(self):
        super().verify()
        assert len(self.inputs) == 0 and len(self.outputs) == 1

    def dot_attrs(self):
        return {
            "shape": "circle",
            "label": '""',
            "style": "filled",
            "fillcolor": "black",
            "fixedsize": "shape",
            "width": 0.2,
            "height": 0.2,
        }


class FlowFinal(Node):
    def verify(self):
        super().verify()
        assert len(self.inputs) == 1 and len(self.outputs) == 0

    def dot_attrs(self):
        return {"shape": "Mcircle", "label": '""'}


class ActivityFinal(Node):
    def verify(self):
        super().verify()
        assert len(self.inputs) == 1 and len(self.outputs) == 0

    def dot_attrs(self):
        return {
            "shape": "doublecircle",
            "label": '""',
            "style": "filled",
            "fillcolor": "black",
            "fixedsize": "shape",
            "width": 0.2,
            "height": 0.2,
        }


class Fork(Node):
    def verify(self):
        super().verify()
        assert len(self.inputs) == 1 and len(self.outputs) >= 1

    def dot_attrs(self):
        return {
            "shape": "box",
            "label": '""',
            "style": '"filled, rounded"',
            "fillcolor": "black",
            "width": math.floor(len(self.outputs) * 1.5),
            "height": 0.1,
        }


class Join(Node):
    def verify(self):
        super().verify()
        assert len(self.inputs) >= 1 and len(self.outputs) == 1

    def dot_attrs(self):
        return {
            "shape": "box",
            "label": '""',
            "style": '"filled, rounded"',
            "fillcolor": "black",
            "width": math.floor(len(self.inputs) * 1.5),
            "height": 0.1,
        }


# Implementation of a generic Action and a generic Decision which
# just take the according done, do and decision functions


class GenericAction(ActionBase):
    def __init__(self, done_func, do_func=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.done = done_func
        if do_func is not None:
            self.do = do_func


class GenericDecision(DecisionBase):
    def __init__(self, decision_func, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.decision = decision_func
