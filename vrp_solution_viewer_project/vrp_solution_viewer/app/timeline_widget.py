from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt


class TimelineWidget(QWidget):
    time_changed = Signal(float)
    play_requested = Signal(bool)
    speed_changed = Signal(float)

    def __init__(self) -> None:
        super().__init__()
        self.start_time = 0.0
        self.end_time = 1.0
        self._updating = False

        self.play_button = QPushButton("▶")
        self.play_button.setCheckable(True)
        self.play_button.toggled.connect(self._on_play_toggled)

        self.time_label = QLabel("t = 0")
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 10000)
        self.slider.valueChanged.connect(self._on_slider_changed)

        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.01, 1_000_000.0)
        self.speed_spin.setDecimals(2)
        self.speed_spin.setSingleStep(1.0)
        self.speed_spin.setValue(10.0)
        self.speed_spin.setSuffix(" Zeit/s")
        self.speed_spin.valueChanged.connect(self.speed_changed.emit)

        top = QHBoxLayout()
        top.addWidget(self.play_button)
        top.addWidget(self.time_label)
        top.addStretch(1)
        top.addWidget(QLabel("Geschwindigkeit:"))
        top.addWidget(self.speed_spin)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.slider)

    def set_range(self, start: float, end: float) -> None:
        self.start_time = float(start)
        self.end_time = float(max(end, start + 1e-9))
        self.set_time(self.start_time)

    def set_time(self, time_value: float) -> None:
        time_value = max(self.start_time, min(self.end_time, float(time_value)))
        alpha = (time_value - self.start_time) / (self.end_time - self.start_time)
        self._updating = True
        self.slider.setValue(round(alpha * self.slider.maximum()))
        self.time_label.setText(f"t = {time_value:.3g}")
        self._updating = False

    def current_speed(self) -> float:
        return float(self.speed_spin.value())

    def set_playing(self, playing: bool) -> None:
        self.play_button.setChecked(playing)
        self.play_button.setText("❚❚" if playing else "▶")

    def _on_slider_changed(self, value: int) -> None:
        if self._updating:
            return
        alpha = value / self.slider.maximum()
        time_value = self.start_time + alpha * (self.end_time - self.start_time)
        self.time_label.setText(f"t = {time_value:.3g}")
        self.time_changed.emit(time_value)

    def _on_play_toggled(self, checked: bool) -> None:
        self.play_button.setText("❚❚" if checked else "▶")
        self.play_requested.emit(checked)
