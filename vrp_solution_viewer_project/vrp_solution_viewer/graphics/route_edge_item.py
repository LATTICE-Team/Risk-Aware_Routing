from __future__ import annotations

import math

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import QGraphicsPathItem, QStyleOptionGraphicsItem, QWidget


class RouteEdgeItem(QGraphicsPathItem):
    """Gezeichnete genutzte Kante mit optionalem seitlichem Versatz."""

    def __init__(
        self,
        source_pos: tuple[float, float],
        target_pos: tuple[float, float],
        *,
        color: str,
        width: float,
        offset: float = 0.0,
        dashed: bool = False,
        show_arrow: bool = True,
    ) -> None:
        super().__init__()
        self.source_pos = QPointF(*source_pos)
        self.target_pos = QPointF(*target_pos)
        self.offset = offset
        self.show_arrow = show_arrow
        self.control_point = self._control_point()
        self.setPath(self._build_path())

        pen = QPen(QColor(color), width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        if dashed:
            pen.setStyle(Qt.PenStyle.DashLine)
        self.setPen(pen)
        self.setZValue(5)

    def _control_point(self) -> QPointF:
        p0 = self.source_pos
        p1 = self.target_pos
        dx = p1.x() - p0.x()
        dy = p1.y() - p0.y()
        length = math.hypot(dx, dy) or 1.0
        nx = -dy / length
        ny = dx / length
        mid = QPointF((p0.x() + p1.x()) / 2.0, (p0.y() + p1.y()) / 2.0)
        return QPointF(mid.x() + nx * self.offset, mid.y() + ny * self.offset)

    def _build_path(self) -> QPainterPath:
        path = QPainterPath(self.source_pos)
        if abs(self.offset) < 1e-9:
            path.lineTo(self.target_pos)
        else:
            path.quadTo(self.control_point, self.target_pos)
        return path

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        super().paint(painter, option, widget)
        if not self.show_arrow:
            return
        self._paint_arrow(painter)

    def _paint_arrow(self, painter: QPainter) -> None:
        pen = self.pen()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(pen.color())

        end = self.target_pos
        tangent_start = self.control_point if abs(self.offset) > 1e-9 else self.source_pos
        angle = math.atan2(end.y() - tangent_start.y(), end.x() - tangent_start.x())
        arrow_length = 12.0 + pen.widthF()
        arrow_width = 7.0 + 0.5 * pen.widthF()

        # Pfeilspitze leicht vor dem Zielpunkt platzieren, damit sie nicht exakt im Knotenmittelpunkt liegt.
        tip = QPointF(end.x() - math.cos(angle) * 18.0, end.y() - math.sin(angle) * 18.0)
        left = QPointF(
            tip.x() - arrow_length * math.cos(angle) + arrow_width * math.sin(angle),
            tip.y() - arrow_length * math.sin(angle) - arrow_width * math.cos(angle),
        )
        right = QPointF(
            tip.x() - arrow_length * math.cos(angle) - arrow_width * math.sin(angle),
            tip.y() - arrow_length * math.sin(angle) + arrow_width * math.cos(angle),
        )
        painter.drawPolygon(QPolygonF([tip, left, right]))
