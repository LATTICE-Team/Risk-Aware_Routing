from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsRectItem, QStyleOptionGraphicsItem, QWidget

from vrp_solution_viewer.config.defaults import CONTAINER_RADIUS, ROBOT_HALF_SIZE


def _scaled_pen(color: str, width: float) -> QPen:
    pen = QPen(QColor(color), max(0.01, float(width)))
    pen.setCosmetic(False)
    return pen


def _readable_text_color(background: str | QColor) -> str:
    """Return black or white depending on the perceived brightness.

    The threshold is based on relative luminance in sRGB.  It keeps the robot
    number readable when the full-size container symbol is drawn below it.
    """
    color = background if isinstance(background, QColor) else QColor(background)
    if not color.isValid():
        return "#000000"
    r = color.redF()
    g = color.greenF()
    b = color.blueF()
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "#ffffff" if luminance < 0.45 else "#000000"


class ContainerItem(QGraphicsEllipseItem):
    def __init__(
        self,
        container_id: str,
        color: str,
        *,
        radius: float | None = None,
        pen_width: float | None = None,
    ) -> None:
        r = CONTAINER_RADIUS if radius is None else float(radius)
        super().__init__(-r, -r, 2 * r, 2 * r)
        self.container_id = container_id
        self.radius = r
        self.color = color
        self.setBrush(QBrush(QColor(color)))
        outline_width = 0.10 * r if pen_width is None else float(pen_width)
        self.setPen(_scaled_pen("#111111", outline_width))
        self.setZValue(40)
        self.setToolTip(f"Container {container_id}")
        # Container werden über ihre Farben identifiziert.  Deshalb wird hier
        # bewusst kein ID-Label im Kreis gezeichnet.

    def set_position_tuple(self, pos: tuple[float, float]) -> None:
        self.setPos(QPointF(pos[0], pos[1]))


class RobotItem(QGraphicsRectItem):
    def __init__(
        self,
        robot_id: str,
        *,
        half_size: float | None = None,
        pen_width: float | None = None,
        load_radius: float | None = None,
        load_pen_width: float | None = None,
    ) -> None:
        s = ROBOT_HALF_SIZE if half_size is None else float(half_size)
        super().__init__(-s, -s, 2 * s, 2 * s)
        self.robot_id = robot_id
        self.half_size = s
        self._loaded_container_id: str | None = None
        self._loaded_container_color: str | None = None
        self.setBrush(QBrush(QColor("#ffffff")))
        outline_width = 0.12 * s if pen_width is None else float(pen_width)
        self.setPen(_scaled_pen("#000000", outline_width))
        self.setZValue(45)
        self.setToolTip(f"Roboter {robot_id}")

        # Vollgroßer Ladungsindikator.  Er wird direkt in paint() gezeichnet,
        # damit der Roboterindex danach sicher darüber gerendert wird.  Ein
        # separates Child-Item würde nach dem Parent gezeichnet und könnte das
        # Label wieder verdecken.
        r_load = CONTAINER_RADIUS if load_radius is None else float(load_radius)
        self.load_indicator_radius = r_load
        self.load_indicator_pen_width = 0.10 * r_load if load_pen_width is None else float(load_pen_width)
        self._loaded_container_brush = QBrush(QColor("#cccccc"))

        # Permanenter Roboterindex.  Das Label wird bewusst direkt im
        # paint()-Callback gezeichnet, nicht als separates QGraphicsTextItem.
        # Dadurch bleibt es exakt an den Roboter gebunden und kann nicht durch
        # View-/Parent-Transformationen scheinbar durch die Szene "fliegen".
        self._label_color = QColor("#000000")

    def set_loaded(self, loaded: bool) -> None:
        """Compatibility method for older scene code."""
        if loaded:
            self.set_loaded_container(self._loaded_container_id, self._loaded_container_color)
        else:
            self.set_loaded_container(None, None)

    def set_loaded_container(self, container_id: str | None, color: str | None = None) -> None:
        self._loaded_container_id = None if container_id is None else str(container_id)
        self._loaded_container_color = color
        loaded = self._loaded_container_id is not None
        self.setBrush(QBrush(QColor("#eeeeee" if loaded else "#ffffff")))
        if loaded:
            container_color = color or "#cccccc"
            self._loaded_container_brush = QBrush(QColor(container_color))
            self._label_color = QColor(_readable_text_color(container_color))
            self.setToolTip(f"Roboter {self.robot_id}, beladen mit Container {self._loaded_container_id}")
        else:
            self._label_color = QColor("#000000")
            self.setToolTip(f"Roboter {self.robot_id}")
        self.update()


    def boundingRect(self) -> QRectF:
        extent = max(self.half_size, self.load_indicator_radius) + max(
            self.pen().widthF(), self.load_indicator_pen_width, 0.0
        )
        return QRectF(-extent, -extent, 2 * extent, 2 * extent)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        """Draw robot body, optional load, and centered robot id.

        Both the load indicator and label are drawn in item-local coordinates.
        This keeps them rigidly attached to the robot during animation and
        prevents drifting text items caused by mixed QGraphics transformations.
        """
        super().paint(painter, option, widget)
        painter.save()
        if self._loaded_container_id is not None:
            r = self.load_indicator_radius
            painter.setPen(_scaled_pen("#111111", self.load_indicator_pen_width))
            painter.setBrush(self._loaded_container_brush)
            painter.drawEllipse(QRectF(-r, -r, 2 * r, 2 * r))
        painter.setPen(QPen(self._label_color))
        font = QFont("Arial")
        font.setBold(True)
        # Conservative point-size range: readable without dominating small
        # automatically scaled symbols.
        font.setPointSizeF(max(5.0, min(14.0, 1.25 * self.half_size)))
        painter.setFont(font)
        label_rect = QRectF(
            -self.load_indicator_radius,
            -self.load_indicator_radius,
            2 * self.load_indicator_radius,
            2 * self.load_indicator_radius,
        ) if self._loaded_container_id is not None else self.rect()
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, str(self.robot_id))
        painter.restore()

    def set_position_tuple(self, pos: tuple[float, float]) -> None:
        self.setPos(QPointF(pos[0], pos[1]))
