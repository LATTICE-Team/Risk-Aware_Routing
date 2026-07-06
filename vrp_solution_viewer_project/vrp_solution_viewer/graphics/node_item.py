from __future__ import annotations

from typing import Any

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPen
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsSimpleTextItem

from vrp_solution_viewer.config.defaults import NODE_RADIUS


class NodeItem(QGraphicsEllipseItem):
    def __init__(
        self,
        node_id: Any,
        position: tuple[float, float],
        label: str | None = None,
        *,
        radius: float | None = None,
        pen_width: float = 0.0,
        pen_color: str = "#222222",
        fill_color: str = "#f7f7f7",
        label_gap: float | None = None,
    ) -> None:
        r = NODE_RADIUS if radius is None else float(radius)
        super().__init__(-r, -r, 2 * r, 2 * r)
        self.node_id = node_id
        self.radius = r
        self.label_gap = max(0.0, 0.35 * r if label_gap is None else float(label_gap))
        self.setPos(QPointF(position[0], position[1]))
        self.setBrush(QBrush(QColor(fill_color)))
        if pen_width > 0.0:
            pen = QPen(QColor(pen_color), float(pen_width))
            pen.setCosmetic(False)
            self.setPen(pen)
        else:
            self.setPen(QPen(Qt.PenStyle.NoPen))
        self.setZValue(20)
        self.setToolTip(str(node_id))

        self.text = QGraphicsSimpleTextItem(label if label is not None else str(node_id), self)
        font = QFont("Arial", 9)
        font.setBold(True)
        self.text.setFont(font)
        self.text.setBrush(QBrush(QColor("#111111")))
        # Kein ItemIgnoresTransformations: Das Label bleibt in Szenenkoordinaten
        # eindeutig am statischen Knoten verankert.  Mit ItemIgnoresTransformations
        # konnte es nach fitInView/Zoom optisch vom Kreis wegdriften.
        self.text.setZValue(6)
        self.place_label_below()

    def label_size(self) -> tuple[float, float]:
        rect: QRectF = self.text.boundingRect()
        return rect.width(), rect.height()

    def set_label_offset(self, dx: float, dy: float) -> None:
        self.text.setPos(float(dx), float(dy))

    def label_scene_rect_for_offset(self, dx: float, dy: float) -> QRectF:
        rect = self.text.boundingRect()
        p = self.scenePos()
        return QRectF(p.x() + dx, p.y() + dy, rect.width(), rect.height())

    def circle_scene_rect(self, extra: float = 0.0) -> QRectF:
        p = self.scenePos()
        r = self.radius + max(0.0, float(extra))
        return QRectF(p.x() - r, p.y() - r, 2 * r, 2 * r)

    def place_label_below(self) -> None:
        w, _ = self.label_size()
        self.set_label_offset(-w / 2.0, self.radius + self.label_gap)
