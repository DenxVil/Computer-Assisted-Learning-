"""Frog Rectus Abdominis CAL source application entry point."""

from pathlib import Path
import sys

# Keep this file directly runnable for teachers who use the source folder,
# while also making it importable by the combined frozen application.
if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from integrated_modules.frog_rectus.qt_compat import (
    Qt, QApplication, QMainWindow, QStackedWidget, QMessageBox,
    QScrollArea, app_exec, ensure_application_font,
)
from integrated_modules.frog_rectus.ui.style import MAIN_STYLESHEET
from integrated_modules.frog_rectus.ui.home_screen import HomeScreen
from integrated_modules.frog_rectus.ui.theory_viewer import TheoryViewer
from integrated_modules.frog_rectus.ui.virtual_lab import VirtualLabScreen
from integrated_modules.frog_rectus.ui.drc_screen import DRCScreen
from integrated_modules.frog_rectus.ui.antagonism_screen import AntagonismScreen
from integrated_modules.frog_rectus.ui.unknown_drug import UnknownDrugScreen
from integrated_modules.frog_rectus.ui.settings_screen import SettingsScreen


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "Frog Rectus Abdominis CAL Simulator — MAMC, New Delhi"
        )
        # 720 by 480 keeps the application reachable on small Windows laptops.
        # Every page is inside a scroll area, so no button is lost below the edge.
        self.setMinimumSize(720, 480)
        self.resize(1280, 780)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.page_scroll_areas = []

        self.home = HomeScreen()
        self.home.navigate.connect(self.navigate_to)
        self._add_scrollable_page(self.home)

        self.theory = TheoryViewer()
        self.theory.go_back.connect(lambda: self.stack.setCurrentIndex(0))
        self._add_scrollable_page(self.theory)

        self.virtual_lab = VirtualLabScreen()
        self.virtual_lab.go_back.connect(lambda: self.stack.setCurrentIndex(0))
        self._add_scrollable_page(self.virtual_lab)

        self.drc = DRCScreen()
        self.drc.go_back.connect(lambda: self.stack.setCurrentIndex(0))
        self._add_scrollable_page(self.drc)

        self.antagonism = AntagonismScreen()
        self.antagonism.go_back.connect(lambda: self.stack.setCurrentIndex(0))
        self._add_scrollable_page(self.antagonism)

        self.unknown = UnknownDrugScreen()
        self.unknown.go_back.connect(lambda: self.stack.setCurrentIndex(0))
        self._add_scrollable_page(self.unknown)

        self.settings_screen = SettingsScreen()
        self.settings_screen.go_back.connect(lambda: self.stack.setCurrentIndex(0))
        self._add_scrollable_page(self.settings_screen)

        self.stack.setCurrentIndex(0)
        self.statusBar().showMessage(
            "Ready | Frog Rectus Abdominis CAL source edition | MAMC, New Delhi"
        )

    def _add_scrollable_page(self, page):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setWidget(page)
        self.page_scroll_areas.append(scroll)
        self.stack.addWidget(scroll)

    def navigate_to(self, module):
        pages = {
            "theory": 1,
            "virtual_lab": 2,
            "drc": 3,
            "antagonism": 4,
            "unknown": 5,
            "settings": 6,
            "exit": -1,
        }
        index = pages.get(module, 0)
        if index == -1:
            self.close()
        else:
            self.stack.setCurrentIndex(index)

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "Exit application", "Exit the simulator?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


def main(argv=None):
    app = QApplication(sys.argv if argv is None else argv)
    ensure_application_font()
    app.setApplicationName("Frog Rectus Abdominis CAL")
    app.setOrganizationName("Department of Pharmacology, MAMC")
    app.setStyleSheet(MAIN_STYLESHEET)
    window = MainWindow()
    window.showMaximized()
    return app_exec(app)


if __name__ == "__main__":
    sys.exit(main())
