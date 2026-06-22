from __future__ import annotations

from typing import Any

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPen
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsSimpleTextItem

from vrp_solution_viewer.config.defaults import NODE_RADIUS


class NodeItem(QGraphicsEllipseItem):
    def __init__(self, node_id: Any, position: tuple[float, float], label: str | None = None) -> None:
        r = NODE_RADIUS
        super().__init__(-r, -r, 2 * r, 2 * r)
        self.node_id = node_id
        self.setPos(QPointF(position[0], position[1]))
        self.setBrush(QBrush(QColor("#f7f7f7")))
        self.setPen(QPen(QColor("#222222"), 1.2))
        self.setZValue(20)
        self.setToolTip(str(node_id))

        self.text = QGraphicsSimpleTextItem(label if label is not None else str(node_id), self)
        self.text.setFont(QFont("Arial", 9))
        self._center_text()

    def _center_text(self) -> None:
        rect: QRectF = self.text.boundingRect()
        self.text.setPos(-rect.width() / 2.0, -rect.height() / 2.0)
        self.text.setFlag(QGraphicsSimpleTextItem.GraphicsItemFlag.ItemIgnoresTransformations, True)
