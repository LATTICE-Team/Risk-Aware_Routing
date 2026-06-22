from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QWheelEvent
from PySide6.QtWidgets import QGraphicsView


class SolutionView(QGraphicsView):
    def __init__(self) -> None:
        super().__init__()
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.TextAntialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)

    def wheelEvent(self, event: QWheelEvent) -> None:
        zoom_in_factor = 1.18
        zoom_out_factor = 1.0 / zoom_in_factor
        factor = zoom_in_factor if event.angleDelta().y() > 0 else zoom_out_factor
        self.scale(factor, factor)
