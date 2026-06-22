import sys

from PySide6.QtWidgets import QApplication

from vrp_solution_viewer.app.main_window import MainWindow
from vrp_solution_viewer.demo.demo_instance import create_demo_solution


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1280, 820)
    window.set_solution(create_demo_solution())
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
