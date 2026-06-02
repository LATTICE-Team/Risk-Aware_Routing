"""Rechtes Dock-Panel zur Bearbeitung von Knoten- und Kantenattributen."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QDockWidget,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from vrp_graph_editor.config.defaults import DEFAULT_CLASSIFICATIONS, DEFAULT_EDGE_COLOR, DEFAULT_NODE_COLOR
from vrp_graph_editor.graphics.edge_item import EdgeItem
from vrp_graph_editor.graphics.node_item import NodeItem
from vrp_graph_editor.model.attributes import normalize_time_window, valid_color

if TYPE_CHECKING:
    from vrp_graph_editor.app.main_window import MainWindow


class AttributeDock(QDockWidget):
    """Attributeditor für jeweils genau ein selektiertes Graphobjekt."""

    def __init__(self, main_window: "MainWindow"):
        super().__init__("Attribute", main_window)
        self.main_window = main_window
        self.current_item = None
        self._updating = False

        self.stack = QStackedWidget()
        self.empty_page = QWidget()
        empty_layout = QVBoxLayout(self.empty_page)
        empty_layout.addWidget(QLabel("Kein einzelnes Objekt ausgewählt."))
        empty_layout.addStretch(1)

        self.node_page = QWidget()
        self.edge_page = QWidget()
        self._build_node_page()
        self._build_edge_page()

        self.stack.addWidget(self.empty_page)
        self.stack.addWidget(self.node_page)
        self.stack.addWidget(self.edge_page)
        self.setWidget(self.stack)
        self.setMinimumWidth(310)

    def _build_node_page(self) -> None:
        layout = QVBoxLayout(self.node_page)
        form = QFormLayout()

        self.node_id_label = QLabel("–")
        self.node_label_edit = QLineEdit()
        self.node_demand_spin = self._double_spin(minimum=0.0, maximum=1_000_000.0, decimals=3)
        self.node_tw_start_spin = self._double_spin(minimum=-1_000_000.0, maximum=1_000_000.0, decimals=3)
        self.node_tw_end_spin = self._double_spin(minimum=-1_000_000.0, maximum=1_000_000.0, decimals=3)
        self.node_color_edit = QLineEdit(DEFAULT_NODE_COLOR)
        self.node_class_combo = QComboBox()
        self.node_class_combo.setEditable(True)
        self.node_class_combo.addItems(DEFAULT_CLASSIFICATIONS)
        self.node_x_spin = self._double_spin(minimum=-1_000_000.0, maximum=1_000_000.0, decimals=3)
        self.node_y_spin = self._double_spin(minimum=-1_000_000.0, maximum=1_000_000.0, decimals=3)

        node_color_row = QHBoxLayout()
        node_color_row.addWidget(self.node_color_edit)
        color_btn = QPushButton("…")
        color_btn.setFixedWidth(34)
        color_btn.clicked.connect(lambda: self._pick_color(self.node_color_edit))
        node_color_row.addWidget(color_btn)
        node_color_widget = QWidget()
        node_color_widget.setLayout(node_color_row)

        form.addRow("Interne ID", self.node_id_label)
        form.addRow("Label", self.node_label_edit)
        form.addRow("Bedarf", self.node_demand_spin)
        form.addRow("TW Start", self.node_tw_start_spin)
        form.addRow("TW Ende", self.node_tw_end_spin)
        form.addRow("Color", node_color_widget)
        form.addRow("Klassifizierung", self.node_class_combo)
        form.addRow("Position x", self.node_x_spin)
        form.addRow("Position y", self.node_y_spin)
        layout.addLayout(form)

        apply_btn = QPushButton("Knotenattribute übernehmen")
        apply_btn.clicked.connect(self.apply_node_attributes)
        layout.addWidget(apply_btn)
        layout.addStretch(1)

    def _build_edge_page(self) -> None:
        layout = QVBoxLayout(self.edge_page)
        form = QFormLayout()

        self.edge_id_label = QLabel("–")
        self.edge_label_edit = QLineEdit()
        self.edge_weight_spin = self._double_spin(minimum=-1_000_000.0, maximum=1_000_000.0, decimals=3)
        self.edge_color_edit = QLineEdit(DEFAULT_EDGE_COLOR)
        self.edge_width_spin = self._double_spin(minimum=0.1, maximum=100.0, decimals=2)

        edge_color_row = QHBoxLayout()
        edge_color_row.addWidget(self.edge_color_edit)
        color_btn = QPushButton("…")
        color_btn.setFixedWidth(34)
        color_btn.clicked.connect(lambda: self._pick_color(self.edge_color_edit))
        edge_color_row.addWidget(color_btn)
        edge_color_widget = QWidget()
        edge_color_widget.setLayout(edge_color_row)

        form.addRow("Kante", self.edge_id_label)
        form.addRow("Label", self.edge_label_edit)
        form.addRow("Weight", self.edge_weight_spin)
        form.addRow("Color", edge_color_widget)
        form.addRow("Width", self.edge_width_spin)
        layout.addLayout(form)

        apply_btn = QPushButton("Kantenattribute übernehmen")
        apply_btn.clicked.connect(self.apply_edge_attributes)
        layout.addWidget(apply_btn)
        layout.addStretch(1)

    @staticmethod
    def _double_spin(minimum: float, maximum: float, decimals: int) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setDecimals(decimals)
        spin.setSingleStep(1.0)
        return spin

    def _pick_color(self, line_edit: QLineEdit) -> None:
        color = QColorDialog.getColor(QColor(line_edit.text()), self, "Farbe wählen")
        if color.isValid():
            line_edit.setText(color.name())

    def show_empty(self) -> None:
        self.current_item = None
        self.stack.setCurrentWidget(self.empty_page)

    def show_node(self, item: NodeItem) -> None:
        self._updating = True
        self.current_item = item
        attrs = item.graph.nodes[item.node_id]
        tw = normalize_time_window(attrs.get("time_window", [0.0, 0.0]))
        pos = item.pos()

        self.node_id_label.setText(item.node_id)
        self.node_label_edit.setText(str(attrs.get("label", item.node_id)))
        self.node_demand_spin.setValue(float(attrs.get("demand", 0.0)))
        self.node_tw_start_spin.setValue(tw[0])
        self.node_tw_end_spin.setValue(tw[1])
        self.node_color_edit.setText(valid_color(str(attrs.get("color", DEFAULT_NODE_COLOR)), DEFAULT_NODE_COLOR))
        classification = str(attrs.get("classification", DEFAULT_CLASSIFICATIONS[0]))
        if self.node_class_combo.findText(classification) < 0:
            self.node_class_combo.addItem(classification)
        self.node_class_combo.setCurrentText(classification)
        self.node_x_spin.setValue(float(pos.x()))
        self.node_y_spin.setValue(float(pos.y()))
        self.stack.setCurrentWidget(self.node_page)
        self._updating = False

    def show_edge(self, item: EdgeItem) -> None:
        self._updating = True
        self.current_item = item
        attrs = item.attrs()
        self.edge_id_label.setText(f"{item.u} – {item.v}")
        self.edge_label_edit.setText(str(attrs.get("label", f"{item.u}–{item.v}")))
        self.edge_weight_spin.setValue(float(attrs.get("weight", 0.0)))
        self.edge_color_edit.setText(valid_color(str(attrs.get("color", DEFAULT_EDGE_COLOR)), DEFAULT_EDGE_COLOR))
        self.edge_width_spin.setValue(float(attrs.get("width", 2.0)))
        self.stack.setCurrentWidget(self.edge_page)
        self._updating = False

    def update_position_fields(self, item: NodeItem) -> None:
        if self._updating or self.current_item is not item:
            return
        self.node_x_spin.blockSignals(True)
        self.node_y_spin.blockSignals(True)
        self.node_x_spin.setValue(float(item.pos().x()))
        self.node_y_spin.setValue(float(item.pos().y()))
        self.node_x_spin.blockSignals(False)
        self.node_y_spin.blockSignals(False)

    def apply_node_attributes(self) -> None:
        item = self.current_item
        if not isinstance(item, NodeItem):
            return
        attrs = item.graph.nodes[item.node_id]
        pos = QPointF(self.node_x_spin.value(), self.node_y_spin.value())
        attrs.update(
            {
                "label": self.node_label_edit.text().strip() or item.node_id,
                "demand": float(self.node_demand_spin.value()),
                "time_window": [float(self.node_tw_start_spin.value()), float(self.node_tw_end_spin.value())],
                "color": valid_color(self.node_color_edit.text(), DEFAULT_NODE_COLOR),
                "classification": self.node_class_combo.currentText().strip() or DEFAULT_CLASSIFICATIONS[0],
                "position": [float(pos.x()), float(pos.y())],
            }
        )
        item.setPos(pos)
        item.update_from_graph()
        self.main_window.statusBar().showMessage("Knotenattribute übernommen.", 2000)

    def apply_edge_attributes(self) -> None:
        item = self.current_item
        if not isinstance(item, EdgeItem):
            return
        attrs = item.attrs()
        attrs.update(
            {
                "label": self.edge_label_edit.text().strip(),
                "weight": float(self.edge_weight_spin.value()),
                "color": valid_color(self.edge_color_edit.text(), DEFAULT_EDGE_COLOR),
                "width": float(self.edge_width_spin.value()),
            }
        )
        item.update_from_graph()
        self.main_window.statusBar().showMessage("Kantenattribute übernommen.", 2000)
