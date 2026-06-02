"""QGraphicsScene mit Editor-spezifischer Interaktionslogik."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtWidgets import QGraphicsScene

from vrp_graph_editor.app.editor_mode import EditorMode
from vrp_graph_editor.config.defaults import SCENE_RECT
from vrp_graph_editor.graphics.edge_item import EdgeItem
from vrp_graph_editor.graphics.node_item import NodeItem

if TYPE_CHECKING:
    from vrp_graph_editor.app.main_window import MainWindow


class GraphScene(QGraphicsScene):
    """Szene, die Knoten- und Kantenerzeugung behandelt."""

    def __init__(self, main_window: "MainWindow"):
        super().__init__()
        self.main_window = main_window
        self.mode = EditorMode.SELECT
        self.node_items: dict[str, NodeItem] = {}
        self.edge_items: dict[tuple[str, str], EdgeItem] = {}
        self.pending_edge_node: Optional[NodeItem] = None
        self.setSceneRect(QRectF(*SCENE_RECT))

    @staticmethod
    def edge_key(u: str, v: str) -> tuple[str, str]:
        return tuple(sorted((str(u), str(v))))

    def set_mode(self, mode: EditorMode) -> None:
        self.mode = mode
        self.reset_pending_edge()

    def reset_pending_edge(self) -> None:
        if self.pending_edge_node is not None:
            self.pending_edge_node.set_pending_edge_start(False)
        self.pending_edge_node = None

    def graph_item_at(self, pos: QPointF):
        for item in self.items(pos):
            current = item
            while current is not None:
                if isinstance(current, (NodeItem, EdgeItem)):
                    return current
                current = current.parentItem()
        return None

    def update_edges_for_node(self, node_id: str) -> None:
        for key, edge_item in list(self.edge_items.items()):
            if node_id in key:
                edge_item.update_position()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            graph_item = self.graph_item_at(event.scenePos())
            if self.mode == EditorMode.ADD_NODE and graph_item is None:
                self.main_window.add_node_at(event.scenePos())
                event.accept()
                return
            if self.mode == EditorMode.ADD_EDGE:
                node_item = graph_item if isinstance(graph_item, NodeItem) else None
                if node_item is not None:
                    self.handle_edge_click(node_item)
                    event.accept()
                    return
        super().mousePressEvent(event)

    def handle_edge_click(self, node_item: NodeItem) -> None:
        if self.pending_edge_node is None:
            self.pending_edge_node = node_item
            node_item.set_pending_edge_start(True)
            self.main_window.statusBar().showMessage(
                f"Startknoten {node_item.node_id} gewählt. Zielknoten anklicken.", 3000
            )
            return

        if node_item.node_id == self.pending_edge_node.node_id:
            self.reset_pending_edge()
            self.main_window.statusBar().showMessage("Kantenerzeugung abgebrochen.", 2000)
            return

        u = self.pending_edge_node.node_id
        v = node_item.node_id
        self.main_window.add_edge_between(u, v)
        self.reset_pending_edge()
