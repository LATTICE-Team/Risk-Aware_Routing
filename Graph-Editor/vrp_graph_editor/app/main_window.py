"""Hauptfenster des VRP Graph Editors."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QAction, QActionGroup, QKeySequence, QTransform
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGraphicsView,
    QMainWindow,
    QMessageBox,
    QToolBar,
)

from vrp_graph_editor.app.editor_mode import EditorMode
from vrp_graph_editor.app.graph_scene import GraphScene
from vrp_graph_editor.app.graph_view import GraphView
from vrp_graph_editor.app.property_panel import AttributeDock
from vrp_graph_editor.graphics.edge_item import EdgeItem
from vrp_graph_editor.graphics.node_item import NodeItem
from vrp_graph_editor.io.graph_json import load_graph_json, save_graph_json
from vrp_graph_editor.model.graph_model import GraphModel


class MainWindow(QMainWindow):
    """Qt-Hauptfenster mit Toolbar, Szene, View und Attributeditor."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VRP Graph Editor — PySide6 + NetworkX")
        self.resize(1280, 820)

        self.model = GraphModel()
        self.current_path: Optional[Path] = None

        self.scene = GraphScene(self)
        self.view = GraphView(self.scene)
        self.setCentralWidget(self.view)

        self.attr_dock = AttributeDock(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.attr_dock)

        self._create_actions()
        self._create_menus_and_toolbar()
        self.scene.selectionChanged.connect(self.on_selection_changed)
        self.statusBar().showMessage("Bereit. Knotenmodus wählen oder Datei öffnen.")

    @property
    def graph(self):
        return self.model.graph

    def _create_actions(self) -> None:
        self.new_action = QAction("Neu", self)
        self.new_action.setShortcut(QKeySequence.StandardKey.New)
        self.new_action.triggered.connect(self.new_graph)

        self.open_action = QAction("Öffnen…", self)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.triggered.connect(self.open_graph)

        self.save_action = QAction("Speichern", self)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.triggered.connect(self.save_graph)

        self.save_as_action = QAction("Speichern unter…", self)
        self.save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.save_as_action.triggered.connect(self.save_graph_as)

        self.delete_action = QAction("Löschen", self)
        self.delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        self.delete_action.triggered.connect(self.delete_selected)

        self.mode_group = QActionGroup(self)
        self.mode_group.setExclusive(True)

        self.select_action = QAction("Auswahl", self, checkable=True)
        self.select_action.setChecked(True)
        self.select_action.triggered.connect(lambda: self.set_mode(EditorMode.SELECT))
        self.mode_group.addAction(self.select_action)

        self.add_node_action = QAction("Knoten", self, checkable=True)
        self.add_node_action.triggered.connect(lambda: self.set_mode(EditorMode.ADD_NODE))
        self.mode_group.addAction(self.add_node_action)

        self.add_edge_action = QAction("Kante", self, checkable=True)
        self.add_edge_action.triggered.connect(lambda: self.set_mode(EditorMode.ADD_EDGE))
        self.mode_group.addAction(self.add_edge_action)

        self.fit_action = QAction("Alles anzeigen", self)
        self.fit_action.triggered.connect(self.fit_graph_in_view)

    def _create_menus_and_toolbar(self) -> None:
        file_menu = self.menuBar().addMenu("Datei")
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_as_action)

        edit_menu = self.menuBar().addMenu("Bearbeiten")
        edit_menu.addAction(self.delete_action)

        view_menu = self.menuBar().addMenu("Ansicht")
        view_menu.addAction(self.fit_action)

        toolbar = QToolBar("Werkzeuge", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        toolbar.addAction(self.new_action)
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)
        toolbar.addSeparator()
        toolbar.addAction(self.select_action)
        toolbar.addAction(self.add_node_action)
        toolbar.addAction(self.add_edge_action)
        toolbar.addSeparator()
        toolbar.addAction(self.delete_action)
        toolbar.addAction(self.fit_action)

    def set_mode(self, mode: EditorMode) -> None:
        self.scene.set_mode(mode)
        if mode == EditorMode.SELECT:
            self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            message = "Auswahlmodus: Knoten ziehen, Objekte auswählen, Attribute rechts bearbeiten."
        elif mode == EditorMode.ADD_NODE:
            self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
            message = "Knotenmodus: Linksklick auf freie Fläche erzeugt einen Knoten."
        else:
            self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
            message = "Kantenmodus: Startknoten und Zielknoten anklicken."
        self.statusBar().showMessage(message, 4000)

    def add_node_at(self, pos: QPointF) -> NodeItem:
        node_id = self.model.add_node(pos)
        item = NodeItem(node_id, self.graph)
        self.scene.addItem(item)
        self.scene.node_items[node_id] = item
        item.setPos(pos)
        item.setSelected(True)
        self.statusBar().showMessage(f"Knoten {node_id} erzeugt.", 2000)
        return item

    def add_edge_between(self, u: str, v: str) -> Optional[EdgeItem]:
        try:
            self.model.add_edge(u, v)
        except ValueError as exc:
            QMessageBox.information(self, "Kante nicht erzeugt", str(exc))
            return None
        item = self._create_edge_item(u, v)
        item.setSelected(True)
        self.statusBar().showMessage(f"Kante {u} – {v} erzeugt.", 2000)
        return item

    def _create_edge_item(self, u: str, v: str) -> EdgeItem:
        item = EdgeItem(u, v, self.graph, self.scene)
        self.scene.addItem(item)
        self.scene.edge_items[self.scene.edge_key(u, v)] = item
        item.update_position()
        return item

    def delete_selected(self) -> None:
        selected = self.scene.selectedItems()
        if not selected:
            return

        nodes_to_delete: set[str] = set()
        edges_to_delete: set[tuple[str, str]] = set()
        for item in selected:
            graph_item = item
            while graph_item is not None and not isinstance(graph_item, (NodeItem, EdgeItem)):
                graph_item = graph_item.parentItem()
            if isinstance(graph_item, NodeItem):
                nodes_to_delete.add(graph_item.node_id)
            elif isinstance(graph_item, EdgeItem):
                edges_to_delete.add(self.scene.edge_key(graph_item.u, graph_item.v))

        for node_id in list(nodes_to_delete):
            for neighbor in list(self.graph.neighbors(node_id)) if node_id in self.graph else []:
                edges_to_delete.add(self.scene.edge_key(node_id, neighbor))

        for key in edges_to_delete:
            self._remove_edge_by_key(key)
        for node_id in nodes_to_delete:
            self._remove_node(node_id)

        self.attr_dock.show_empty()
        self.statusBar().showMessage("Auswahl gelöscht.", 2000)

    def _remove_edge_by_key(self, key: tuple[str, str]) -> None:
        item = self.scene.edge_items.pop(key, None)
        if item is not None:
            self.scene.removeItem(item)
        u, v = key
        self.model.remove_edge(u, v)

    def _remove_node(self, node_id: str) -> None:
        item = self.scene.node_items.pop(node_id, None)
        if item is not None:
            self.scene.removeItem(item)
        self.model.remove_node(node_id)

    def on_selection_changed(self) -> None:
        selected_graph_items = []
        seen = set()
        for item in self.scene.selectedItems():
            graph_item = item
            while graph_item is not None and not isinstance(graph_item, (NodeItem, EdgeItem)):
                graph_item = graph_item.parentItem()
            if graph_item is None:
                continue
            key = id(graph_item)
            if key not in seen:
                selected_graph_items.append(graph_item)
                seen.add(key)

        if len(selected_graph_items) != 1:
            self.attr_dock.show_empty()
            return

        item = selected_graph_items[0]
        if isinstance(item, NodeItem):
            self.attr_dock.show_node(item)
        elif isinstance(item, EdgeItem):
            self.attr_dock.show_edge(item)

    def on_node_position_changed(self, item: NodeItem) -> None:
        self.attr_dock.update_position_fields(item)

    def sync_positions_from_items(self) -> None:
        for node_id, item in self.scene.node_items.items():
            if node_id in self.graph.nodes:
                self.graph.nodes[node_id]["position"] = [float(item.pos().x()), float(item.pos().y())]

    def new_graph(self) -> None:
        self.model.clear()
        self.current_path = None
        self.rebuild_scene_from_graph()
        self.statusBar().showMessage("Neuer Graph angelegt.", 2000)

    def open_graph(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Graph öffnen", "", "JSON Graph (*.json);;Alle Dateien (*)")
        if not path:
            return
        try:
            loaded = load_graph_json(path)
            self.model.set_graph(loaded)
            self.current_path = Path(path)
            self.rebuild_scene_from_graph()
            self.statusBar().showMessage(f"Graph geladen: {path}", 3000)
        except Exception as exc:
            QMessageBox.critical(self, "Fehler beim Öffnen", str(exc))

    def save_graph(self) -> None:
        if self.current_path is None:
            self.save_graph_as()
            return
        self._write_graph(self.current_path)

    def save_graph_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Graph speichern", "graph.json", "JSON Graph (*.json);;Alle Dateien (*)")
        if not path:
            return
        self.current_path = Path(path)
        self._write_graph(self.current_path)

    def _write_graph(self, path: Path) -> None:
        try:
            self.sync_positions_from_items()
            save_graph_json(self.graph, path)
            self.statusBar().showMessage(f"Graph gespeichert: {path}", 3000)
        except Exception as exc:
            QMessageBox.critical(self, "Fehler beim Speichern", str(exc))

    def rebuild_scene_from_graph(self) -> None:
        self.scene.clear()
        self.scene.node_items.clear()
        self.scene.edge_items.clear()
        self.scene.reset_pending_edge()
        self.attr_dock.show_empty()

        self.model.normalize_loaded_graph()
        for node_id, attrs in self.graph.nodes(data=True):
            pos = attrs.get("position", [0.0, 0.0])
            item = NodeItem(str(node_id), self.graph)
            self.scene.addItem(item)
            self.scene.node_items[str(node_id)] = item
            item.setPos(QPointF(float(pos[0]), float(pos[1])))

        for u, v in self.graph.edges:
            self._create_edge_item(str(u), str(v))
        self.model.update_node_counter_from_graph()
        self.fit_graph_in_view()

    def fit_graph_in_view(self) -> None:
        if not self.scene.items():
            self.view.setTransform(QTransform())
            self.view.centerOn(0, 0)
            return
        rect = self.scene.itemsBoundingRect().adjusted(-80, -80, 80, 80)
        self.view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.delete_selected()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Escape:
            self.scene.reset_pending_edge()
            self.select_action.setChecked(True)
            self.set_mode(EditorMode.SELECT)
            event.accept()
            return
        super().keyPressEvent(event)


def run_app() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
