from __future__ import annotations

from PySide6.QtCore import QPointF
from PySide6.QtGui import QBrush, QColor, QFont, QPen
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsSimpleTextItem

from vrp_solution_viewer.config.defaults import CONTAINER_RADIUS, ROBOT_HALF_SIZE


class ContainerItem(QGraphicsEllipseItem):
    def __init__(self, container_id: str, color: str) -> None:
        r = CONTAINER_RADIUS
        super().__init__(-r, -r, 2 * r, 2 * r)
        self.container_id = container_id
        self.setBrush(QBrush(QColor(color)))
        self.setPen(QPen(QColor("#111111"), 1.0))
        self.setZValue(40)
        self.setToolTip(f"Container {container_id}")
        self.label = _label(container_id, self)

    def set_position_tuple(self, pos: tuple[float, float]) -> None:
        self.setPos(QPointF(pos[0], pos[1]))


class RobotItem(QGraphicsRectItem):
    def __init__(self, robot_id: str) -> None:
        s = ROBOT_HALF_SIZE
        super().__init__(-s, -s, 2 * s, 2 * s)
        self.robot_id = robot_id
        self.setBrush(QBrush(QColor("#ffffff")))
        self.setPen(QPen(QColor("#000000"), 1.8))
        self.setZValue(45)
        self.setToolTip(f"Roboter {robot_id}")
        self.label = _label(robot_id, self)

    def set_loaded(self, loaded: bool) -> None:
        self.setBrush(QBrush(QColor("#dddddd" if loaded else "#ffffff")))

    def set_position_tuple(self, pos: tuple[float, float]) -> None:
        self.setPos(QPointF(pos[0], pos[1]))


def _label(text: str, parent) -> QGraphicsSimpleTextItem:
    label = QGraphicsSimpleTextItem(text, parent)
    label.setFont(QFont("Arial", 8))
    rect = label.boundingRect()
    label.setPos(-rect.width() / 2.0, -rect.height() / 2.0)
    label.setFlag(QGraphicsSimpleTextItem.GraphicsItemFlag.ItemIgnoresTransformations, True)
    return label
