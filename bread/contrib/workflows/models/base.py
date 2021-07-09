import math
import subprocess

import htmlgenerator as hg
from django.db import models


class WorkflowBase(models.Model):
    """
    This class represents a workflow in the form of a UML Activity Diagram. In order to
    make the purpose of the system more clear the word "Workflow" is used in all places
    instead of "Activity".
    In order to persist state for an instance of a workflow Django models can be used.
    The diagram itself is defined in a class-variable of type dict named ``WORKFLOW``.
    The keys of ``WORKFLOW`` represent source nodes and the values the target nodes.
    Keys always need to be of type :py:class:`bread.contrib.acitivities.models.Node`.
    Values must be of type :py:class:`bread.contrib.acitivities.models.Node`.
    Exceptions are entries with a Fork node as key and entries with a Decision node as key.
    They require tuple(:py:class:`bread.contrib.acitivities.models.Node`) and of type dict{str: :py:class:`bread.contrib.acitivities.models.Node`} as values.
    """

    started = models.DateTimeField(auto_now_add=True, editable=False)
    completed = models.DateTimeField(null=True, editable=False)
    cancelled = models.DateTimeField(null=True, editable=False)

    @classmethod
    def workflowdiagram(cls):  # noqa
        def allnodes(graph):
            return set(sum((list(i[:2]) for i in graph), []))

        if hasattr(cls, "_GENERATED_DIAGRAM"):
            return cls._GENERATED_DIAGRAM
        assert hasattr(cls, "WORKFLOW")
        assert isinstance(cls.WORKFLOW, dict)
        graph = []  # [(source, target, choice)]

        # some type checking
        for node in allnodes(graph):
            assert isinstance(
                node, (Node, dict, tuple, type(None))
            ), f"Node {node} if not of type {Node}"

        # flatten the WORKFLOW definition
        for source, target in cls.WORKFLOW.items():
            if isinstance(target, tuple):
                graph.extend((source, node, None) for node in target)
            elif isinstance(target, dict):
                assert all(
                    t is not None for t in target.keys()
                ), "None is not an allowed key for choices"
                graph.extend((source, node, choice) for choice, node in target.items())
            else:
                graph.append((source, target, None))

        # insert initial and final nodes, mostly for activity diagram compliance
        for source, target, choice in list(graph):
            if source not in set(i[1] for i in graph):
                graph.append((Initial(), source, None))
            if target not in set(i[0] for i in graph):
                graph.append((target, WorkflowFinal(), None))
            if target is None:
                graph.append((target, FlowFinal(), None))

        # insert merge nodes
        removed_edges = []
        new_edges = []
        for node in allnodes(graph):
            inputs = [[s, choice] for s, t, choice in graph if t == node]
            if len(inputs) > 1:
                mergenode = Merge()
                new_edges.append((mergenode, node, None))
                for inputnode, choice in inputs:
                    new_edges.append((inputnode, mergenode, choice))
                    removed_edges.append((inputnode, node, choice))
        for edge in removed_edges:
            graph.remove(edge)
        graph.extend(new_edges)

        # insert fork nodes
        removed_edges = []
        new_edges = []
        for node in allnodes(graph):  # check if node needs to be a fork node
            outputs = [
                [s, choice] for s, t, choice in graph if s == node and choice is None
            ]
            if len(outputs) > 1:
                forknode = Fork()
                new_edges.append((node, forknode, None))
                for outputnode, choice in outputs:
                    new_edges.append((forknode, outputnode, choice))
                    removed_edges.append((node, outputnode, choice))
        for edge in removed_edges:
            graph.remove(edge)
        graph.extend(new_edges)

        # set inputs and outputs per node and verify
        for node in allnodes(graph):
            node.inputs = tuple(
                [source for source, target, choice in graph if target == node]
            )
            node.outputs = tuple(
                [target for source, target, choice in graph if source == node]
            )
            node._node_verify()
        cls._GENERATED_DIAGRAM = graph
        return cls._GENERATED_DIAGRAM

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
        for source, target, choice in cls.workflowdiagram():
            nodes.add(source.as_dot())
            nodes.add(target.as_dot())
            edges.append(
                (
                    source,
                    target,
                    f'taillabel = "[{choice}]" labeldistance = 3.0' if choice else "",
                )
            )

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
                        "Workflow diagram could not be generated, the error message was:"
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
        # helpnodes = (
        # ("Start node", Initial()),
        # ("End node, will finish activity", WorkflowFinal()),
        # ("End node, will finish branch but no activity", FlowFinal()),
        # ("Decision node", GenericDecision(lambda s, a: None, label=" ")),
        # ("Action node", Action(lambda s, a: None, verbose_name=" ")),  # TODO!!! FIX
        # )
        # dot.extend(n.as_dot({"xlabel": '"' + label + '"'}) for label, n in helpnodes)
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
                        "Workflow diagram could not be generated, the error message was:"
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
            isinstance(i, WorkflowFinal) and i.done(self)
            for i in self.workflowdiagram().values()
        )

    class Meta:
        abstract = True


