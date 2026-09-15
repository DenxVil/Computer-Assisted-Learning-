"""
Settings Screen
===============
App configuration: sound, fullscreen, animation speed, reset.
"""

from ..qt_compat import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QCheckBox, QSlider, QComboBox, QMessageBox,
    Signal, Qt,
)

from ..settings import settings
from .style import (
    BORDER, TEXT_SECONDARY, INSTITUTION_TEXT, INSTITUTION_LABEL_STYLE,
)


class SettingsScreen(QWidget):
    go_back = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(15)

        # Top bar
        top = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setProperty("secondary", True)
        back_btn.setMaximumWidth(100)
        back_btn.clicked.connect(self.go_back.emit)
        top.addWidget(back_btn)
        title = QLabel("⚙️ Settings")
        title.setProperty("heading", True)
        top.addWidget(title)
        top.addStretch()
        institution = QLabel(INSTITUTION_TEXT)
        institution.setStyleSheet(INSTITUTION_LABEL_STYLE)
        top.addWidget(institution)
        layout.addLayout(top)

        # ── Display Settings ──────────────────────────────
        display_group = QGroupBox("Display")
        display_layout = QVBoxLayout()

        self.fullscreen_cb = QCheckBox("Fullscreen Mode")
        self.fullscreen_cb.setChecked(settings.fullscreen)
        self.fullscreen_cb.toggled.connect(self.toggle_fullscreen)
        display_layout.addWidget(self.fullscreen_cb)

        display_group.setLayout(display_layout)
        layout.addWidget(display_group)

        # ── Sound Settings ────────────────────────────────
        sound_group = QGroupBox("Sound")
        sound_layout = QVBoxLayout()

        self.sound_cb = QCheckBox("Enable Sound Effects")
        self.sound_cb.setChecked(settings.sound_enabled)
        self.sound_cb.toggled.connect(self.toggle_sound)
        sound_layout.addWidget(self.sound_cb)

        sound_group.setLayout(sound_layout)
        layout.addWidget(sound_group)

        # ── Animation Speed ───────────────────────────────
        anim_group = QGroupBox("Animation Speed")
        anim_layout = QHBoxLayout()

        anim_layout.addWidget(QLabel("Slow"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(50, 200)
        self.speed_slider.setValue(int(settings.animation_speed * 100))
        self.speed_slider.setTickInterval(25)
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.valueChanged.connect(self.change_speed)
        anim_layout.addWidget(self.speed_slider)
        anim_layout.addWidget(QLabel("Fast"))

        self.speed_label = QLabel(f"{settings.animation_speed:.1f}×")
        anim_layout.addWidget(self.speed_label)

        anim_group.setLayout(anim_layout)
        layout.addWidget(anim_group)

        # ── Reset ─────────────────────────────────────────
        reset_group = QGroupBox("Reset")
        reset_layout = QVBoxLayout()

        reset_btn = QPushButton("Reset All Settings to Default")
        reset_btn.setProperty("danger", True)
        reset_btn.clicked.connect(self.reset_settings)
        reset_layout.addWidget(reset_btn)

        reset_group.setLayout(reset_layout)
        layout.addWidget(reset_group)

        # ── About ─────────────────────────────────────────
        about_group = QGroupBox("About")
        about_layout = QVBoxLayout()
        about_label = QLabel(
            "<b>Frog Rectus Abdominis CAL Simulator</b><br/>"
            "Version 1.0<br/><br/>"
            "Computer-Assisted Learning software for MBBS Phase II<br/>"
            "Pharmacology practical demonstration.<br/><br/>"
            "NMC CBME Compliant • 3Rs Replacement<br/><br/>"
            "<b>MAMC, New Delhi</b>"
        )
        about_label.setWordWrap(True)
        about_label.setStyleSheet(f"color: {TEXT_SECONDARY}; padding: 8px;")
        about_layout.addWidget(about_label)
        about_group.setLayout(about_layout)
        layout.addWidget(about_group)

        layout.addStretch()

    def toggle_fullscreen(self, checked):
        settings.fullscreen = checked
        window = self.window()
        if checked:
            window.showFullScreen()
        else:
            window.showNormal()

    def toggle_sound(self, checked):
        settings.sound_enabled = checked

    def change_speed(self, value):
        settings.animation_speed = value / 100.0
        self.speed_label.setText(f"{settings.animation_speed:.1f}×")

    def reset_settings(self):
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Reset all settings to default?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            settings.sound_enabled = True
            settings.fullscreen = False
            settings.animation_speed = 1.0
            self.sound_cb.setChecked(True)
            self.fullscreen_cb.setChecked(False)
            self.speed_slider.setValue(100)
            self.window().showNormal()
