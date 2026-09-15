"""Responsive virtual organ bath experiment with complete recording."""

from ..qt_compat import (
    Signal, Qt, QTimer, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QComboBox, QGroupBox, QSplitter, QTextEdit,
    QMessageBox, QScrollArea,
)
from ..simulation import (
    DRUG_LIBRARY, ExperimentState, get_agonists, get_antagonists,
    dose_to_display, response_height_mm,
    generate_contraction_curve, generate_wash_curve,
)
from .concentration_input import ConcentrationInput
from .organ_bath import OrganBathWidget
from .live_graph import LiveGraphWidget
from .style import (
    TEXT_SECONDARY, BORDER, INSTITUTION_TEXT, INSTITUTION_LABEL_STYLE,
)


class VirtualLabScreen(QWidget):
    go_back = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = ExperimentState()
        self.record_count = 0
        self._anim_queue = []
        self._anim_index = 0
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._play_animation)
        self.setup_ui()

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 9, 12, 12)
        root.setSpacing(8)

        top = QGridLayout()
        back_button = QPushButton("Back to home")
        back_button.setProperty("secondary", True)
        back_button.setMaximumWidth(150)
        back_button.clicked.connect(self.go_back.emit)
        top.addWidget(back_button, 0, 0, 2, 1)

        title = QLabel("Virtual Experiment Lab")
        title.setProperty("heading", True)
        title.setWordWrap(True)
        top.addWidget(title, 0, 1)
        institution = QLabel(INSTITUTION_TEXT)
        institution.setStyleSheet(INSTITUTION_LABEL_STYLE)
        institution.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        top.addWidget(institution, 0, 2)
        self.status_label = QLabel("Ready. Add a drug after tissue equilibration.")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-style: italic; padding: 2px 6px;"
        )
        top.addWidget(self.status_label, 1, 1)
        top.setColumnStretch(1, 1)
        root.addLayout(top)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)

        left_content = QWidget()
        left_content.setMinimumWidth(270)
        left_layout = QVBoxLayout(left_content)
        left_layout.setContentsMargins(4, 4, 7, 7)
        left_layout.setSpacing(8)

        drug_group = QGroupBox("Agonist and final bath concentration")
        drug_layout = QGridLayout(drug_group)
        drug_layout.addWidget(QLabel("Agonist"), 0, 0)
        self.agonist_combo = QComboBox()
        self.agonist_combo.addItems(list(get_agonists().keys()))
        self.agonist_combo.currentTextChanged.connect(self._update_material_note)
        drug_layout.addWidget(self.agonist_combo, 0, 1)
        drug_layout.addWidget(QLabel("Concentration"), 1, 0)
        self.dose_input = ConcentrationInput("1", "µM", include_mass_units=True)
        drug_layout.addWidget(self.dose_input, 1, 1)
        self.material_note = QLabel("")
        self.material_note.setWordWrap(True)
        self.material_note.setStyleSheet(
            "color: #455A64; background: #EAF4FF; padding: 7px; "
            "border-radius: 5px; font-size: 11px;"
        )
        drug_layout.addWidget(self.material_note, 2, 0, 1, 2)
        left_layout.addWidget(drug_group)

        antagonist_group = QGroupBox("Antagonist pre-incubation")
        antagonist_layout = QGridLayout(antagonist_group)
        antagonist_layout.addWidget(QLabel("Antagonist"), 0, 0)
        self.antag_combo = QComboBox()
        self.antag_combo.addItem("None")
        self.antag_combo.addItems(list(get_antagonists().keys()))
        antagonist_layout.addWidget(self.antag_combo, 0, 1)
        antagonist_layout.addWidget(QLabel("Concentration"), 1, 0)
        self.antag_input = ConcentrationInput(
            "100", "nM", include_mass_units=False
        )
        antagonist_layout.addWidget(self.antag_input, 1, 1)
        self.add_antag_button = QPushButton("Apply pre-incubation")
        self.add_antag_button.setProperty("secondary", True)
        self.add_antag_button.clicked.connect(self.add_antagonist)
        antagonist_layout.addWidget(self.add_antag_button, 2, 0, 1, 2)
        antag_note = QLabel(
            "d Tubocurarine blocks nicotinic Nm receptors competitively. "
            "Atropine is not used because muscarinic blockade does not give "
            "a meaningful shift of this skeletal muscle ACh response."
        )
        antag_note.setWordWrap(True)
        antag_note.setStyleSheet("color: #5D4037; font-size: 10px;")
        antagonist_layout.addWidget(antag_note, 3, 0, 1, 2)
        left_layout.addWidget(antagonist_group)

        action_group = QGroupBox("Experiment actions")
        action_layout = QVBoxLayout(action_group)
        self.add_drug_button = QPushButton("Add selected drug to bath")
        self.add_drug_button.setProperty("success", True)
        self.add_drug_button.clicked.connect(self.add_drug)
        action_layout.addWidget(self.add_drug_button)
        self.wash_button = QPushButton("Wash tissue")
        self.wash_button.clicked.connect(self.wash_tissue)
        action_layout.addWidget(self.wash_button)
        save_button = QPushButton("Save complete recording as PNG")
        save_button.setProperty("secondary", True)
        save_button.clicked.connect(self._export_graph)
        action_layout.addWidget(save_button)
        self.reset_button = QPushButton("Full reset")
        self.reset_button.setProperty("danger", True)
        self.reset_button.clicked.connect(self.full_reset)
        action_layout.addWidget(self.reset_button)
        left_layout.addWidget(action_group)

        log_group = QGroupBox("Experiment log")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(145)
        self.log_text.setStyleSheet(
            f"background: #F8FBFE; border: 1px solid {BORDER}; "
            "font-family: Consolas, 'Courier New', monospace; font-size: 10px;"
        )
        log_layout.addWidget(self.log_text)
        left_layout.addWidget(log_group)
        left_layout.addStretch()

        self.left_scroll = QScrollArea()
        self.left_scroll.setWidgetResizable(True)
        self.left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.left_scroll.setWidget(left_content)
        self.left_scroll.setMinimumWidth(285)
        self.splitter.addWidget(self.left_scroll)

        self.organ_bath = OrganBathWidget()
        self.splitter.addWidget(self.organ_bath)

        self.graph = LiveGraphWidget()
        self.graph.export_requested.connect(self._export_graph)
        self.splitter.addWidget(self.graph)

        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.setStretchFactor(2, 4)
        self.splitter.setSizes([310, 310, 650])
        root.addWidget(self.splitter, 1)

        self._update_material_note(self.agonist_combo.currentText())
        self.log("Experiment started. Tissue is mounted in aerated Frog Ringer solution.")
        self.log("The displayed EC50 is a simulator calibration, not a universal constant.")

    def _update_material_note(self, drug_name):
        drug = DRUG_LIBRARY.get(drug_name)
        if not drug:
            return
        if drug_name == "Acetylcholine":
            material = "Mass units use acetylcholine chloride MW 181.66 g/mol."
        else:
            material = f"Mass units use {drug.material_name} MW {drug.molecular_weight:g} g/mol."
        self.material_note.setText(
            "Enter the final organ bath concentration. This screen does not "
            "treat the entry as a stock concentration. " + material
        )

    def log(self, message):
        self.log_text.append("• " + str(message))
        bar = self.log_text.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _selected_agonist_molar(self):
        name = self.agonist_combo.currentText()
        drug = DRUG_LIBRARY[name]
        return name, drug, self.dose_input.molar(drug.molecular_weight)

    def add_drug(self):
        if self._anim_timer.isActive():
            self.status_label.setText("Please wait for the present recording to finish.")
            return
        if not self.state.is_washed:
            QMessageBox.information(
                self, "Wash required",
                "Wash the tissue before adding the next agonist dose. "
                "This keeps the practical sequence scientifically clear."
            )
            return
        try:
            drug_name, drug, dose_molar = self._selected_agonist_molar()
        except (ValueError, OverflowError) as exc:
            QMessageBox.warning(self, "Invalid concentration", str(exc))
            return

        self.state.add_drug(drug_name, dose_molar)
        response = self.state.current_response
        height = response_height_mm(response)
        dose_text = dose_to_display(dose_molar)
        self.record_count += 1
        record_label = f"R{self.record_count}"

        self.organ_bath.set_drug(drug_name, drug.color)
        self.graph.add_marker(f"{record_label} {drug_name} {dose_text}", drug.color)
        self.graph.add_measurement(
            record_label, f"{drug_name} {dose_text}", response, height,
            "Final bath concentration"
        )
        self.graph.export_notes = (
            "Educational Hill model. ACh EC50 is calibrated to 3 µM for this "
            "simulator. Species, bath composition, temperature and contact time "
            "can change a real tissue response. Height is above the 5 mm baseline."
        )
        self.log(
            f"{record_label}: {drug_name} {dose_text}; response {response:.2f} %; "
            f"height {height:.2f} mm."
        )
        self.status_label.setText(
            f"Recording {record_label}: {drug_name} {dose_text}, response {response:.2f} %"
        )
        self._start_animation(generate_contraction_curve(response, 82))

    def add_antagonist(self):
        name = self.antag_combo.currentText()
        if name == "None":
            self.state.antagonist_name = None
            self.state.antagonist_conc = 0.0
            self.log("Antagonist cleared. Use full reset for a fresh control series.")
            self.status_label.setText("No antagonist is selected.")
            return
        try:
            concentration = self.antag_input.molar()
            self.state.add_antagonist(name, concentration)
        except (ValueError, OverflowError) as exc:
            QMessageBox.warning(self, "Invalid antagonist concentration", str(exc))
            return
        dose_text = dose_to_display(concentration)
        self.graph.add_marker(f"Pre-incubation {name} {dose_text}",
                              DRUG_LIBRARY[name].color)
        self.log(
            f"Pre-incubated with {name} {dose_text}. Allow the stated contact "
            "period before giving ACh."
        )
        self.status_label.setText(f"{name} {dose_text} is present in the bath.")

    def wash_tissue(self):
        if self._anim_timer.isActive():
            self.status_label.setText("Please wait for the present recording to finish.")
            return
        if self.state.is_washed:
            self.log("Tissue is already washed and ready.")
            return
        current_absolute_height = 5.0 + response_height_mm(self.state.current_response)
        self.state.wash()
        self.organ_bath.clear_drug()
        self.graph.add_marker("Wash", "#2E7D32")
        self.log("Tissue washed with fresh aerated Frog Ringer solution.")
        self.status_label.setText("Tissue washed. It is ready for the next dose.")
        self._start_animation(generate_wash_curve(current_absolute_height, 5.0, 52))

    def full_reset(self):
        reply = QMessageBox.question(
            self, "Confirm reset",
            "Reset the experiment and remove all current recording data?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self._anim_timer.stop()
        self.state.full_reset()
        self.record_count = 0
        self.organ_bath.set_contraction(0)
        self.organ_bath.clear_drug()
        self.graph.clear()
        self.log_text.clear()
        self.log("Fresh tissue mounted. The experiment is ready.")
        self.status_label.setText("Ready. Add a drug after tissue equilibration.")

    def _start_animation(self, trace_data):
        self._anim_queue = list(trace_data)
        self._anim_index = 0
        self._anim_timer.start(35)

    def _play_animation(self):
        if self._anim_index >= len(self._anim_queue):
            self._anim_timer.stop()
            return
        _, height = self._anim_queue[self._anim_index]
        self.graph.add_point(height)
        contraction = max(0.0, min(100.0, (height - 5.0) / 45.0 * 100.0))
        self.organ_bath.set_contraction(contraction)
        self._anim_index += 1

    def _export_graph(self):
        try:
            path = self.graph.choose_and_save(
                self, "frog_rectus_complete_recording.png"
            )
        except (IOError, OSError) as exc:
            QMessageBox.warning(self, "Could not save image", str(exc))
            return
        if path:
            self.status_label.setText("Complete annotated recording saved as PNG.")
            self.log("Saved complete annotated recording as a PNG image.")

    def resizeEvent(self, event):
        compact = self.width() < 980
        orientation = Qt.Vertical if compact else Qt.Horizontal
        if self.splitter.orientation() != orientation:
            self.splitter.setOrientation(orientation)
            if compact:
                self.setMinimumHeight(1280)
                self.left_scroll.setMinimumHeight(480)
                self.splitter.setSizes([500, 350, 430])
            else:
                self.setMinimumHeight(0)
                self.left_scroll.setMinimumHeight(0)
                self.splitter.setSizes([310, 310, 650])
        super().resizeEvent(event)