class Node:
    """
    The base class for all nodes in an Workflow Diagram.
    Should normally not need to be directly subclassed.
    Instead subclass Actionand Decision.
    """

    def __init__(self, verbose_name=None):
        self.inputs = ()
        self.outputs = ()
        self.verbose_name = verbose_name

    def _node_verify(self):
        ALLOWED_NODES_TYPES = (Node, models.CharField, models.BooleanField)
        assert isinstance(self.inputs, tuple)
        assert isinstance(self.outputs, tuple)
        for node in self.inputs + self.outputs:
            assert isinstance(
                node, ALLOWED_NODES_TYPES
            ), f"Nodes in the workflow must be of type {ALLOWED_NODES_TYPES}"
            if isinstance(node, models.CharField):
                assert hasattr(
                    node, "choices"
                ), f"Node {node} needs to have attribute 'choices'"

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
        return str(self.verbose_name or self.__class__.__name__)


class Action(models.BooleanField, Node):
    """
    Represents an action node in an Workflow Diagram.
    Should be subclassed with an implementation for ``done()`` and optionally one for ``do()``
    Changes should only happen through the ``do()`` method or user actions.
    Cannot be null, default is always False
    """

    def __init__(self, *args, **kwargs):
        kwargs["default"] = False
        kwargs["null"] = False
        super().__init__(*args, **kwargs)  # MRO says we call BooleanField.__init__
        self.inputs = ()
        self.outputs = ()

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if "default" in kwargs:
            del kwargs["default"]
        if "null" in kwargs:
            del kwargs["null"]
        return name, path, args, kwargs

    def _node_verify(self):
        super()._node_verify()
        assert (
            len(self.inputs) == 1 and len(self.outputs) == 1
        ), f"{self} can only have one input and one output"

    def dot_attrs(self):
        return {"shape": "box", "style": "rounded"}

    def pre_save(self, model_instance, add):
        value = super().pre_save()
        if not value:
            value = self.action(model_instance)
            setattr(model_instance, self.attname, value)
        return value

    def action(self, instance):
        """
        Should run automated actions and return True if the action was successfull
        """
        return False

    def __str__(self):
        return str(self.verbose_name or self.__class__.__name__)


class Decision(models.CharField, Node):
    def __init__(self, *args, choices=None, **kwargs):
        kwargs["default"] = None
        kwargs["null"] = True
        kwargs["max_length"] = 255
        assert choices is not None
        super().__init__(
            *args, choices=choices, **kwargs
        )  # MRO says we call BooleanField.__init__
        self.inputs = ()
        self.outputs = ()

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if "default" in kwargs:
            del kwargs["default"]
        if "null" in kwargs:
            del kwargs["null"]
        if "max_length" in kwargs:
            del kwargs["max_length"]
        return name, path, args, kwargs

    def _node_verify(self):
        super()._node_verify()
        print(self)
        assert len(self.inputs) == 1
        assert len(self.outputs) > 1
        assert len(self.choices) == len(self.outputs)

    def dot_attrs(self):
        return {
            "shape": "diamond",
            "label": '""',
            "tooltip": '"' + str(self) + '"',
            "xlabel": '"' + str(self) + '"',
            "fixedsize": "TRUE",
            "width": 0.5,
            "height": 0.5,
        }

    def pre_save(self, model_instance, add):
        value = super().pre_save()
        if value is None:
            value = self.decide(model_instance)
            setattr(model_instance, self.attname, value)
        return value

    def decide(self, instance):
        """
        Should run automated decisions and return the according value if a decision has been made
        """
        return None

    def __str__(self):
        return str(self.verbose_name or self.__class__.__name__) + "?"


# Fixed Workflow Diagram nodes which should in general not be subclassed


class Merge(Node):
    def _node_verify(self):
        super()._node_verify()
        assert len(self.inputs) >= 1 and len(self.outputs) == 1

    def done(self, activity):
        return any(i.done(activity) for i in self.inputs)

    def dot_attrs(self):
        return {
            "shape": "diamond",
            "label": '""',
            "fixedsize": "TRUE",
            "width": 0.5,
            "height": 0.5,
        }


class Initial(Node):
    def _node_verify(self):
        super()._node_verify()
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
    def _node_verify(self):
        super()._node_verify()
        assert len(self.inputs) == 1 and len(self.outputs) == 0

    def dot_attrs(self):
        return {
            "shape": "circle",
            "label": '"X"',
            "fixedsize": "shape",
            "width": 0.2,
            "height": 0.2,
        }


class WorkflowFinal(Node):
    def _node_verify(self):
        super()._node_verify()
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
    def _node_verify(self):
        super()._node_verify()
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
    def _node_verify(self):
        super()._node_verify()
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
