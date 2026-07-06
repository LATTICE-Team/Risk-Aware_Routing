from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QElapsedTimer, Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from vrp_solution_viewer.app.solution_scene import SolutionScene
from vrp_solution_viewer.app.solution_view import SolutionView
from vrp_solution_viewer.app.timeline_widget import TimelineWidget
from vrp_solution_viewer.config.defaults import (
    ANIMATION_INTERVAL_MS,
    SYMBOL_USER_SCALE_DEFAULT,
    SYMBOL_USER_SCALE_MAX,
    SYMBOL_USER_SCALE_MIN,
    SYMBOL_USER_SCALE_STEP,
)
from vrp_solution_viewer.demo.demo_instance import create_demo_solution
from vrp_solution_viewer.io.solution_json import load_solution_json, save_solution_json
from vrp_solution_viewer.model.solution_data import SolutionData


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("VRP Solution Viewer")
        self.solution: SolutionData | None = None
        self.current_time = 0.0

        self.scene = SolutionScene()
        self.view = SolutionView()
        self.view.setScene(self.scene)

        self.timeline = TimelineWidget()
        self.timeline.time_changed.connect(self.set_time)
        self.timeline.play_requested.connect(self.set_playing)

        self.timer = QTimer(self)
        self.timer.setInterval(ANIMATION_INTERVAL_MS)
        self.timer.timeout.connect(self._animation_tick)
        self.elapsed = QElapsedTimer()

        self._build_ui()
        self._build_menu()

    def set_solution(self, solution: SolutionData) -> None:
        try:
            solution.validate()
        except Exception as exc:  # noqa: BLE001 - GUI-Fehlerdialog
            QMessageBox.critical(self, "Ungültige Lösung", str(exc))
            return

        self.solution = solution
        animation_start = self._animation_start_time(solution)
        animation_end = self._animation_end_time(solution, animation_start)

        self._set_symbol_scale_control(SYMBOL_USER_SCALE_DEFAULT)
        self.scene.set_user_symbol_scale(SYMBOL_USER_SCALE_DEFAULT)
        self.scene.set_solution(solution, initial_time=animation_start)
        self.timeline.set_range(animation_start, animation_end)
        self.set_time(animation_start)
        self._update_info()
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def set_time(self, time_value: float) -> None:
        self.current_time = float(time_value)
        self.scene.set_time(self.current_time)
        self.timeline.set_time(self.current_time)

    def set_playing(self, playing: bool) -> None:
        if playing:
            self.elapsed.restart()
            self.timer.start()
        else:
            self.timer.stop()
        self.timeline.set_playing(playing)

    def _animation_tick(self) -> None:
        if self.solution is None:
            self.set_playing(False)
            return
        dt_real = self.elapsed.restart() / 1000.0
        next_time = self.current_time + dt_real * self.timeline.current_speed()
        if next_time >= self.solution.end_time:
            next_time = self.solution.end_time
            self.set_playing(False)
        self.set_time(next_time)

    def _build_ui(self) -> None:
        side_panel = QWidget()
        side_layout = QVBoxLayout(side_panel)

        load_button = QPushButton("Lösung laden …")
        load_button.clicked.connect(self._open_solution)
        demo_button = QPushButton("Demo laden")
        demo_button.clicked.connect(lambda: self.set_solution(create_demo_solution()))
        save_button = QPushButton("Aktuelle Lösung speichern …")
        save_button.clicked.connect(self._save_solution)

        self.show_robot_routes_box = QCheckBox("Roboter-Routen anzeigen")
        self.show_robot_routes_box.toggled.connect(self._toggle_robot_routes)

        self.symbol_scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.symbol_scale_slider.setMinimum(int(SYMBOL_USER_SCALE_MIN * 100))
        self.symbol_scale_slider.setMaximum(int(SYMBOL_USER_SCALE_MAX * 100))
        self.symbol_scale_slider.setSingleStep(int(SYMBOL_USER_SCALE_STEP * 100))
        self.symbol_scale_slider.setPageStep(25)
        self.symbol_scale_slider.setValue(int(SYMBOL_USER_SCALE_DEFAULT * 100))
        self.symbol_scale_slider.valueChanged.connect(self._symbol_scale_slider_changed)

        self.symbol_scale_box = QDoubleSpinBox()
        self.symbol_scale_box.setRange(SYMBOL_USER_SCALE_MIN, SYMBOL_USER_SCALE_MAX)
        self.symbol_scale_box.setSingleStep(SYMBOL_USER_SCALE_STEP)
        self.symbol_scale_box.setDecimals(2)
        self.symbol_scale_box.setSuffix("×")
        self.symbol_scale_box.setValue(SYMBOL_USER_SCALE_DEFAULT)
        self.symbol_scale_box.valueChanged.connect(self._symbol_scale_box_changed)

        reset_symbol_scale_button = QPushButton("Auto")
        reset_symbol_scale_button.setToolTip(
            "Setzt die manuelle Symbolskalierung auf 1× zurück. "
            "Die automatische Skalierung aus der Graphgröße bleibt aktiv."
        )
        reset_symbol_scale_button.clicked.connect(self._reset_symbol_scale)

        symbol_scale_layout = QHBoxLayout()
        symbol_scale_layout.addWidget(self.symbol_scale_slider, 1)
        symbol_scale_layout.addWidget(self.symbol_scale_box)
        symbol_scale_layout.addWidget(reset_symbol_scale_button)

        self.info_label = QLabel("Keine Lösung geladen")
        self.info_label.setWordWrap(True)

        form = QFormLayout()
        form.addRow(load_button)
        form.addRow(demo_button)
        form.addRow(save_button)
        form.addRow(self.show_robot_routes_box)
        form.addRow(QLabel("Symbolgröße:"), symbol_scale_layout)
        form.addRow(QLabel("Instanz:"), self.info_label)

        side_layout.addLayout(form)
        side_layout.addStretch(1)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(self.view, 1)
        left_layout.addWidget(self.timeline)

        splitter = QSplitter()
        splitter.addWidget(left)
        splitter.addWidget(side_panel)
        splitter.setSizes([1000, 320])
        self.setCentralWidget(splitter)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("Datei")
        open_action = file_menu.addAction("Lösung laden …")
        open_action.triggered.connect(self._open_solution)
        save_action = file_menu.addAction("Lösung speichern …")
        save_action.triggered.connect(self._save_solution)
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Beenden")
        exit_action.triggered.connect(self.close)

        view_menu = self.menuBar().addMenu("Ansicht")
        fit_action = view_menu.addAction("Alles einpassen")
        fit_action.triggered.connect(lambda: self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio))
        reset_symbols_action = view_menu.addAction("Symbolgröße automatisch")
        reset_symbols_action.triggered.connect(self._reset_symbol_scale)

    def _open_solution(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "VRP-Lösung laden",
            str(Path.home()),
            "JSON-Dateien (*.json);;Alle Dateien (*)",
        )
        if not path:
            return
        try:
            self.set_solution(load_solution_json(path))
        except Exception as exc:  # noqa: BLE001 - GUI-Fehlerdialog
            QMessageBox.critical(self, "Fehler beim Laden", str(exc))

    def _save_solution(self) -> None:
        if self.solution is None:
            QMessageBox.information(self, "Keine Lösung", "Es ist keine Lösung geladen.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "VRP-Lösung speichern",
            str(Path.home() / "solution.json"),
            "JSON-Dateien (*.json);;Alle Dateien (*)",
        )
        if not path:
            return
        try:
            save_solution_json(self.solution, path)
        except Exception as exc:  # noqa: BLE001 - GUI-Fehlerdialog
            QMessageBox.critical(self, "Fehler beim Speichern", str(exc))

    def _toggle_robot_routes(self, checked: bool) -> None:
        self.scene.show_robot_routes = checked
        self.scene.redraw()
        self.scene.set_time(self.current_time)

    def _symbol_scale_slider_changed(self, value: int) -> None:
        scale = value / 100.0
        self._set_symbol_scale_control(scale)
        self._apply_symbol_scale(scale)

    def _symbol_scale_box_changed(self, value: float) -> None:
        self._set_symbol_scale_control(float(value))
        self._apply_symbol_scale(float(value))

    def _reset_symbol_scale(self) -> None:
        self._set_symbol_scale_control(SYMBOL_USER_SCALE_DEFAULT)
        self._apply_symbol_scale(SYMBOL_USER_SCALE_DEFAULT)

    def _set_symbol_scale_control(self, scale: float) -> None:
        self.symbol_scale_slider.blockSignals(True)
        self.symbol_scale_box.blockSignals(True)
        self.symbol_scale_slider.setValue(int(round(scale * 100)))
        self.symbol_scale_box.setValue(scale)
        self.symbol_scale_slider.blockSignals(False)
        self.symbol_scale_box.blockSignals(False)

    def _apply_symbol_scale(self, scale: float) -> None:
        self.scene.set_user_symbol_scale(scale)
        self.scene.set_time(self.current_time)
        self._update_info()

    def _update_info(self) -> None:
        if self.solution is None:
            self.info_label.setText("Keine Lösung geladen")
            return
        animation_start = self._animation_start_time(self.solution)
        animation_end = self._animation_end_time(self.solution, animation_start)
        self.info_label.setText(
            f"Knoten: {self.solution.graph.number_of_nodes()}\n"
            f"Container: {len(self.solution.containers)}\n"
            f"Roboter: {len(self.solution.robots)}\n"
            f"Containerbewegungen: {len(self.solution.container_movements)}\n"
            f"Roboterbewegungen: {len(self.solution.robot_movements)}\n"
            f"Animationszeitraum: [{animation_start:g}, {animation_end:g}]\n"
            f"Erste Bewegung: t = {self.solution.start_time:g}\n"
            f"Auto-Skalierung: {self.scene.auto_symbol_scale:.3g}×\n"
            f"Manuelle Symbolgröße: {self.scene.user_symbol_scale:.2f}×"
        )

    @staticmethod
    def _animation_start_time(solution: SolutionData) -> float:
        """The viewer timeline always starts at t=0.

        Solver/model event times are intentionally not modified.  If the first
        movement starts later than zero, agents remain at their first event's
        source node until that movement begins.
        """

        return 0.0

    @staticmethod
    def _animation_end_time(solution: SolutionData, animation_start: float) -> float:
        return max(solution.end_time, animation_start + 1e-9)
