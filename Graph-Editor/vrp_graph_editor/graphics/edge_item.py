"""Grafisches Kantenitem für die QGraphicsScene."""

from __future__ import annotations

from typing import TYPE_CHECKING

import networkx as nx
from PySide6.QtCore import QLineF, QPointF, Qt
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsLineItem, QGraphicsSimpleTextItem

from vrp_graph_editor.config.defaults import DEFAULT_EDGE_COLOR
from vrp_graph_editor.model.attributes import valid_color

if TYPE_CHECKING:
    from vrp_graph_editor.app.graph_scene import GraphScene


class EdgeItem(QGraphicsLineItem):
    """Interaktives Item für eine Graphkante."""

    def __init__(self, u: str, v: str, graph: nx.Graph, scene_ref: "GraphScene"):
        super().__init__()
        self.u = u
        self.v = v
        self.graph = graph
        self.scene_ref = scene_ref
        self._selected = False

        self.label_item = QGraphicsSimpleTextItem(self)
        self.label_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.label_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(0)

        self.update_from_graph()
        self.update_position()

    def attrs(self) -> dict:
        return self.graph.edges[self.u, self.v]

    def update_from_graph(self) -> None:
        attrs = self.attrs()
        color = valid_color(str(attrs.get("color", DEFAULT_EDGE_COLOR)), DEFAULT_EDGE_COLOR)
        width = max(0.1, float(attrs.get("width", 2.0)))
        attrs["color"] = color
        attrs["width"] = width

        draw_width = width + (1.5 if self._selected else 0.0)
        self.setPen(QPen(QColor(color), draw_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        label = str(attrs.get("label", ""))
        self.label_item.setText(label)
        self.setToolTip(
            f"Kante: {self.u} – {self.v}\n"
            f"Label: {label}\n"
            f"Weight: {attrs.get('weight', 0.0)}\n"
            f"Width: {width}"
        )
        self.update_label_position()

    def update_position(self) -> None:
        node_u = self.scene_ref.node_items.get(self.u)
        node_v = self.scene_ref.node_items.get(self.v)
        if node_u is None or node_v is None:
            return
        p1 = node_u.scenePos()
        p2 = node_v.scenePos()
        self.setLine(QLineF(p1, p2))
        self.update_label_position()

    def update_label_position(self) -> None:
        line = self.line()
        midpoint = QPointF((line.x1() + line.x2()) / 2.0, (line.y1() + line.y2()) / 2.0)
        br = self.label_item.boundingRect()
        self.label_item.setPos(midpoint.x() - br.width() / 2.0, midpoint.y() - br.height() / 2.0 - 4.0)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self._selected = bool(value)
            if self.u in self.graph and self.v in self.graph[self.u]:
                self.update_from_graph()
        return super().itemChange(change, value)
