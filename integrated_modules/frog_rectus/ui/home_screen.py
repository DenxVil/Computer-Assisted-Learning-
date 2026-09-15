"""Responsive home screen with clear text based navigation."""

from ..qt_compat import (
    Signal, Qt, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGridLayout, QFrame,
)
from .style import (
    HOME_BUTTON_STYLE, TITLE_LABEL_STYLE, SUBTITLE_LABEL_STYLE,
    PRIMARY, PRIMARY_DARK, TEXT_SECONDARY,
)


class HomeScreen(QWidget):
    navigate = Signal(str)

    BUTTONS = [
        ("theory", "Theory and Practical", "Simple notes and four guided experiment settings"),
        ("virtual_lab", "Virtual Experiment Lab", "Organ bath setup with retained kymograph recording"),
        ("drc", "Dose Response Curve", "ACh and agonist curves on a semi log scale"),
        ("antagonism", "Antagonism Study", "d Tubocurarine competitive blockade demonstration"),
        ("unknown", "Unknown ACh Bioassay", "Interpolation, three point and four point methods"),
        ("settings", "Settings", "Display and experiment preferences"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._column_count = 0
        self.buttons = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 20)
        layout.setSpacing(12)

        banner = QFrame()
        banner.setStyleSheet(
            "QFrame { background: #FFFFFF; border: 1px solid #C7D7E8; "
            "border-radius: 14px; }"
        )
        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(20, 14, 20, 14)
        banner_layout.setSpacing(5)

        title = QLabel("Frog Rectus Abdominis Simulator")
        title.setStyleSheet(TITLE_LABEL_STYLE)
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        banner_layout.addWidget(title)

        subtitle = QLabel("Computer Assisted Learning in Experimental Pharmacology")
        subtitle.setStyleSheet(SUBTITLE_LABEL_STYLE)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        banner_layout.addWidget(subtitle)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(f"color: {PRIMARY}; margin: 5px 25px;")
        banner_layout.addWidget(separator)

        institution = QLabel("MAMC, New Delhi")
        institution.setStyleSheet(f"font-size: 10px; color: {TEXT_SECONDARY};")
        institution.setAlignment(Qt.AlignCenter)
        institution.setWordWrap(True)
        banner_layout.addWidget(institution)

        note = QLabel(
            "Educational simulation  |  Retained recording  |  Bioassay practice"
        )
        note.setAlignment(Qt.AlignCenter)
        note.setWordWrap(True)
        note.setStyleSheet(
            "background: #E8F5E9; color: #1B5E20; border-radius: 6px; "
            "padding: 5px; font-size: 11px; font-weight: 600;"
        )
        banner_layout.addWidget(note)
        layout.addWidget(banner)

        section = QLabel("Select an experiment or learning section")
        section.setProperty("heading", True)
        section.setWordWrap(True)
        layout.addWidget(section)

        self.grid = QGridLayout()
        self.grid.setSpacing(11)
        for button_id, button_title, description in self.BUTTONS:
            button = QPushButton(f"{button_title}\n{description}")
            button.setStyleSheet(HOME_BUTTON_STYLE)
            button.setCursor(Qt.PointingHandCursor)
            button.setToolTip(description)
            button.clicked.connect(
                lambda checked=False, selected=button_id: self.navigate.emit(selected)
            )
            self.buttons.append(button)
        layout.addLayout(self.grid)
        self._relayout_buttons(2)

        layout.addStretch()
        footer = QHBoxLayout()
        footer.addStretch()
        exit_button = QPushButton("Exit application")
        exit_button.setProperty("danger", True)
        exit_button.setMinimumWidth(165)
        exit_button.clicked.connect(lambda: self.navigate.emit("exit"))
        footer.addWidget(exit_button)
        footer.addStretch()
        layout.addLayout(footer)

        version = QLabel(
            "Source edition 2.0  |  MBBS experimental pharmacology teaching tool  |  MAMC"
        )
        version.setStyleSheet(f"font-size: 10px; color: {TEXT_SECONDARY};")
        version.setAlignment(Qt.AlignCenter)
        version.setWordWrap(True)
        layout.addWidget(version)

    def _relayout_buttons(self, columns):
        if columns == self._column_count:
            return
        for button in self.buttons:
            self.grid.removeWidget(button)
        for index, button in enumerate(self.buttons):
            self.grid.addWidget(button, index // columns, index % columns)
        for column in range(columns):
            self.grid.setColumnStretch(column, 1)
        self._column_count = columns

    def resizeEvent(self, event):
        self._relayout_buttons(1 if self.width() < 820 else 2)
        super().resizeEvent(event)
