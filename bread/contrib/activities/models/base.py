import math
import subprocess

import htmlgenerator as hg
from django.db import models


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

    started = models.DateTimeField(auto_now_add=True, editable=False)
    completed = models.DateTimeField(null=True, editable=False)
    cancelled = models.DateTimeField(null=True, editable=False)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        assert hasattr(cls, "DIAGRAM")
        assert isinstance(cls.DIAGRAM, dict)
        cls.build_internal_diagram()
        cls.build_graph()

    @classmethod
    def build_internal_diagram(cls):
        cls._GENERATED_DIAGRAM = {}
        for source, target in cls.DIAGRAM.items():
            # automatically generte initial nodes for nodes without incoming edges
            if source not in cls.DIAGRAM.values():
                cls._GENERATED_DIAGRAM[Initial()] = source
            # automatically generte flow final nodes for nodes who have None as target
            if target is None:
                target = FlowFinal()
            # automatically generate Activity final nodes for nodes without outgoing edges
            elif not isinstance(target, dict) and target not in cls.DIAGRAM:
                target = ActivityFinal()

            # automatically generte merge nodes
            if list(cls.DIAGRAM.values()).count(target) > 1:
                try:
                    mergenode = list(cls._GENERATED_DIAGRAM.keys())[
                        list(cls._GENERATED_DIAGRAM.values()).index(target)
                    ]
                except ValueError:
                    mergenode = Merge()
                    cls._GENERATED_DIAGRAM[mergenode] = target
                cls._GENERATED_DIAGRAM[source] = mergenode
            # generate fork nodes
            elif isinstance(target, tuple):
                cls._GENERATED_DIAGRAM[source] = Fork()
                for node in target:
                    cls._GENERATED_DIAGRAM[cls._GENERATED_DIAGRAM[source]] = node
            elif isinstance(target, dict):
                assert hasattr(
                    source, "choices"
                ), f"Node {source} needs to be a Django field with attribute 'choices'"
                cls._GENERATED_DIAGRAM[DecisionBase()] = target
            else:
                cls._GENERATED_DIAGRAM[source] = target

    @classmethod
    def build_graph(cls):
        assert any(isinstance(i, Initial) for i in cls._GENERATED_DIAGRAM.keys())
        assert any(
            isinstance(i, ActivityFinal) for i in cls._GENERATED_DIAGRAM.values()
        )
        for node, target in cls._GENERATED_DIAGRAM.items():
            if isinstance(target, dict):
                assert isinstance(
                    node, DecisionBase
                ), f"Node {node} has a dict value but no 'choices' attributes"
                node.decision_labels = tuple(target.keys())
                target = tuple(target.values())
            assert isinstance(
                node, Node
            ), f"Node {node} is not of instance Node but {type(node)}"
            if not isinstance(target, tuple):
                target = (target,)
            node.outputs += target
            for t in target:
                assert isinstance(t, Node), f"{t} is not of instance Node but {type(t)}"
                t.inputs += (node,)
        for node, target in cls._GENERATED_DIAGRAM.items():
            node.verify()
            if isinstance(node, DecisionBase):
                target = tuple(target.values())
            if not isinstance(target, tuple):
                target = (target,)
            [t.verify() for t in target]

    @classmethod
    def as_dot(cls, attrs=None):
        default_attrs = {}
        default_attrs.update(attrs or {})
        dot = [
            f'digraph "{cls._meta.verbose_name}" {{',
            *[f"{k}={v}" for k, v in default_attrs.items()],
            'graph[bgcolor="#ffffff00" ranksep=1]',
            "edge[arrowhead=open]",
        ]
        nodes = set()
        edges = []
        for node, target in cls._GENERATED_DIAGRAM.items():
            nodes.add(node.as_dot())
            if isinstance(target, dict):
                target = tuple(target.values())
            if not isinstance(target, tuple):
                target = (target,)
            for i, t in enumerate(target):
                nodes.add(t.as_dot())
                if isinstance(node, DecisionBase):
                    edges.append(
                        (
                            node,
                            t,
                            f'xlabel = "[{node.decision_labels[i]}]"',
                        )
                    )
                else:
                    edges.append((node, t))

        dot.extend(n for n in nodes)
        dot.extend(
            f"{id(n1)} -> {id(n2)}[{' '.join(attrs)}]" for n1, n2, *attrs in edges
        )

        dot.append("}")
        return "\n".join(dot)

    @classmethod
    def as_svg(cls, attrs=None):
        dot = cls.as_dot(attrs).encode()
        try:
            process = subprocess.run(
                ["dot", "-Tsvg"],
                input=dot,
                capture_output=True,
                check=True,
            )
            return process.stdout.decode()
        except subprocess.CalledProcessError as e:
            return hg.render(
                hg.DIV(
                    hg.DIV(
                        "Activity diagram could not be generated, the error message was:"
                    ),
                    hg.DIV(hg.CODE(e)),
                    hg.DIV(hg.CODE(e.stderr.decode())),
                    hg.DIV(hg.PRE(hg.CODE(dot.decode()))),
                ),
                {},
            )

    @classmethod
    def help_as_dot(cls, attrs=None):
        default_attrs = {"rankdir": "LR"}
        default_attrs.update(attrs or {})
        dot = [
            f'digraph "{cls._meta.verbose_name}" {{',
            *[f"{k}={v}" for k, v in default_attrs.items()],
            'graph[bgcolor="#ffffff00", ranksep=5]',
            "edge[arrowhead=open]",
        ]
        helpnodes = (
            ("Start node", Initial()),
            ("End node, will finish activity", ActivityFinal()),
            ("End node, will finish branch but no activity", FlowFinal()),
            # ("Decision node", GenericDecision(lambda s, a: None, label=" ")),
            ("Action node", Action(lambda s, a: None, label=" ")),
        )

        dot.extend(n.as_dot({"xlabel": '"' + label + '"'}) for label, n in helpnodes)
        dot.append("}")
        return "\n".join(dot)

    @classmethod
    def help_as_svg(cls, attrs=None):
        dot = cls.help_as_dot(attrs).encode()
        try:
            process = subprocess.run(
                ["dot", "-Tsvg"],
                input=dot,
                capture_output=True,
                check=True,
            )
            return process.stdout.decode()
        except subprocess.CalledProcessError as e:
            return hg.render(
                hg.DIV(
                    hg.DIV(
                        "Activity diagram could not be generated, the error message was:"
                    ),
                    hg.DIV(hg.CODE(e)),
                    hg.DIV(hg.CODE(e.stderr.decode())),
                    hg.DIV(hg.PRE(hg.CODE(dot.decode()))),
                ),
                {},
            )

    @property
    def done(self):
        return any(
            isinstance(i, ActivityFinal) and i.done(self)
            for i in self._GENERATED_DIAGRAM.values()
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
        return {}

    def as_dot(self, attrs=None):
        attrs = ", ".join(
            f"{k}={v}"
            for k, v in {
                "label": f'"{self}"',
                **self.dot_attrs(),
                **(attrs or {}),
            }.items()
        )
        return f"{id(self)}[{attrs}]"

    def __str__(self):
        return str(self.label or self.__class__.__name__)


# Action node and Decision node, need to be sublassed


class Action(models.BooleanField, Node):
    """
    Represents an action node in an Activity Diagram.
    Should be subclassed with an implementation for ``done()`` and optionally one for ``do()``
    Changes should only happen through the ``do()`` method or user actions.
    """

    def __init__(self, *args, action, **kwargs):
        self.action = action
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs["max_length"]
        return name, path, args, self.action, kwargs

    def verify(self):
        super().verify()
        assert (
            len(self.inputs) == 1 and len(self.outputs) == 1
        ), f"{self} can only have one input and one output"

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
        return {
            "shape": "circle",
            "label": '"X"',
            "fixedsize": "shape",
            "width": 0.2,
            "height": 0.2,
        }


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
