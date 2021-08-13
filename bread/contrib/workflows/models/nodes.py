import math

from django.db import models


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

    def done(self, workflowinstance):
        """Returns True if this node can be considered done. This method should never have side effects (changing the database)"""
        return self.hasincoming(workflowinstance)

    def hasincoming(self, workflowinstance):
        return any(
            i.done(workflowinstance)
            and (not isinstance(i, Decision) or getattr(workflowinstance, i.name) == c)
            for i, c in self.inputs
        )

    def __str__(self):
        return str(self.verbose_name or self.__class__.__name__)

    def _node_verify(self):
        ALLOWED_NODES_TYPES = (Node, models.CharField, models.BooleanField)
        assert isinstance(self.inputs, tuple)  # nosec because only for API validation
        assert isinstance(self.outputs, tuple)  # nosec because only for API validation
        for node, choice in self.inputs + self.outputs:
            assert isinstance(  # nosec because only for API validation
                node, ALLOWED_NODES_TYPES
            ), f"Nodes in the workflow must be of type {ALLOWED_NODES_TYPES}"
            if isinstance(node, models.CharField):
                assert hasattr(  # nosec because only for API validation
                    node, "choices"
                ), f"Node {node} needs to have attribute 'choices'"

    def dot_attrs(self):
        return {}

    def as_dot(self, attrs=None):
        attrs = ", ".join(
            f"{k}={v}"
            for k, v in {
                "label": f'"{self}"',
                "tooltip": f'"{getattr(self, "help_text", self)}"',
                **self.dot_attrs(),
                **(attrs or {}),
            }.items()
        )
        return f"{id(self)}[{attrs}]"


class Action(models.BooleanField, Node):
    """
    Represents an action node in an Workflow Diagram.
    Should be subclassed with an optional implementation for ``action()``
    Changes should only happen through the ``do()`` method or user actions.
    Cannot be null, default is always False
    """

    def __init__(self, *args, **kwargs):
        kwargs["default"] = False
        kwargs["null"] = False
        super().__init__(*args, **kwargs)  # MRO says we call BooleanField.__init__
        self.inputs = ()
        self.outputs = ()

    def done(self, instance):
        return super().done(instance) and getattr(instance, self.name)

    def action(self, instance):
        """
        Should run automated actions and return True if the action was successfull
        The default just returns the value of the field which is makes this a manual action which will be confirmed through checking the checkbox for this field.
        This method can be called multiple times and should therefore be idempotent, but only if done does not return True
        """
        return getattr(instance, self.name)

    def __str__(self):
        return str(self.verbose_name or self.__class__.__name__)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if "default" in kwargs:
            del kwargs["default"]
        if "null" in kwargs:
            del kwargs["null"]
        return name, path, args, kwargs

    def _node_verify(self):
        super()._node_verify()
        assert (  # nosec because only for API validation
            len(self.inputs) == 1 and len(self.outputs) == 1
        ), f"{self} can only have one input and one output"

    def dot_attrs(self):
        return {"shape": "box", "style": "rounded"}


class Decision(models.CharField, Node):
    def __init__(self, *args, choices=None, **kwargs):
        kwargs["default"] = None
        kwargs["null"] = True
        kwargs["blank"] = True
        kwargs["max_length"] = 255
        assert choices is not None  # nosec because only for API validation
        super().__init__(
            *args, choices=choices, **kwargs
        )  # MRO says we call BooleanField.__init__
        self.inputs = ()
        self.outputs = ()

    def decide(self, instance):
        """
        Should run automated decisions and return the according value if a decision has been made
        The default just returns the value of the field which is makes this a manual decision which will be confirmed through selection an option on the form field.
        This method can be called multiple times and should therefore be idempotent
        """
        return getattr(instance, self.name)

    def done(self, instance):
        return super().done(instance) and getattr(instance, self.name) is not None

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if "default" in kwargs:
            del kwargs["default"]
        if "null" in kwargs:
            del kwargs["null"]
        if "blank" in kwargs:
            del kwargs["blank"]
        if "max_length" in kwargs:
            del kwargs["max_length"]
        return name, path, args, kwargs

    def __str__(self):
        return str(self.verbose_name or self.__class__.__name__) + "?"

    def _node_verify(self):
        super()._node_verify()
        assert len(self.inputs) == 1  # nosec because only for API validation
        assert len(self.outputs) > 1  # nosec because only for API validation
        assert len(self.choices) == len(  # nosec because only for API validation
            self.outputs
        )

    def dot_attrs(self):
        return {
            "shape": "diamond",
            "label": '""',
            "xlabel": '"' + str(self) + '"',
            "fixedsize": "TRUE",
            "width": 0.5,
            "height": 0.5,
        }


# Fixed Workflow Diagram nodes which should in general not be subclassed


class Merge(Node):
    def _node_verify(self):
        super()._node_verify()
        assert (  # nosec because only for API validation
            len(self.inputs) >= 1 and len(self.outputs) == 1
        )

    def dot_attrs(self):
        return {
            "shape": "diamond",
            "label": '""',
            "fixedsize": "TRUE",
            "width": 0.5,
            "height": 0.5,
        }


class Initial(Node):
    def done(self, workflowinstance):
        return True

    def _node_verify(self):
        super()._node_verify()
        assert (  # nosec because only for API validation
            len(self.inputs) == 0 and len(self.outputs) == 1
        )

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
        assert (  # nosec because only for API validation
            len(self.inputs) == 1 and len(self.outputs) == 0
        )

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
        assert (  # nosec because only for API validation
            len(self.inputs) == 1 and len(self.outputs) == 0
        )

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
        assert (  # nosec because only for API validation
            len(self.inputs) == 1 and len(self.outputs) >= 1
        )

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
    def done(self, workflowinstance):
        return super().done(workflowinstance) and all(
            i.done(workflowinstance) for i, c in self.inputs
        )

    def _node_verify(self):
        super()._node_verify()
        assert (  # nosec because only for API validation
            len(self.inputs) >= 1 and len(self.outputs) == 1
        )

    def dot_attrs(self):
        return {
            "shape": "box",
            "label": '""',
            "style": '"filled, rounded"',
            "fillcolor": "black",
            "width": math.floor(len(self.inputs) * 1.5),
            "height": 0.1,
        }
