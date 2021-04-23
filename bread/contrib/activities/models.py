import logging

from django.db import models
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class ActivityBase(models.Model):
    _STATES = (
        ("started", _("Started")),
        ("ongoing", _("Ongoing")),
        ("completed", _("Completed")),
        ("cancelled", _("Cancelled")),
    )
    started = models.DateTimeField(auto_now_add=True, editable=False)
    completed = models.DateTimeField(null=True, editable=False)
    status = models.CharField(max_length=32, choices=_STATES)

    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)
        assert hasattr(cls, "DIAGRAM")
        cls.build_graph()

    @classmethod
    def build_graph(cls):
        assert any(isinstance(i, Initial) for i in cls.DIAGRAM.keys())
        assert any(isinstance(i, ActivityFinal) for i in cls.DIAGRAM.values())
        for node, target in cls.DIAGRAM.items():
            assert isinstance(node, Node)
            if not isinstance(target, tuple):
                target = (target,)
            node.outputs += target
            for t in target:
                assert isinstance(t, Node)
                t.inputs += (node,)
        for node, target in cls.DIAGRAM.items():
            node.verify()
            if not isinstance(target, tuple):
                target = (target,)
            [t.verify() for t in target]

    @classmethod
    def as_dot(cls):
        dot = [
            f'digraph "{cls._meta.verbose_name}" {{',
            "rankdir=TD",
            "concentrate=true",
            "graph[splines=ortho, nodesep=1]",
            "edge[arrowhead=open]",
        ]
        nodes = set()
        edges = []
        for node, target in cls.DIAGRAM.items():
            nodes.add(node)
            if not isinstance(target, tuple):
                target = (target,)
            for t in target:
                nodes.add(t)
                edges.append((node, t))

        dot.extend(n.as_dot() for n in nodes)
        dot.extend(f"{id(n1)} -> {id(n2)}" for n1, n2 in edges)
        dot.append("}")
        return "\n".join(dot)

    def is_done(self):
        return any(
            isinstance(i, ActivityFinal) and i.is_done(self)
            for i in self.DIAGRAM.values()
        )


class Node:
    def __init__(self):
        self.inputs = ()
        self.outputs = ()

    def __init_subclass__(cls, /, **kwargs):
        assert hasattr(cls, "is_done")
        assert callable(cls.is_done)
        assert hasattr(cls, "as_dot")
        assert callable(cls.as_dot)

    def verify(self):
        assert isinstance(self.inputs, tuple)
        assert isinstance(self.outputs, tuple)
        assert all(isinstance(i, Node) for i in self.inputs + self.outputs)


class ActionBase(Node):
    def verify(self):
        super().verify()
        assert len(self.inputs) == 1 and len(self.outputs) == 1

    def is_done(self, activity):
        raise NotImplementedError()

    def as_dot(self):
        return f'{id(self)}[shape=box,style=rounded, label="{self}"]'

    def __str__(self):
        return self.__class__.__name__


class DecisionBase(Node):
    def verify(self):
        super().verify()
        assert len(self.inputs) == 1 and len(self.outputs) == 2

    def decide(self, activity):
        raise NotImplementedError()

    def is_done(self, activity):
        return all(i.is_done(activity) for i in self.inputs)

    def as_dot(self):
        return f'{id(self)}[shape=diamond, label="{self}"]'

    def __str__(self):
        return self.__class__.__name__


class Merge(Node):
    def verify(self):
        super().verify()
        assert len(self.inputs) >= 1 and len(self.outputs) == 1

    def is_done(self, activity):
        return any(i.is_done(activity) for i in self.inputs)

    def as_dot(self):
        return f'{id(self)}[shape=diamond, label=""]'


class Initial(Node):
    def verify(self):
        super().verify()
        assert len(self.inputs) == 0 and len(self.outputs) == 1

    def is_done(self, activity):
        return True

    def as_dot(self):
        return f'{id(self)}[shape=circle, label="", style=filled, fillcolor=black, fixedsize=shape, width=0.2, height=0.2]'


class FlowFinal(Node):
    def verify(self):
        super().verify()
        assert len(self.inputs) == 1 and len(self.outputs) == 0

    def is_done(self, activity):
        return all(i.is_done(activity) for i in self.inputs)

    def as_dot(self):
        return f'{id(self)}[shape=Mcircle, label=""]'


class ActivityFinal(Node):
    def verify(self):
        super().verify()
        assert len(self.inputs) == 1 and len(self.outputs) == 0

    def is_done(self, activity):
        return all(i.is_done(activity) for i in self.inputs)

    def as_dot(self):
        return f'{id(self)}[shape=doublecircle, label="", style=filled, fillcolor=black, fixedsize=shape, width=0.2, height=0.2]'


class Fork(Node):
    def verify(self):
        super().verify()
        assert len(self.inputs) == 1 and len(self.outputs) >= 1

    def is_done(self, activity):
        return all(i.is_done(activity) for i in self.inputs)

    def as_dot(self):
        return f'{id(self)}[shape=box, label="", width={len(self.outputs * 2)}, height=0.2, style="filled, rounded", fillcolor=black]'


class Join(Node):
    def verify(self):
        super().verify()
        assert len(self.inputs) >= 1 and len(self.outputs) == 1

    def is_done(self, activity):
        return all(i.is_done(activity) for i in self.inputs)

    def as_dot(self):
        return f'{id(self)}[shape=box, label="", width={len(self.inputs * 2)}, height=0.2, style="filled, rounded", fillcolor=black]'
