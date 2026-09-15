"""Responsive coloured organ bath illustration."""

import math

from ..qt_compat import (
    Qt, QRectF, QPointF, QTimer, QWidget, QPainter, QPen, QBrush,
    QColor, QLinearGradient, QFont, QPainterPath,
)
from .style import PRIMARY, PRIMARY_DARK, BATH_BLUE


class OrganBathWidget(QWidget):
    """Scaled visual of the frog rectus preparation and recording lever."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(240, 320)
        self.contraction_pct = 0.0
        self.is_drug_present = False
        self.drug_color = QColor("#1565C0")
        self.drug_name = ""
        self.show_bubbles = True
        self._bubble_phase = 0.0
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._animate)
        self._anim_timer.start(70)

    def set_contraction(self, pct):
        self.contraction_pct = max(0.0, min(100.0, float(pct)))
        self.update()

    def set_drug(self, name, color):
        self.is_drug_present = True
        self.drug_name = str(name)
        self.drug_color = QColor(color)
        self.update()

    def clear_drug(self):
        self.is_drug_present = False
        self.drug_name = ""
        self.update()

    def _animate(self):
        self._bubble_phase += 0.18
        if self.show_bubbles:
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = float(self.width()), float(self.height())

        bg = QLinearGradient(0, 0, 0, h)
        bg.setColorAt(0, QColor("#F8FCFF"))
        bg.setColorAt(1, QColor("#E9F4FB"))
        painter.setPen(QPen(QColor("#C7DAEA"), 1))
        painter.setBrush(QBrush(bg))
        painter.drawRoundedRect(QRectF(2, 2, w - 4, h - 4), 14, 14)

        painter.setPen(QColor(PRIMARY_DARK))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(QRectF(12, 8, w - 24, 24), Qt.AlignCenter,
                         "Isolated Frog Rectus Preparation")

        bath_x = max(30.0, w * 0.16)
        bath_y = max(92.0, h * 0.22)
        bath_w = max(150.0, w * 0.68)
        bath_w = min(bath_w, w - bath_x - 24.0)
        bath_h = max(150.0, h * 0.55)
        bath_h = min(bath_h, h - bath_y - 64.0)

        # Transducer and lever remain clear even on a compact laptop layout.
        muscle_x = bath_x + bath_w * 0.50
        lever_y = bath_y - 30
        lever_half = bath_w * 0.30
        tilt = self.contraction_pct * 0.07
        painter.setPen(QPen(QColor("#37474F"), 3))
        painter.drawLine(QPointF(muscle_x - lever_half, lever_y + tilt),
                         QPointF(muscle_x + lever_half, lever_y - tilt))
        painter.setPen(QPen(QColor("#263238"), 2))
        painter.setBrush(QBrush(QColor("#B0BEC5")))
        painter.drawEllipse(QPointF(muscle_x, lever_y), 5, 5)
        painter.setPen(QPen(QColor("#D32F2F"), 2))
        painter.drawLine(QPointF(muscle_x + lever_half, lever_y - tilt),
                         QPointF(muscle_x + lever_half, lever_y - tilt + 10))

        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(QColor("#455A64"))
        painter.drawText(QRectF(6, lever_y - 10, bath_x - 8, 20),
                         Qt.AlignRight | Qt.AlignVCenter, "Lever")

        # Glass chamber.
        glass = QLinearGradient(bath_x, bath_y, bath_x + bath_w, bath_y)
        glass.setColorAt(0, QColor(164, 211, 244, 125))
        glass.setColorAt(0.5, QColor(243, 250, 255, 75))
        glass.setColorAt(1, QColor(120, 190, 235, 130))
        bath_path = QPainterPath()
        bath_path.moveTo(bath_x, bath_y)
        bath_path.lineTo(bath_x - 4, bath_y + bath_h)
        bath_path.lineTo(bath_x + bath_w + 4, bath_y + bath_h)
        bath_path.lineTo(bath_x + bath_w, bath_y)
        painter.setPen(QPen(QColor("#4F89B8"), 2.4))
        painter.setBrush(QBrush(glass))
        painter.drawPath(bath_path)

        solution_top = bath_y + bath_h * 0.12
        solution_color = QColor(BATH_BLUE)
        if self.is_drug_present:
            solution_color = QColor(self.drug_color)
        solution = QLinearGradient(0, solution_top, 0, bath_y + bath_h)
        solution.setColorAt(0, QColor(solution_color.red(), solution_color.green(),
                                     solution_color.blue(), 52))
        solution.setColorAt(1, QColor(solution_color.red(), solution_color.green(),
                                     solution_color.blue(), 115))
        solution_path = QPainterPath()
        solution_path.moveTo(bath_x + 2, solution_top)
        steps = max(20, int(bath_w))
        for i in range(steps + 1):
            x = bath_x + 2 + i * (bath_w - 4) / float(steps)
            y = solution_top + math.sin(i / 5.0 + self._bubble_phase) * 1.8
            solution_path.lineTo(x, y)
        solution_path.lineTo(bath_x + bath_w + 2, bath_y + bath_h - 2)
        solution_path.lineTo(bath_x - 2, bath_y + bath_h - 2)
        solution_path.closeSubpath()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(solution))
        painter.drawPath(solution_path)

        # Aeration tube and bubbles.
        air_x = bath_x + bath_w * 0.80
        painter.setPen(QPen(QColor("#78909C"), 2))
        painter.drawLine(QPointF(air_x, bath_y - 8),
                         QPointF(air_x, bath_y + bath_h - 12))
        if self.show_bubbles:
            painter.setPen(QPen(QColor(80, 160, 220, 145), 1))
            painter.setBrush(QBrush(QColor(220, 245, 255, 95)))
            for i in range(7):
                travel = (self._bubble_phase * 22 + i * 31) % max(40, bath_h * 0.76)
                by = bath_y + bath_h - 18 - travel
                bx = air_x + math.sin(i + self._bubble_phase) * 7
                radius = 2 + i % 3
                painter.drawEllipse(QPointF(bx, by), radius, radius)

        # Tissue with visible fibres.
        hook_y = bath_y + bath_h - 17
        muscle_top = bath_y + bath_h * 0.20 + self.contraction_pct * 0.12
        muscle_bottom = hook_y - 10 - self.contraction_pct * 0.12
        muscle_width = max(15.0, min(23.0, bath_w * 0.09))
        tissue_gradient = QLinearGradient(muscle_x - muscle_width / 2,
                                         muscle_top,
                                         muscle_x + muscle_width / 2,
                                         muscle_top)
        tissue_gradient.setColorAt(0, QColor("#F48FB1"))
        tissue_gradient.setColorAt(0.5, QColor("#EF5350"))
        tissue_gradient.setColorAt(1, QColor("#F8BBD0"))
        tissue_rect = QRectF(muscle_x - muscle_width / 2, muscle_top,
                             muscle_width, max(12, muscle_bottom - muscle_top))
        painter.setPen(QPen(QColor("#C62828"), 1.4))
        painter.setBrush(QBrush(tissue_gradient))
        painter.drawRoundedRect(tissue_rect, 7, 7)
        painter.setPen(QPen(QColor(170, 55, 70, 105), 0.7))
        y = muscle_top + 6
        while y < muscle_bottom - 4:
            painter.drawLine(QPointF(muscle_x - muscle_width / 2 + 3, y),
                             QPointF(muscle_x + muscle_width / 2 - 3, y))
            y += 7

        # Threads and hooks.
        painter.setPen(QPen(QColor("#455A64"), 1.5, Qt.DashLine))
        painter.drawLine(QPointF(muscle_x, muscle_top),
                         QPointF(muscle_x, lever_y + 5))
        painter.setPen(QPen(QColor("#607D8B"), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawArc(QRectF(muscle_x - 7, hook_y - 7, 14, 14),
                        0, 180 * 16)
        painter.drawLine(QPointF(muscle_x, muscle_bottom),
                         QPointF(muscle_x, hook_y - 5))

        # Labels use a light panel so they stay readable over solution colour.
        label_x = min(w - 112, muscle_x + muscle_width / 2 + 9)
        painter.setPen(QColor("#263238"))
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        painter.drawText(QRectF(label_x, muscle_top + 8, 105, 34),
                         Qt.AlignLeft | Qt.TextWordWrap,
                         "Frog rectus\nabdominis")

        painter.setPen(QColor(PRIMARY_DARK))
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(QRectF(bath_x, bath_y + bath_h + 7, bath_w, 20),
                         Qt.AlignCenter, "Frog Ringer solution with aeration")

        status_y = bath_y - 59
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        if self.contraction_pct > 0.5:
            painter.setPen(QColor("#B71C1C"))
            painter.drawText(QRectF(bath_x, status_y, bath_w, 20),
                             Qt.AlignCenter,
                             f"Response {self.contraction_pct:.1f} %")
        if self.is_drug_present:
            painter.setPen(self.drug_color)
            painter.drawText(QRectF(8, h - 31, w - 16, 22), Qt.AlignCenter,
                             f"In bath: {self.drug_name}")

        painter.end()
