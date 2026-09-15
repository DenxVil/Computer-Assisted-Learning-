"""Unknown ACh concentration practical with three accepted assay methods."""

import math
import random

from ..qt_compat import (
    Signal, Qt, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton,
    QLabel, QComboBox, QGroupBox, QSplitter, QMessageBox, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
)
from ..simulation import (
    ACH_CHLORIDE_MW, DRUG_LIBRARY, dose_to_display, response_height_mm,
    generate_contraction_curve, generate_wash_curve,
    interpolate_standard_curve, estimate_three_point_concentration,
    estimate_four_point_concentration,
)
from .concentration_input import ConcentrationInput
from .organ_bath import OrganBathWidget
from .live_graph import LiveGraphWidget
from .style import (
    BORDER, SUCCESS, DANGER, TEXT_SECONDARY, INSTITUTION_TEXT,
    INSTITUTION_LABEL_STYLE,
)


class UnknownDrugScreen(QWidget):
    """The historic class name is kept so existing navigation remains valid."""

    go_back = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ach = DRUG_LIBRARY["Acetylcholine"]
        self.secret_molar = None
        self.sample_code = ""
        self.records = []
        self.calculated_molar = None
        self.revealed = False
        self._random = random.SystemRandom()
        self.setup_ui()
        self.new_unknown()

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 9, 12, 12)
        root.setSpacing(8)

        top = QHBoxLayout()
        back_button = QPushButton("Back to home")
        back_button.setProperty("secondary", True)
        back_button.setMaximumWidth(150)
        back_button.clicked.connect(self.go_back.emit)
        top.addWidget(back_button)
        title = QLabel("Unknown ACh Concentration Bioassay")
        title.setProperty("heading", True)
        title.setWordWrap(True)
        top.addWidget(title, 1)
        institution = QLabel(INSTITUTION_TEXT)
        institution.setStyleSheet(INSTITUTION_LABEL_STYLE)
        institution.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        top.addWidget(institution)
        root.addLayout(top)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)

        controls = QWidget()
        controls.setMinimumWidth(285)
        control_layout = QVBoxLayout(controls)
        control_layout.setContentsMargins(4, 4, 7, 7)

        intro = QLabel(
            "The bottle contains acetylcholine chloride, but its concentration "
            "is hidden. Record standards and the unknown on the same preparation. "
            "Use responses in the submaximal range."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet(
            "background: #E8F5E9; color: #1B5E20; border: 1px solid #A5D6A7; "
            "border-radius: 7px; padding: 9px;"
        )
        control_layout.addWidget(intro)

        setup_group = QGroupBox("Assay setting")
        setup_layout = QGridLayout(setup_group)
        setup_layout.addWidget(QLabel("Method"), 0, 0)
        self.method_combo = QComboBox()
        self.method_combo.addItem("Interpolation method", "interpolation")
        self.method_combo.addItem("Three point bioassay", "three_point")
        self.method_combo.addItem("Four point bioassay", "four_point")
        self.method_combo.currentIndexChanged.connect(self._method_changed)
        setup_layout.addWidget(self.method_combo, 0, 1)
        setup_layout.addWidget(QLabel("Low standard"), 1, 0)
        self.low_input = ConcentrationInput("1", "µM", include_mass_units=True)
        setup_layout.addWidget(self.low_input, 1, 1)
        setup_layout.addWidget(QLabel("High standard"), 2, 0)
        self.high_input = ConcentrationInput("6", "µM", include_mass_units=True)
        setup_layout.addWidget(self.high_input, 2, 1)
        salt_note = QLabel(
            "All mass units are converted using acetylcholine chloride "
            "molecular weight 181.66 g/mol. Entries are final bath concentrations."
        )
        salt_note.setWordWrap(True)
        salt_note.setStyleSheet("color: #455A64; font-size: 10px;")
        setup_layout.addWidget(salt_note, 3, 0, 1, 2)
        control_layout.addWidget(setup_group)

        unknown_group = QGroupBox("Unknown sample")
        unknown_layout = QVBoxLayout(unknown_group)
        self.code_label = QLabel("")
        self.code_label.setWordWrap(True)
        self.code_label.setStyleSheet(
            "background: #FFF8E1; color: #6D4C41; padding: 8px; "
            "border-radius: 6px; font-weight: 650;"
        )
        unknown_layout.addWidget(self.code_label)
        new_button = QPushButton("Prepare a new unknown sample")
        new_button.setProperty("secondary", True)
        new_button.clicked.connect(self.new_unknown)
        unknown_layout.addWidget(new_button)
        self.run_button = QPushButton("Run selected bioassay")
        self.run_button.setProperty("success", True)
        self.run_button.clicked.connect(self.run_assay)
        unknown_layout.addWidget(self.run_button)
        calculate_button = QPushButton("Calculate from recorded responses")
        calculate_button.clicked.connect(self.calculate_from_records)
        unknown_layout.addWidget(calculate_button)
        control_layout.addWidget(unknown_group)

        answer_group = QGroupBox("Student answer")
        answer_layout = QVBoxLayout(answer_group)
        answer_layout.addWidget(QLabel("Estimated unknown concentration"))
        self.answer_input = ConcentrationInput(
            "1", "µM", include_mass_units=True
        )
        answer_layout.addWidget(self.answer_input)
        check_button = QPushButton("Check my estimate and reveal result")
        check_button.clicked.connect(self.check_answer)
        answer_layout.addWidget(check_button)
        self.result_label = QLabel("Run the assay to obtain observations.")
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet(
            f"border: 1px solid {BORDER}; background: white; "
            "border-radius: 7px; padding: 9px;"
        )
        answer_layout.addWidget(self.result_label)
        control_layout.addWidget(answer_group)

        save_button = QPushButton("Save annotated result as PNG")
        save_button.setProperty("secondary", True)
        save_button.clicked.connect(self._export_graph)
        control_layout.addWidget(save_button)
        control_layout.addStretch()

        self.control_scroll = QScrollArea()
        self.control_scroll.setWidgetResizable(True)
        self.control_scroll.setWidget(controls)
        self.control_scroll.setMinimumWidth(300)
        self.splitter.addWidget(self.control_scroll)

        self.organ_bath = OrganBathWidget()
        self.splitter.addWidget(self.organ_bath)

        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        results_layout.setContentsMargins(0, 0, 0, 0)
        self.method_note = QLabel("")
        self.method_note.setWordWrap(True)
        self.method_note.setStyleSheet(
            f"color: {TEXT_SECONDARY}; background: #EAF4FF; "
            "border-radius: 6px; padding: 7px;"
        )
        results_layout.addWidget(self.method_note)
        self.graph = LiveGraphWidget()
        self.graph.export_requested.connect(self._export_graph)
        results_layout.addWidget(self.graph, 3)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "Record", "Dose or sample", "Response", "Height", "Purpose"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setMinimumHeight(180)
        results_layout.addWidget(self.table, 2)
        self.splitter.addWidget(results_widget)

        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.setStretchFactor(2, 5)
        self.splitter.setSizes([320, 285, 690])
        root.addWidget(self.splitter, 1)
        self._update_method_note()

    def _standard_limits(self):
        low = self.low_input.molar(ACH_CHLORIDE_MW)
        high = self.high_input.molar(ACH_CHLORIDE_MW)
        if high <= low:
            raise ValueError("High standard must be greater than low standard.")
        return low, high

    def _method_key(self):
        return self.method_combo.currentData()

    def _method_changed(self):
        if self._method_key() == "four_point":
            self.high_input.set_value(4, "µM")
        else:
            self.high_input.set_value(6, "µM")
        self._update_method_note()
        self.new_unknown()

    def _update_method_note(self):
        key = self._method_key()
        if key == "interpolation":
            text = (
                "Interpolation records five known ACh standards. The unknown "
                "response is located between two neighbouring standard responses "
                "on the log concentration scale."
            )
        elif key == "three_point":
            text = (
                "Three point assay uses low standard S1, high standard S2 and "
                "one unknown response T. S1 and S2 must bracket T."
            )
        else:
            text = (
                "Four point assay uses S1, S2, T1 and T2. The standard and test "
                "dose ratios are equal. Both pairs should be parallel and submaximal."
            )
        self.method_note.setText(text)

    def new_unknown(self):
        try:
            low, high = self._standard_limits()
        except (ValueError, OverflowError):
            low, high = 1e-6, 6e-6
        key = self._method_key()
        if key == "four_point":
            # T1 remains near S1 and T2 uses the same ratio as S2/S1.
            self.secret_molar = low * math.exp(
                self._random.uniform(math.log(0.82), math.log(1.28))
            )
        else:
            lower = low * 1.08
            upper = high / 1.08
            if upper <= lower:
                lower, upper = low, high
            self.secret_molar = math.exp(
                self._random.uniform(math.log(lower), math.log(upper))
            )
        self.sample_code = "U-ACH-%04d" % self._random.randint(1, 9999)
        self.revealed = False
        self.calculated_molar = None
        self.records = []
        self.graph.clear()
        self.table.setRowCount(0)
        self.organ_bath.set_contraction(0)
        self.organ_bath.clear_drug()
        self.code_label.setText(
            f"Sample code: {self.sample_code}\nIdentity: ACh chloride\n"
            "Concentration: hidden"
        )
        self.result_label.setText("New unknown prepared. Run the selected bioassay.")
        self.result_label.setStyleSheet(
            f"border: 1px solid {BORDER}; background: white; "
            "border-radius: 7px; padding: 9px;"
        )

    def run_assay(self):
        try:
            low, high = self._standard_limits()
        except (ValueError, OverflowError) as exc:
            QMessageBox.warning(self, "Invalid standards", str(exc))
            return

        key = self._method_key()
        if self.secret_molar is None:
            self.new_unknown()
        if key != "four_point" and not (low < self.secret_molar < high):
            self.new_unknown()
        if key == "four_point" and not (0.6 * low < self.secret_molar < 1.6 * low):
            self.new_unknown()

        self.records = []
        self.calculated_molar = None
        self.revealed = False
        self.graph.clear()
        self.table.setRowCount(0)

        if key == "interpolation":
            concentrations = [
                math.exp(math.log(low) + i * (math.log(high) - math.log(low)) / 4.0)
                for i in range(5)
            ]
            sequence = []
            for index, concentration in enumerate(concentrations, 1):
                sequence.append((f"S{index}", concentration,
                                 dose_to_display(concentration), "Standard"))
                if index == 3:
                    sequence.append(("U", self.secret_molar,
                                     "Unknown sample, 1 unit dose", "Unknown"))
        elif key == "three_point":
            sequence = [
                ("S1", low, dose_to_display(low), "Low standard"),
                ("T", self.secret_molar, "Unknown sample, 1 unit dose", "Unknown"),
                ("S2", high, dose_to_display(high), "High standard"),
            ]
        else:
            ratio = high / low
            sequence = [
                ("S1", low, dose_to_display(low), "Low standard"),
                ("T1", self.secret_molar,
                 "Unknown sample, 1 unit dose", "Unknown low"),
                ("S2", high, dose_to_display(high), "High standard"),
                ("T2", self.secret_molar * ratio,
                 f"Unknown sample, {ratio:.3g} unit dose", "Unknown high"),
            ]

        for label, actual_concentration, visible_dose, purpose in sequence:
            self._record_observation(
                label, actual_concentration, visible_dose, purpose,
                hidden=purpose.startswith("Unknown"),
            )

        self.organ_bath.set_drug("ACh sample", self.ach.color)
        self.graph.export_notes = (
            f"Sample {self.sample_code}. Method: {self.method_combo.currentText()}. "
            "Unknown concentration remains hidden until the student submits an "
            "estimate. ACh chloride MW 181.66 g/mol. Responses come from the "
            "documented educational calibration and are not patient data."
        )
        self.result_label.setText(
            "Assay recorded. Inspect the response table and trace. Calculate the "
            "unknown, enter your estimate and then check it."
        )

    def _record_observation(self, label, concentration, visible_dose,
                            purpose, hidden=False):
        response = self.ach.mean_response(concentration)
        height = response_height_mm(response)
        display = visible_dose if hidden else f"ACh {visible_dose}"
        self.graph.add_marker(f"{label} {display}", self.ach.color)
        contraction = generate_contraction_curve(response, 72)
        self.graph.add_points([value for _, value in contraction])
        wash = generate_wash_curve(5.0 + height, 5.0, 34)
        self.graph.add_marker("Wash", "#2E7D32")
        self.graph.add_points([value for _, value in wash])
        self.graph.add_measurement(label, display, response, height, purpose)

        record = {
            "label": label,
            "concentration": concentration,
            "visible_dose": display,
            "response": response,
            "height": height,
            "purpose": purpose,
            "hidden": hidden,
        }
        self.records.append(record)

        row = self.table.rowCount()
        self.table.insertRow(row)
        values = [
            label, display, f"{response:.2f} %", f"{height:.2f} mm", purpose,
        ]
        for column, value in enumerate(values):
            self.table.setItem(row, column, QTableWidgetItem(value))

    def _estimate_from_records(self):
        if not self.records:
            raise ValueError("Run the bioassay before calculating.")
        key = self._method_key()
        by_label = {record["label"]: record for record in self.records}
        if key == "interpolation":
            standards = [
                (record["concentration"], record["response"])
                for record in self.records if record["label"].startswith("S")
            ]
            return interpolate_standard_curve(standards, by_label["U"]["response"])
        if key == "three_point":
            return estimate_three_point_concentration(
                by_label["S1"]["concentration"],
                by_label["S2"]["concentration"],
                by_label["S1"]["response"],
                by_label["S2"]["response"],
                by_label["T"]["response"],
            )
        return estimate_four_point_concentration(
            by_label["S1"]["concentration"],
            by_label["S2"]["concentration"],
            by_label["S1"]["response"],
            by_label["S2"]["response"],
            by_label["T1"]["response"],
            by_label["T2"]["response"],
        )

    def calculate_from_records(self):
        try:
            self.calculated_molar = self._estimate_from_records()
        except ValueError as exc:
            QMessageBox.warning(self, "Cannot calculate", str(exc))
            return
        self.answer_input.set_value(self.calculated_molar * 1e6, "µM")
        self.result_label.setText(
            "Calculated estimate from the displayed responses: "
            f"{dose_to_display(self.calculated_molar)}. "
            "Submit it to reveal the coded concentration."
        )

    def check_answer(self):
        if not self.records:
            QMessageBox.information(self, "No observations", "Run the assay first.")
            return
        try:
            student_molar = self.answer_input.molar(ACH_CHLORIDE_MW)
        except (ValueError, OverflowError) as exc:
            QMessageBox.warning(self, "Invalid estimate", str(exc))
            return
        error_pct = abs(student_molar - self.secret_molar) / self.secret_molar * 100.0
        self.revealed = True
        if error_pct <= 15.0:
            result = "Accepted"
            colour = SUCCESS
            background = "#E8F5E9"
            advice = "Your estimate is within 15 percent of the coded value."
        else:
            result = "Needs review"
            colour = DANGER
            background = "#FFEBEE"
            advice = "Check bracketing, the log scale and the selected unit."
        self.result_label.setText(
            f"<b>{result}</b><br>Student estimate: {dose_to_display(student_molar)}"
            f"<br>Coded concentration: {dose_to_display(self.secret_molar)}"
            f"<br>Absolute percentage error: {error_pct:.2f} %<br>{advice}"
        )
        self.result_label.setStyleSheet(
            f"border: 2px solid {colour}; background: {background}; "
            "border-radius: 7px; padding: 9px;"
        )
        calculated = self.calculated_molar
        calculated_text = dose_to_display(calculated) if calculated else "not requested"
        self.graph.export_notes = (
            f"Sample {self.sample_code}. {self.method_combo.currentText()}. "
            f"Student estimate {dose_to_display(student_molar)}. Coded ACh chloride "
            f"concentration {dose_to_display(self.secret_molar)}. Method calculation "
            f"{calculated_text}. Error {error_pct:.2f} %. Height is above the 5 mm "
            "baseline. Educational simulation only."
        )

    def _export_graph(self):
        try:
            self.graph.choose_and_save(
                self, f"frog_rectus_{self.sample_code}_bioassay.png"
            )
        except (IOError, OSError) as exc:
            QMessageBox.warning(self, "Could not save image", str(exc))

    def resizeEvent(self, event):
        compact = self.width() < 1040
        orientation = Qt.Vertical if compact else Qt.Horizontal
        if self.splitter.orientation() != orientation:
            self.splitter.setOrientation(orientation)
            if compact:
                self.setMinimumHeight(1500)
                self.control_scroll.setMinimumHeight(575)
                self.splitter.setSizes([590, 350, 560])
            else:
                self.setMinimumHeight(0)
                self.control_scroll.setMinimumHeight(0)
                self.splitter.setSizes([320, 285, 690])
        super().resizeEvent(event)
