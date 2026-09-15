"""Reusable manual concentration entry with a selectable unit."""

from ..qt_compat import QWidget, QHBoxLayout, QLineEdit, QComboBox
from ..simulation import (
    CONCENTRATION_UNITS, concentration_to_molar, parse_positive_number,
)


class ConcentrationInput(QWidget):
    def __init__(self, value="1", unit="µM", include_mass_units=True,
                 parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.value_edit = QLineEdit(str(value))
        self.value_edit.setPlaceholderText("Example: 1 or 2.5e-3")
        self.value_edit.setToolTip(
            "Enter any positive decimal value. Scientific notation is accepted."
        )
        layout.addWidget(self.value_edit, 2)

        self.unit_combo = QComboBox()
        units = CONCENTRATION_UNITS if include_mass_units else CONCENTRATION_UNITS[:5]
        self.unit_combo.addItems(list(units))
        index = self.unit_combo.findText(unit)
        self.unit_combo.setCurrentIndex(max(0, index))
        self.unit_combo.setToolTip("Select the concentration unit")
        layout.addWidget(self.unit_combo, 1)

    def value(self):
        return parse_positive_number(self.value_edit.text())

    def unit(self):
        return self.unit_combo.currentText()

    def molar(self, molecular_weight=None):
        return concentration_to_molar(
            self.value(), self.unit(), molecular_weight=molecular_weight
        )

    def set_value(self, value, unit=None):
        self.value_edit.setText(f"{float(value):.8g}")
        if unit is not None:
            index = self.unit_combo.findText(unit)
            if index >= 0:
                self.unit_combo.setCurrentIndex(index)
