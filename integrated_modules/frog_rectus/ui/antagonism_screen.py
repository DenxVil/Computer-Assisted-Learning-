"""
Antagonism Study Screen
=======================
Shows competitive antagonism: rightward shift of agonist DRC
in presence of increasing antagonist concentrations.
"""

import math

from ..qt_compat import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QGroupBox, QGridLayout, QDoubleSpinBox, QListWidget,
    Signal, Qt,
)

from ..simulation import (
    DRUG_LIBRARY, get_agonists, get_antagonists,
    generate_dose_series, dose_to_display
)
from .drc_screen import DRCPlotWidget
from .style import (
    PRIMARY, BORDER, TEXT_SECONDARY, INSTITUTION_TEXT,
    INSTITUTION_LABEL_STYLE,
)


# Colors for successive antagonist concentrations
SHIFT_COLORS = ["#1565C0", "#E65100", "#2E7D32", "#6A1B9A", "#C62828"]


class AntagonismScreen(QWidget):
    go_back = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.curves = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)

        # Top bar
        top = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setProperty("secondary", True)
        back_btn.setMaximumWidth(100)
        back_btn.clicked.connect(self.go_back.emit)
        top.addWidget(back_btn)
        title = QLabel("⚔️ Antagonism Study")
        title.setProperty("heading", True)
        top.addWidget(title)
        top.addStretch()
        institution = QLabel(INSTITUTION_TEXT)
        institution.setStyleSheet(INSTITUTION_LABEL_STYLE)
        top.addWidget(institution)
        layout.addLayout(top)

        # Content
        content = QHBoxLayout()

        # Controls
        ctrl = QVBoxLayout()

        # Drug selection
        sel_group = QGroupBox("Experiment Setup")
        sel_layout = QGridLayout()

        sel_layout.addWidget(QLabel("Agonist:"), 0, 0)
        self.agonist_combo = QComboBox()
        for name in get_agonists():
            self.agonist_combo.addItem(name)
        sel_layout.addWidget(self.agonist_combo, 0, 1)

        sel_layout.addWidget(QLabel("Antagonist:"), 1, 0)
        self.antag_combo = QComboBox()
        for name in get_antagonists():
            self.antag_combo.addItem(name)
        sel_layout.addWidget(self.antag_combo, 1, 1)

        sel_group.setLayout(sel_layout)
        ctrl.addWidget(sel_group)

        # Run buttons
        run_group = QGroupBox("Run Experiment")
        run_layout = QVBoxLayout()

        self.run_control_btn = QPushButton("1️⃣ Plot Control DRC\n(No Antagonist)")
        self.run_control_btn.setProperty("success", True)
        self.run_control_btn.setMinimumHeight(50)
        self.run_control_btn.clicked.connect(self.plot_control)
        run_layout.addWidget(self.run_control_btn)

        # Antagonist concentrations
        conc_layout = QHBoxLayout()
        conc_layout.addWidget(QLabel("Antag conc:"))
        self.conc_spin = QDoubleSpinBox()
        self.conc_spin.setRange(1, 100000)
        self.conc_spin.setValue(100)
        self.conc_spin.setSuffix(" nM")
        conc_layout.addWidget(self.conc_spin)
        run_layout.addLayout(conc_layout)

        self.add_shift_btn = QPushButton("2️⃣ Add Shifted DRC\n(With Antagonist)")
        self.add_shift_btn.setMinimumHeight(50)
        self.add_shift_btn.clicked.connect(self.add_shifted_curve)
        run_layout.addWidget(self.add_shift_btn)

        self.auto_btn = QPushButton("🔄 Auto: Show 3 Shifts")
        self.auto_btn.setProperty("secondary", True)
        self.auto_btn.clicked.connect(self.auto_demo)
        run_layout.addWidget(self.auto_btn)

        run_group.setLayout(run_layout)
        ctrl.addWidget(run_group)

        clear_btn = QPushButton("🗑 Clear All")
        clear_btn.setProperty("danger", True)
        clear_btn.clicked.connect(self.clear_all)
        ctrl.addWidget(clear_btn)

        # Info panel
        self.info_label = QLabel(
            "<b>Competitive Antagonism</b><br/><br/>"
            "A competitive antagonist shifts the agonist DRC to the "
            "<b>right</b> (parallel shift) without reducing E<sub>max</sub>.<br/><br/>"
            "The shift magnitude follows the <b>Schild equation</b>:<br/>"
            "DR = 1 + [B]/K<sub>B</sub>"
        )
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet(f"""
            background: #FFF3E0; border: 1px solid {BORDER};
            border-radius: 8px; padding: 12px; font-size: 12px;
        """)
        ctrl.addWidget(self.info_label)
        ctrl.addStretch()

        ctrl_widget = QWidget()
        ctrl_widget.setLayout(ctrl)
        ctrl_widget.setMaximumWidth(280)
        content.addWidget(ctrl_widget)

        # Plot
        self.plot = DRCPlotWidget()
        content.addWidget(self.plot, stretch=1)

        layout.addLayout(content)

    def _generate_drc(self, agonist_name, antag_name=None, antag_conc=0):
        agonist = DRUG_LIBRARY[agonist_name]
        antag_kb = DRUG_LIBRARY[antag_name].kb if antag_name else 1e-8
        doses = generate_dose_series(1e-8, 1e-3, points_per_log=3)
        points = []
        for d in doses:
            resp = agonist.response(d, antagonist_conc=antag_conc,
                                     antagonist_kb=antag_kb)
            points.append((math.log10(d), resp))
        return points

    def plot_control(self):
        self.curves.clear()
        ag = self.agonist_combo.currentText()
        points = self._generate_drc(ag)
        self.curves.append((f"{ag} (control)", SHIFT_COLORS[0], points))
        self.plot.set_curves(self.curves)

    def add_shifted_curve(self):
        ag = self.agonist_combo.currentText()
        antag = self.antag_combo.currentText()
        conc_nM = self.conc_spin.value()
        conc_M = conc_nM * 1e-9

        color_idx = min(len(self.curves), len(SHIFT_COLORS) - 1)
        points = self._generate_drc(ag, antag, conc_M)

        label = f"{ag} + {antag} {dose_to_display(conc_M)}"
        self.curves.append((label, SHIFT_COLORS[color_idx], points))
        self.plot.set_curves(self.curves)

        # Calculate dose ratio
        antag_drug = DRUG_LIBRARY[antag]
        dr = 1 + conc_M / antag_drug.kb
        self.info_label.setText(
            f"<b>Last addition:</b><br/>"
            f"{antag} at {dose_to_display(conc_M)}<br/><br/>"
            f"<b>Dose Ratio:</b> {dr:.1f}×<br/>"
            f"K<sub>B</sub> = {dose_to_display(antag_drug.kb)}<br/><br/>"
            f"The DRC shifts rightward by {dr:.1f}× "
            f"without change in E<sub>max</sub>."
        )

    def auto_demo(self):
        self.curves.clear()
        ag = self.agonist_combo.currentText()
        antag = self.antag_combo.currentText()

        # Control
        pts = self._generate_drc(ag)
        self.curves.append((f"{ag} (control)", SHIFT_COLORS[0], pts))

        # Three antagonist concentrations
        for i, conc_nM in enumerate([100, 500, 2000], 1):
            conc_M = conc_nM * 1e-9
            pts = self._generate_drc(ag, antag, conc_M)
            label = f"+ {antag} {dose_to_display(conc_M)}"
            self.curves.append((label, SHIFT_COLORS[i], pts))

        self.plot.set_curves(self.curves)
        self.info_label.setText(
            f"<b>Automatic demo complete</b><br/><br/>"
            f"Control DRC + 3 rightward shifts with increasing "
            f"{antag} concentrations.<br/><br/>"
            f"Note: E<sub>max</sub> remains unchanged (parallel shift) "
            f"— hallmark of competitive antagonism."
        )

    def clear_all(self):
        self.curves.clear()
        self.plot.clear()
