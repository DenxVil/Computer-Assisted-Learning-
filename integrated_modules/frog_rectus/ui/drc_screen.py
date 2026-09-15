"""
Dose-Response Curve Module
==========================
Automatic DRC plotting with log-dose scale.
Compares drugs on same axes.
"""

import math

from ..qt_compat import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QGroupBox, QGridLayout, QCheckBox, Signal, Qt,
    QRectF, QPointF, QPainter, QPen, QBrush, QColor, QFont,
    QPainterPath, QLinearGradient,
)

from ..simulation import (
    DRUG_LIBRARY, get_agonists, generate_dose_series, dose_to_display
)
from .style import (
    PRIMARY, GRAPH_BG, BORDER, TEXT_SECONDARY,
    INSTITUTION_TEXT, INSTITUTION_LABEL_STYLE,
)


class DRCPlotWidget(QWidget):
    """Custom widget that draws dose-response curves."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 350)
        self.curves = []  # list of (name, color, [(log_dose, response), ...])
        self.show_ec50 = True
        self.show_emax = True

    def set_curves(self, curves):
        self.curves = curves
        self.update()

    def clear(self):
        self.curves = []
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        ml, mr, mt, mb = 65, 30, 30, 50
        pw, ph = w - ml - mr, h - mt - mb

        # Background
        p.fillRect(0, 0, w, h, QColor(GRAPH_BG))
        p.setPen(QPen(QColor(BORDER), 1))
        p.setBrush(QBrush(QColor(255, 255, 255)))
        p.drawRect(QRectF(ml, mt, pw, ph))

        # ── Grid ──────────────────────────────────────────
        p.setPen(QPen(QColor(230, 235, 240), 0.5, Qt.DotLine))
        for i in range(1, 5):
            gy = mt + ph * i / 5
            p.drawLine(QPointF(ml, gy), QPointF(ml + pw, gy))
        for i in range(1, 6):
            gx = ml + pw * i / 6
            p.drawLine(QPointF(gx, mt), QPointF(gx, mt + ph))

        # ── Axes Labels ───────────────────────────────────
        p.setPen(QColor(TEXT_SECONDARY))
        font = QFont("Segoe UI", 8)
        p.setFont(font)

        # Y-axis: 0-100%
        for i in range(6):
            val = i * 20
            gy = mt + ph * (1 - val / 100)
            p.drawText(QRectF(0, gy - 8, ml - 8, 16),
                      Qt.AlignRight | Qt.AlignVCenter, f"{val}%")

        # X-axis: log concentrations
        log_min, log_max = -8, -3
        for log_val in range(log_min, log_max + 1):
            frac = (log_val - log_min) / (log_max - log_min)
            gx = ml + pw * frac
            label = f"10^{log_val}"
            if log_val == -6:
                label = "1µM"
            elif log_val == -3:
                label = "1mM"
            elif log_val == -8:
                label = "10nM"
            p.drawText(QRectF(gx - 25, mt + ph + 5, 50, 16),
                      Qt.AlignCenter, label)

        # Axis titles
        p.setPen(QColor(PRIMARY))
        font_title = QFont("Segoe UI", 10, QFont.Bold)
        p.setFont(font_title)
        p.drawText(QRectF(ml, mt - 25, pw, 20), Qt.AlignCenter,
                  "Dose-Response Curve (Semi-Log Plot)")

        p.setPen(QColor(TEXT_SECONDARY))
        font_axis = QFont("Segoe UI", 9)
        p.setFont(font_axis)
        p.drawText(QRectF(ml, h - 20, pw, 18), Qt.AlignCenter,
                  "Log [Drug Concentration] (M)")

        p.save()
        p.translate(14, mt + ph / 2)
        p.rotate(-90)
        p.drawText(QRectF(-50, 0, 100, 15), Qt.AlignCenter, "Response (%)")
        p.restore()

        # ── Curves ────────────────────────────────────────
        if not self.curves:
            p.setPen(QColor(180, 180, 180))
            font_msg = QFont("Segoe UI", 12)
            p.setFont(font_msg)
            p.drawText(QRectF(ml, mt, pw, ph), Qt.AlignCenter,
                      "Select a drug and click\n'Plot DRC' to begin")
            p.end()
            return

        legend_y = mt + 10
        for curve_name, color, data_points in self.curves:
            curve_color = QColor(color)
            p.setPen(QPen(curve_color, 2.5))
            p.setBrush(Qt.NoBrush)

            path = QPainterPath()
            first = True
            ec50_x = ec50_y = None

            for log_dose, response in data_points:
                frac_x = (log_dose - log_min) / (log_max - log_min)
                x = ml + pw * frac_x
                y = mt + ph * (1 - response / 100)

                if first:
                    path.moveTo(x, y)
                    first = False
                else:
                    path.lineTo(x, y)

                # Find EC50 point
                if self.show_ec50 and abs(response - 50) < 3:
                    ec50_x, ec50_y = x, y

            p.drawPath(path)

            # Data points
            p.setBrush(QBrush(curve_color))
            for log_dose, response in data_points:
                frac_x = (log_dose - log_min) / (log_max - log_min)
                x = ml + pw * frac_x
                y = mt + ph * (1 - response / 100)
                p.drawEllipse(QPointF(x, y), 3, 3)

            # EC50 marker
            if ec50_x and self.show_ec50:
                p.setPen(QPen(curve_color, 1, Qt.DashLine))
                p.drawLine(QPointF(ec50_x, mt + ph), QPointF(ec50_x, ec50_y))
                p.drawLine(QPointF(ml, ec50_y), QPointF(ec50_x, ec50_y))
                p.setPen(curve_color)
                font_ec = QFont("Segoe UI", 7)
                p.setFont(font_ec)
                p.drawText(QPointF(ec50_x + 5, ec50_y - 5), "EC₅₀")

            # Emax marker
            if self.show_emax and data_points:
                max_resp = max(r for _, r in data_points)
                emax_y = mt + ph * (1 - max_resp / 100)
                p.setPen(QPen(curve_color, 1, Qt.DotLine))
                p.drawLine(QPointF(ml, emax_y), QPointF(ml + pw, emax_y))

            # Legend
            p.setPen(QPen(curve_color, 2))
            p.drawLine(QPointF(ml + pw - 140, legend_y),
                      QPointF(ml + pw - 120, legend_y))
            p.setPen(curve_color)
            font_leg = QFont("Segoe UI", 9, QFont.Bold)
            p.setFont(font_leg)
            p.drawText(QPointF(ml + pw - 115, legend_y + 4), curve_name)
            legend_y += 20

        p.end()


class DRCScreen(QWidget):
    go_back = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.plotted_drugs = []
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
        title = QLabel("📈 Dose-Response Curve")
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
        ctrl.setSpacing(10)

        sel_group = QGroupBox("Drug Selection")
        sel_layout = QGridLayout()

        sel_layout.addWidget(QLabel("Drug:"), 0, 0)
        self.drug_combo = QComboBox()
        for name in get_agonists():
            self.drug_combo.addItem(name)
        sel_layout.addWidget(self.drug_combo, 0, 1)

        self.plot_btn = QPushButton("📊 Plot DRC")
        self.plot_btn.setProperty("success", True)
        self.plot_btn.clicked.connect(self.plot_drc)
        sel_layout.addWidget(self.plot_btn, 1, 0, 1, 2)

        self.add_btn = QPushButton("➕ Add Another Drug")
        self.add_btn.clicked.connect(self.add_drug_curve)
        sel_layout.addWidget(self.add_btn, 2, 0, 1, 2)

        sel_group.setLayout(sel_layout)
        ctrl.addWidget(sel_group)

        # Options
        opt_group = QGroupBox("Display Options")
        opt_layout = QVBoxLayout()

        self.ec50_cb = QCheckBox("Show EC₅₀ lines")
        self.ec50_cb.setChecked(True)
        self.ec50_cb.toggled.connect(self.update_options)
        opt_layout.addWidget(self.ec50_cb)

        self.emax_cb = QCheckBox("Show Emax lines")
        self.emax_cb.setChecked(True)
        self.emax_cb.toggled.connect(self.update_options)
        opt_layout.addWidget(self.emax_cb)

        opt_group.setLayout(opt_layout)
        ctrl.addWidget(opt_group)

        clear_btn = QPushButton("🗑 Clear All Curves")
        clear_btn.setProperty("danger", True)
        clear_btn.clicked.connect(self.clear_all)
        ctrl.addWidget(clear_btn)

        # Info
        self.info_label = QLabel("")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet(f"""
            background: #EBF5FB; border: 1px solid {BORDER};
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

    def _generate_curve_data(self, drug_name):
        drug = DRUG_LIBRARY[drug_name]
        doses = generate_dose_series(1e-8, 1e-3, points_per_log=3)
        points = []
        for d in doses:
            resp = drug.response(d)
            log_d = math.log10(d)
            points.append((log_d, resp))
        return points

    def plot_drc(self):
        self.plotted_drugs.clear()
        self.add_drug_curve()

    def add_drug_curve(self):
        name = self.drug_combo.currentText()
        drug = DRUG_LIBRARY[name]

        # Check if already plotted
        for existing_name, _, _ in self.plotted_drugs:
            if existing_name == name:
                return

        points = self._generate_curve_data(name)
        self.plotted_drugs.append((name, drug.color, points))
        self.plot.set_curves(self.plotted_drugs)

        # Update info
        ec50_str = dose_to_display(drug.ec50)
        self.info_label.setText(
            f"<b>{name}</b><br/>"
            f"EC₅₀: {ec50_str}<br/>"
            f"Emax: {drug.emax:.0f}%<br/>"
            f"Hill coefficient: {drug.hill_n:.1f}<br/>"
            f"Type: {drug.drug_type.title()}"
        )

    def update_options(self):
        self.plot.show_ec50 = self.ec50_cb.isChecked()
        self.plot.show_emax = self.emax_cb.isChecked()
        self.plot.update()

    def clear_all(self):
        self.plotted_drugs.clear()
        self.plot.clear()
        self.info_label.setText("")
