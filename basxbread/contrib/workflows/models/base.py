import re
import subprocess  # nosec because all dealt with

import htmlgenerator as hg
from django.db import models
from django.utils import timezone
from django.utils.html import mark_safe

from .nodes import (
    Action,
    Decision,
    FlowFinal,
    Fork,
    Initial,
    Join,
    Merge,
    Node,
    WorkflowFinal,
)


class WorkflowBase(models.Model):
    """
    This class represents a workflow in the form of a UML Activity Diagram. In order to
    make the purpose of the system more clear the word "Workflow" is used in all places
    instead of "Activity".
    In order to persist state for an instance of a workflow Django models can be used.
    The diagram itself is defined in a class-variable of type dict named ``WORKFLOW``.
    The keys of ``WORKFLOW`` represent source nodes and the values the target nodes.
    Keys always need to be of type :py:class:`basxbread.contrib.acitivities.models.Node`.
    Values must be of type :py:class:`basxbread.contrib.acitivities.models.Node`.
    Exceptions are entries with a Fork node as key and entries with a Decision node as key.
    They require tuple(:py:class:`basxbread.contrib.acitivities.models.Node`) and of type dict{str: :py:class:`basxbread.contrib.acitivities.models.Node`} as values.
    """

    started = models.DateTimeField(auto_now_add=True, editable=False)
    completed = models.DateTimeField(null=True, editable=False)
    cancelled = models.DateTimeField(null=True, editable=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_workflow_state()

    @classmethod
    def workflowdiagram(cls):
        """
        Method which does the magic of converting a graph from simple dict format to
        full fledged activity diagram and do quite a bit of verification. Requires an
        attribute ``WORKFLOW`` of type ``dict``
        """

        if not hasattr(cls, "_GENERATED_DIAGRAM"):
            cls._GENERATED_DIAGRAM = generate_workflowdiagram(cls)
        return cls._GENERATED_DIAGRAM

    @classmethod
    def workflow_as_dot(cls, attrs=None):
        default_attrs = {"splines": "ortho"}
        default_attrs.update(attrs or {})
        dot = [
            f'digraph "{cls._meta.verbose_name}" {{n',
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
    def workflow_as_svg(cls, attrs=None):
        return dot2svg(cls.workflow_as_dot(attrs))

    def active_fields(self):
        ret = []
        for field in self._meta.get_fields():
            if isinstance(field, (Action, Decision)):
                if not field.done(self) and field.hasincoming(self):
                    ret.append(field.name)
        return ret

    def as_dot(self, attrs=None):
        def edgecolor(source, target, choice, instance):
            if isinstance(source, Decision):
                return (
                    "lightgreen"
                    if getattr(instance, source.name) == choice
                    else "black"
                )
            if source.done(instance) and target.done(instance):
                return "lightgreen"
            return "black"

        def nodecolor(node, instance):
            if node.done(instance):
                return "lightgreen"
            if node.hasincoming(instance):
                return "orange"
            return "black"

        default_attrs = {"splines": "ortho", "overlap": "true"}
        default_attrs.update(attrs or {})
        dot = [
            f'digraph "{self._meta.verbose_name}" {{\nranksep=2',
            *[f"{k}={v}" for k, v in default_attrs.items()],
            'graph[bgcolor="#ffffff00" ranksep=1]',
            "edge[arrowhead=open]",
        ]
        nodes = set()
        edges = []
        for source, target, choice in self.workflowdiagram():
            nodes.add(
                source.as_dot(
                    attrs={
                        "fillcolor": "lightgreen" if source.done(self) else "lightgrey",
                        "color": nodecolor(source, self),
                    }
                )
            )
            nodes.add(
                target.as_dot(
                    attrs={
                        "fillcolor": "lightgreen" if target.done(self) else "lightgrey",
                        "color": nodecolor(target, self),
                    }
                )
            )
            edges.append(
                (
                    source,
                    target,
                    f'taillabel = "[{choice}]" labeldistance = 3.0' if choice else "",
                    f"color={edgecolor(source, target, choice, self)}",
                    *(("headport=n",) if isinstance(target, Join) else ()),
                    *(("tailport=s",) if isinstance(target, Fork) else ()),
                )
            )

        dot.extend(n for n in nodes)
        dot.extend(
            f"{id(n1)} -> {id(n2)}[{' '.join(attrs)}]" for n1, n2, *attrs in edges
        )

        dot.append("}")
        return "\n".join(dot)

    def as_svg(self, attrs=None):
        return dot2svg(self.as_dot(attrs))

    @property
    def done(self):
        """Checks whether any Final nodes have been reached"""
        return any(
            isinstance(target, WorkflowFinal) and target.done(self)
            for source, target, choice in self.workflowdiagram()
        )

    def cancel(self, save=True):
        if self.completed:
            raise RuntimeError("Workflow has already completed, cannot cancel")
        self.cancelled = timezone.now()
        if save:
            self.save()

    def save(self, *args, **kwargs):
        if self.pk is not None:
            self.update_workflow_state(runactions=True)
        if not self.completed and not self.cancelled and self.done:
            self.completed = timezone.now()
        super().save(*args, **kwargs)
        self.update_workflow_state(runactions=True)
        super().save(*args, **kwargs)

    def update_workflow_state(self, runactions=False):
        # don't do anything on the workflow after it has been cancelled
        if self.cancelled:
            return
        state_changed = True
        while state_changed:
            nodequeue = [
                source
                for source, target, choice in self.workflowdiagram()
                if isinstance(source, Initial)
            ]
            state_changed = False
            while nodequeue:
                node = nodequeue.pop()
                if not node.done(self):
                    if isinstance(node, Action):
                        if (
                            node.hasincoming(self)
                            and not getattr(self, node.name)
                            and runactions
                        ):
                            actionresult = node.action(self)
                            if actionresult != getattr(self, node.name):
                                state_changed = True
                                setattr(self, node.name, actionresult)
                    if isinstance(node, Decision):
                        if any(n.done(self) for n, c in node.inputs):
                            decision = node.decide(self)
                            if decision != getattr(self, node.name):
                                state_changed = True
                                setattr(self, node.name, decision)
                for outputnode, choice in node.outputs:
                    nodequeue.insert(0, outputnode)

    class Meta:
        abstract = True


def dot2svg(dot: str):
    try:
        process = subprocess.run(  # nosec because fixed arguments and we take the risk of relative path
            ["dot", "-Tsvg"],
            input=dot.encode(),
            capture_output=True,
            check=True,
        )
        svg = process.stdout.decode()
        svg = re.sub('width="[0-9]*pt"', "", svg)
        svg = re.sub('height="[0-9]*pt"', "", svg)
        return mark_safe(svg)
    except subprocess.CalledProcessError as e:
        return mark_safe(
            hg.render(
                hg.DIV(
                    hg.DIV(
                        "Workflow diagram could not be generated, the error message was:"
                    ),
                    hg.DIV(hg.CODE(e)),
                    hg.DIV(hg.CODE(e.stderr.decode())),
                    hg.DIV(hg.PRE(hg.CODE(dot))),
                ),
                {},
            )
        )


def generate_workflowdiagram(model):  # noqa
    """Method which does the magic of converting a graph from simple dict format to
    full fledged activity diagram and do quite a bit of verification. Requires an attribute ``WORKFLOW`` of type ``dict``
    """

    def allnodes(graph):
        return set(sum((list(i[:2]) for i in graph), []))

    assert hasattr(
        model, "WORKFLOW"
    ), f"class {model} needs to have an attribute 'WORKFLOW' with the workflowdefinition"  # nosec because only for API validation
    assert isinstance(  # nosec because only for API validation
        model.WORKFLOW, dict
    ), f"{model}.WORKFLOW needs to be of type {type(dict)}"
    graph = []  # [(source, target, choice)]

    # some type checking
    for node in allnodes(graph):
        assert isinstance(  # nosec because only for API validation
            node, (Node, dict, tuple, type(None))
        ), f"Node {node} if not of type {Node}"

    # flatten the WORKFLOW definition
    for source, target in model.WORKFLOW.items():
        if isinstance(target, tuple):
            graph.extend((source, node, None) for node in target)
        elif isinstance(target, dict):
            assert all(  # nosec because only for API validation
                t is not None for t in target.keys()
            ), "None is not an allowed key for choices"
            graph.extend((source, node, choice) for choice, node in target.items())
        else:
            graph.append((source, target, None))

    # insert initial and final nodes, mostly for activity diagram compliance
    for source, target, choice in list(graph):
        if source not in set(i[1] for i in graph) and not isinstance(source, Initial):
            graph.append((Initial(), source, None))
        if target not in set(i[0] for i in graph) and not isinstance(
            target, WorkflowFinal
        ):
            graph.append((target, WorkflowFinal(), None))
        if target is None:
            graph.append((target, FlowFinal(), None))

    # insert merge nodes
    removed_edges = []
    new_edges = []
    for node in allnodes(graph):
        inputs = [[s, choice] for s, t, choice in graph if t == node]
        if len(inputs) > 1 and not isinstance(node, (Join, Merge)):
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
            [t, choice] for s, t, choice in graph if s == node and choice is None
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

    # set inputs and outputs per node and verify all nodes
    for node in allnodes(graph):
        node.inputs = tuple(
            [(source, choice) for source, target, choice in graph if target == node]
        )
        node.outputs = tuple(
            [(target, choice) for source, target, choice in graph if source == node]
        )
        node._node_verify()
    return graph
