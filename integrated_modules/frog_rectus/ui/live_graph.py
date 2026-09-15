"""Retained, horizontally scrollable kymograph and annotated PNG export."""

from ..qt_compat import (
    Signal, Qt, QRectF, QPointF, QTimer, QSize,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox,
    QScrollArea, QFileDialog, QMessageBox,
    QPainter, QPen, QBrush, QColor, QLinearGradient, QFont,
    QPainterPath, QImage, ensure_application_font,
)
from .style import PRIMARY, GRAPH_BG, BORDER, TEXT_SECONDARY


class KymographCanvas(QWidget):
    """Canvas whose width grows with the complete retained recording."""

    pixels_per_point = 2.2
    y_min = 0.0
    y_max = 55.0
    baseline = 5.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.trace_data = [self.baseline] * 50
        self.markers = []
        self.setMinimumSize(760, 320)

    def sizeHint(self):
        return QSize(self.content_width(), 390)

    def content_width(self):
        return max(760, int(100 + len(self.trace_data) * self.pixels_per_point))

    def refresh_size(self):
        self.setMinimumWidth(self.content_width())
        self.updateGeometry()
        self.update()

    def add_point(self, value):
        self.trace_data.append(float(value))
        self.refresh_size()

    def add_points(self, values):
        self.trace_data.extend(float(v) for v in values)
        self.refresh_size()

    def add_marker(self, label, color="#1565C0"):
        self.markers.append({
            "index": max(0, len(self.trace_data) - 1),
            "label": str(label),
            "color": str(color),
        })
        self.update()

    def clear(self):
        self.trace_data = [self.baseline] * 50
        self.markers = []
        self.refresh_size()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.draw_graph(painter, self.width(), self.height(), full_record=True)
        painter.end()

    def draw_graph(self, painter, width, height, full_record=True,
                   export_scale=None):
        margin_l, margin_r = 76, 24
        margin_t, margin_b = 38, 70
        plot_w = max(10, width - margin_l - margin_r)
        plot_h = max(10, height - margin_t - margin_b)

        painter.fillRect(0, 0, width, height, QColor(GRAPH_BG))
        plot_rect = QRectF(margin_l, margin_t, plot_w, plot_h)
        painter.setPen(QPen(QColor(BORDER), 1))
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawRect(plot_rect)

        painter.setPen(QPen(QColor("#DCE6F0"), 1, Qt.DotLine))
        for i in range(1, 11):
            gy = margin_t + plot_h * i / 11.0
            painter.drawLine(QPointF(margin_l, gy),
                             QPointF(margin_l + plot_w, gy))

        count = max(1, len(self.trace_data) - 1)
        if export_scale is None:
            x_scale = self.pixels_per_point
        else:
            x_scale = export_scale
        for i in range(0, len(self.trace_data), 100):
            gx = margin_l + i * x_scale
            if gx <= margin_l + plot_w:
                painter.drawLine(QPointF(gx, margin_t),
                                 QPointF(gx, margin_t + plot_h))

        axis_font = QFont("Segoe UI", 8)
        painter.setFont(axis_font)
        painter.setPen(QColor(TEXT_SECONDARY))
        for i in range(12):
            value = self.y_max - i * 5.0
            gy = margin_t + plot_h * i / 11.0
            painter.drawText(QRectF(0, gy - 9, margin_l - 8, 18),
                             Qt.AlignRight | Qt.AlignVCenter,
                             f"{value:.0f}")

        painter.save()
        painter.translate(15, margin_t + plot_h / 2.0)
        painter.rotate(-90)
        painter.drawText(QRectF(-110, 0, 220, 18), Qt.AlignCenter,
                         "Kymograph height (mm)")
        painter.restore()

        painter.drawText(QRectF(margin_l, height - 19, plot_w, 16),
                         Qt.AlignCenter, "Recording time (scroll sideways to review)")
        painter.setPen(QColor(PRIMARY))
        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        painter.drawText(QRectF(margin_l, 7, plot_w, 24), Qt.AlignCenter,
                         "Frog Rectus Abdominis Kymograph")

        if len(self.trace_data) > 1:
            path = QPainterPath()
            for i, value in enumerate(self.trace_data):
                x = margin_l + i * x_scale
                if x > margin_l + plot_w:
                    break
                clipped = max(self.y_min, min(self.y_max, value))
                y = margin_t + plot_h * (1.0 - clipped /
                                         (self.y_max - self.y_min))
                if i == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)

            fill = QPainterPath(path)
            last_i = min(len(self.trace_data) - 1,
                         int(plot_w / max(0.001, x_scale)))
            last_x = margin_l + last_i * x_scale
            fill.lineTo(last_x, margin_t + plot_h)
            fill.lineTo(margin_l, margin_t + plot_h)
            fill.closeSubpath()
            gradient = QLinearGradient(0, margin_t, 0, margin_t + plot_h)
            gradient.setColorAt(0, QColor(211, 47, 47, 42))
            gradient.setColorAt(1, QColor(211, 47, 47, 5))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawPath(fill)
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor("#C62828"), 2.1))
            painter.drawPath(path)

        baseline_y = margin_t + plot_h * (1.0 - self.baseline / self.y_max)
        painter.setPen(QPen(QColor("#2E7D32"), 1, Qt.DashDotLine))
        painter.drawLine(QPointF(margin_l, baseline_y),
                         QPointF(margin_l + plot_w, baseline_y))
        painter.setFont(QFont("Segoe UI", 7))
        painter.drawText(QRectF(margin_l + 4, baseline_y - 17, 90, 16),
                         Qt.AlignLeft, "5 mm baseline")

        painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
        for number, marker in enumerate(self.markers):
            px = margin_l + marker["index"] * x_scale
            if px < margin_l or px > margin_l + plot_w:
                continue
            color = QColor(marker["color"])
            painter.setPen(QPen(color, 1.2, Qt.DashLine))
            painter.drawLine(QPointF(px, margin_t),
                             QPointF(px, margin_t + plot_h))
            painter.setPen(color)
            label_y = margin_t + plot_h + 3 + (number % 2) * 20
            painter.drawText(QRectF(px - 72, label_y, 144, 20),
                             Qt.AlignHCenter | Qt.AlignTop,
                             marker["label"].replace("\n", " "))


