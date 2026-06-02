"""Grafisches Knotenitem für die QGraphicsScene."""

from __future__ import annotations

from typing import TYPE_CHECKING

import networkx as nx
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem, QGraphicsSimpleTextItem

from vrp_graph_editor.config.defaults import (
    DEFAULT_EDGE_COLOR,
    DEFAULT_NODE_COLOR,
    DEFAULT_PENDING_EDGE_COLOR,
    DEFAULT_SELECTED_NODE_COLOR,
    NODE_RADIUS,
)
from vrp_graph_editor.model.attributes import normalize_time_window, valid_color

if TYPE_CHECKING:
    from vrp_graph_editor.app.graph_scene import GraphScene


class NodeItem(QGraphicsEllipseItem):
    """Interaktives Item für einen Graphknoten."""

    def __init__(self, node_id: str, graph: nx.Graph):
        super().__init__(-NODE_RADIUS, -NODE_RADIUS, 2 * NODE_RADIUS, 2 * NODE_RADIUS)
        self.node_id = node_id
        self.graph = graph
        self._pending_edge_start = False
        self._selected = False

        self.label_item = QGraphicsSimpleTextItem(self)
        self.label_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.label_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(10)

        self.update_from_graph()

    def update_from_graph(self) -> None:
        attrs = self.graph.nodes[self.node_id]
        color = valid_color(str(attrs.get("color", DEFAULT_NODE_COLOR)), DEFAULT_NODE_COLOR)
        attrs["color"] = color
        self.setBrush(QBrush(QColor(color)))
        self._refresh_pen()

        label = str(attrs.get("label", self.node_id))
        self.label_item.setText(label)
        self._center_label()

        tw = normalize_time_window(attrs.get("time_window", [0.0, 0.0]))
        attrs["time_window"] = tw
        tooltip = (
            f"ID: {self.node_id}\n"
            f"Label: {label}\n"
            f"Bedarf: {attrs.get('demand', 0.0)}\n"
            f"Time Window: [{tw[0]}, {tw[1]}]\n"
            f"Klassifizierung: {attrs.get('classification', '')}\n"
            f"Position: {attrs.get('position', [0.0, 0.0])}"
        )
        self.setToolTip(tooltip)

    def set_pending_edge_start(self, pending: bool) -> None:
        self._pending_edge_start = pending
        self._refresh_pen()

    def _refresh_pen(self) -> None:
        pen = QPen(QColor("#202020"), 1.8)
        if self._selected:
            pen = QPen(QColor(DEFAULT_SELECTED_NODE_COLOR), 3.0)
        if self._pending_edge_start:
            pen = QPen(QColor(DEFAULT_PENDING_EDGE_COLOR), 3.0, Qt.PenStyle.DashLine)
        self.setPen(pen)

    def _center_label(self) -> None:
        br = self.label_item.boundingRect()
        self.label_item.setPos(-br.width() / 2.0, -NODE_RADIUS - br.height() - 3.0)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            pos = value if isinstance(value, QPointF) else self.pos()
            if self.node_id in self.graph.nodes:
                self.graph.nodes[self.node_id]["position"] = [float(pos.x()), float(pos.y())]
            scene = self.scene()
            if hasattr(scene, "update_edges_for_node"):
                scene.update_edges_for_node(self.node_id)
            if hasattr(scene, "main_window"):
                scene.main_window.on_node_position_changed(self)
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self._selected = bool(value)
            self._refresh_pen()
        return super().itemChange(change, value)
