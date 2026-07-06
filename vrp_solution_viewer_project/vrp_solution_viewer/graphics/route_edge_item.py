from __future__ import annotations

import math

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import QGraphicsPathItem, QStyleOptionGraphicsItem, QWidget


class RouteEdgeItem(QGraphicsPathItem):
    """Gezeichnete genutzte Kante mit optionalem seitlichem Versatz.

    The edge is defined by the source/target node centres, but the visible
    path is clipped to the circular node boundary.  This prevents arrows and
    edge endings from floating in front of, or disappearing inside, the node
    symbols.
    """

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
        arrow_scale: float = 1.0,
        source_trim: float = 0.0,
        target_trim: float = 0.0,
    ) -> None:
        super().__init__()
        self.source_center = QPointF(*source_pos)
        self.target_center = QPointF(*target_pos)
        self.offset = float(offset)
        self.show_arrow = show_arrow
        self.arrow_scale = max(0.01, float(arrow_scale))
        self.source_trim = max(0.0, float(source_trim))
        self.target_trim = max(0.0, float(target_trim))

        self.control_point = self._control_point()
        self.source_pos, self.target_pos = self._trimmed_endpoints()
        self.setPath(self._build_path())

        pen = QPen(QColor(color), max(0.01, float(width)))
        pen.setCosmetic(False)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        if dashed:
            pen.setStyle(Qt.PenStyle.DashLine)
        self.setPen(pen)
        self.setZValue(5)

    def _control_point(self) -> QPointF:
        p0 = self.source_center
        p1 = self.target_center
        dx = p1.x() - p0.x()
        dy = p1.y() - p0.y()
        length = math.hypot(dx, dy) or 1.0
        nx = -dy / length
        ny = dx / length
        mid = QPointF((p0.x() + p1.x()) / 2.0, (p0.y() + p1.y()) / 2.0)
        return QPointF(mid.x() + nx * self.offset, mid.y() + ny * self.offset)

    def _trimmed_endpoints(self) -> tuple[QPointF, QPointF]:
        """Return path endpoints clipped away from the node centres.

        For straight edges the clipping direction is the edge direction.  For
        curved/offset edges the clipping direction follows the local quadratic
        Bezier tangent at the corresponding endpoint.
        """
        total_length = math.hypot(
            self.target_center.x() - self.source_center.x(),
            self.target_center.y() - self.source_center.y(),
        )
        max_trim = max(0.0, 0.45 * total_length)
        source_trim = min(self.source_trim, max_trim)
        target_trim = min(self.target_trim, max_trim)

        source_neighbor = self.control_point if abs(self.offset) > 1e-9 else self.target_center
        target_neighbor = self.control_point if abs(self.offset) > 1e-9 else self.source_center

        source = self._move_from_towards(self.source_center, source_neighbor, source_trim)
        target = self._move_from_towards(self.target_center, target_neighbor, target_trim)
        return source, target

    @staticmethod
    def _move_from_towards(origin: QPointF, towards: QPointF, distance: float) -> QPointF:
        dx = towards.x() - origin.x()
        dy = towards.y() - origin.y()
        length = math.hypot(dx, dy)
        if length <= 1e-12 or distance <= 0.0:
            return QPointF(origin)
        factor = distance / length
        return QPointF(origin.x() + dx * factor, origin.y() + dy * factor)

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

        tip = self.target_pos
        if abs(self.offset) > 1e-9:
            tangent_start = self.control_point
        else:
            tangent_start = self.source_pos

        angle = math.atan2(tip.y() - tangent_start.y(), tip.x() - tangent_start.x())
        arrow_length = (12.0 + pen.widthF()) * self.arrow_scale
        arrow_width = (7.0 + 0.5 * pen.widthF()) * self.arrow_scale

        left = QPointF(
            tip.x() - arrow_length * math.cos(angle) + arrow_width * math.sin(angle),
            tip.y() - arrow_length * math.sin(angle) - arrow_width * math.cos(angle),
        )
        right = QPointF(
            tip.x() - arrow_length * math.cos(angle) - arrow_width * math.sin(angle),
            tip.y() - arrow_length * math.sin(angle) + arrow_width * math.cos(angle),
        )
        painter.drawPolygon(QPolygonF([tip, left, right]))
