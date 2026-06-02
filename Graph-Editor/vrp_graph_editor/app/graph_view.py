"""QGraphicsView mit Zoom und Panning."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGraphicsView

from vrp_graph_editor.app.graph_scene import GraphScene


class GraphView(QGraphicsView):
    """View-Komponente: Zoom per Mausrad, Pan per Mittel-/Rechtsklick."""

    def __init__(self, scene: GraphScene):
        super().__init__(scene)
        self._panning = False
        self._last_pan_pos = None
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)
        self.setMouseTracking(True)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta == 0:
            event.ignore()
            return
        zoom_in_factor = 1.15
        factor = zoom_in_factor if delta > 0 else 1.0 / zoom_in_factor
        current_scale = self.transform().m11()
        next_scale = current_scale * factor
        if 0.05 <= next_scale <= 20.0:
            self.scale(factor, factor)
        event.accept()

    def mousePressEvent(self, event):
        if event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.RightButton):
            self._panning = True
            self._last_pan_pos = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning and self._last_pan_pos is not None:
            current = event.position().toPoint()
            delta = current - self._last_pan_pos
            self._last_pan_pos = current
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.RightButton) and self._panning:
            self._panning = False
            self._last_pan_pos = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)