class LiveGraphWidget(QWidget):
    """Kymograph with permanent data, lateral scrolling and full PNG export."""

    export_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        ensure_application_font()
        self.setMinimumSize(360, 300)
        self.measurements = []
        self.export_notes = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        tools = QHBoxLayout()
        title = QLabel("Complete recording")
        title.setStyleSheet("font-weight: 700; color: #0D47A1;")
        tools.addWidget(title)
        tools.addStretch()
        self.follow_check = QCheckBox("Follow latest")
        self.follow_check.setChecked(True)
        self.follow_check.setToolTip(
            "Clear this box to move the horizontal bar and inspect old records."
        )
        tools.addWidget(self.follow_check)
        self.save_button = QPushButton("Save recording as PNG")
        self.save_button.setProperty("secondary", True)
        self.save_button.setToolTip(
            "Save the complete trace, dose, response and measured height."
        )
        self.save_button.clicked.connect(self.export_requested.emit)
        tools.addWidget(self.save_button)
        layout.addLayout(tools)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.canvas = KymographCanvas()
        self.scroll_area.setWidget(self.canvas)
        layout.addWidget(self.scroll_area, 1)

        self.scroll_area.horizontalScrollBar().sliderMoved.connect(
            self._manual_scroll
        )

    @property
    def trace_data(self):
        return self.canvas.trace_data

    @property
    def markers(self):
        return self.canvas.markers

    def _manual_scroll(self, value):
        bar = self.scroll_area.horizontalScrollBar()
        if value < bar.maximum():
            self.follow_check.setChecked(False)

    def _follow_latest(self):
        if self.follow_check.isChecked():
            bar = self.scroll_area.horizontalScrollBar()
            bar.setValue(bar.maximum())

    def add_point(self, value):
        self.canvas.add_point(value)
        QTimer.singleShot(0, self._follow_latest)

    def add_points(self, values):
        self.canvas.add_points(values)
        QTimer.singleShot(0, self._follow_latest)

    def add_marker(self, label, color="#1565C0"):
        self.canvas.add_marker(label, color)

    def add_measurement(self, label, dose_text, response_pct, height_mm,
                        note=""):
        self.measurements.append({
            "label": str(label),
            "dose": str(dose_text),
            "response": float(response_pct),
            "height": float(height_mm),
            "note": str(note),
        })

    def clear(self):
        self.canvas.clear()
        self.measurements = []
        self.export_notes = ""
        self.follow_check.setChecked(True)
        QTimer.singleShot(0, self._follow_latest)

    def choose_and_save(self, parent=None, suggested_name="frog_rectus_recording.png"):
        path, _ = QFileDialog.getSaveFileName(
            parent or self, "Save complete kymograph", suggested_name,
            "PNG image (*.png)"
        )
        if not path:
            return None
        if not path.lower().endswith(".png"):
            path += ".png"
        self.save_image(path)
        return path

    def save_image(self, path):
        """Save all retained points and an annotated result table."""
        data_count = max(1, len(self.canvas.trace_data))
        width = min(16000, max(1500, 100 + int(data_count * 2.2)))
        chart_height = 620
        row_height = 30
        table_height = 92 + max(1, len(self.measurements)) * row_height
        notes_height = 80 if self.export_notes else 32
        height = chart_height + table_height + notes_height
        image = QImage(width, height, QImage.Format_ARGB32)
        image.fill(QColor("#FFFFFF"))

        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        available_plot = width - 100
        scale = available_plot / float(max(1, data_count - 1))
        self.canvas.draw_graph(
            painter, width, chart_height, full_record=True, export_scale=scale
        )

        top = chart_height + 12
        painter.setPen(QColor(PRIMARY))
        painter.setFont(QFont("Segoe UI", 12, QFont.Bold))
        painter.drawText(QRectF(48, top, width - 96, 28),
                         Qt.AlignLeft | Qt.AlignVCenter,
                         "Dose and response record")
        top += 36

        columns = [
            ("Record", 0.18), ("Dose or sample added", 0.35),
            ("Response", 0.15), ("Graph height", 0.15), ("Note", 0.17),
        ]
        left = 48
        table_width = width - 96
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.setPen(QColor("#FFFFFF"))
        painter.setBrush(QBrush(QColor(PRIMARY)))
        painter.drawRect(QRectF(left, top, table_width, row_height))
        x = left
        for name, fraction in columns:
            cell_w = table_width * fraction
            painter.drawText(QRectF(x + 6, top, cell_w - 12, row_height),
                             Qt.AlignLeft | Qt.AlignVCenter, name)
            x += cell_w
        top += row_height

        rows = self.measurements or [{
            "label": "No completed dose", "dose": "Not recorded",
            "response": 0.0, "height": 0.0, "note": "",
        }]
        painter.setFont(QFont("Segoe UI", 9))
        for row_index, row in enumerate(rows):
            bg = QColor("#F4F8FC") if row_index % 2 == 0 else QColor("#FFFFFF")
            painter.setPen(QPen(QColor(BORDER), 1))
            painter.setBrush(QBrush(bg))
            painter.drawRect(QRectF(left, top, table_width, row_height))
            values = [
                row["label"], row["dose"], f"{row['response']:.2f} %",
                f"{row['height']:.2f} mm", row["note"],
            ]
            x = left
            painter.setPen(QColor("#243447"))
            for value, (_, fraction) in zip(values, columns):
                cell_w = table_width * fraction
                painter.drawText(QRectF(x + 6, top, cell_w - 12, row_height),
                                 Qt.AlignLeft | Qt.AlignVCenter, str(value))
                x += cell_w
            top += row_height

        top += 14
        painter.setPen(QColor(TEXT_SECONDARY))
        painter.setFont(QFont("Segoe UI", 9))
        note = self.export_notes or (
            "Educational simulation. Height is measured above the 5 mm baseline."
        )
        painter.drawText(QRectF(48, top, width - 96, notes_height - 10),
                         Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, note)
        painter.end()

        if not image.save(path, "PNG"):
            raise IOError("The PNG image could not be saved.")
        return path
