"""Scientific model for the frog rectus abdominis teaching simulator.

The numerical values are an educational calibration.  They are not universal
biological constants.  Frog species, tissue condition, temperature, contact
time and the recording system can change the observed sensitivity.
"""

import math
import random
from dataclasses import dataclass, field
from typing import Optional, Sequence, Tuple


ACH_CHLORIDE_MW = 181.66  # g/mol, acetylcholine chloride
BASELINE_MM = 5.0
MAX_CONTRACTION_MM = 45.0

MOLAR_UNIT_FACTORS = {
    "M": 1.0,
    "mM": 1e-3,
    "uM": 1e-6,
    "µM": 1e-6,
    "nM": 1e-9,
    "pM": 1e-12,
}

MASS_UNIT_TO_G_PER_L = {
    "g/L": 1.0,
    "mg/mL": 1.0,
    "mg/L": 1e-3,
    "ug/mL": 1e-3,
    "µg/mL": 1e-3,
    "ug/L": 1e-6,
    "µg/L": 1e-6,
}

CONCENTRATION_UNITS = (
    "M", "mM", "µM", "nM", "pM",
    "g/L", "mg/mL", "mg/L", "µg/mL", "µg/L",
)


def parse_positive_number(text: str) -> float:
    """Parse a positive decimal or scientific notation value."""
    cleaned = str(text).strip().replace(",", "")
    value = float(cleaned)
    if not math.isfinite(value) or value <= 0:
        raise ValueError("Enter a positive finite concentration.")
    return value


def concentration_to_molar(value: float, unit: str,
                           molecular_weight: Optional[float] = None) -> float:
    """Convert molar or mass concentration to mol/L.

    Mass units need the molecular weight of the material actually weighed.
    For ACh this simulator uses acetylcholine chloride, 181.66 g/mol.
    """
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError("Concentration must be a positive finite value.")
    if unit in MOLAR_UNIT_FACTORS:
        converted = value * MOLAR_UNIT_FACTORS[unit]
        if not math.isfinite(converted):
            raise ValueError("Concentration is outside the supported numeric range.")
        return converted
    if unit in MASS_UNIT_TO_G_PER_L:
        if molecular_weight is None or molecular_weight <= 0:
            raise ValueError("Molecular weight is required for a mass unit.")
        converted = value * MASS_UNIT_TO_G_PER_L[unit] / molecular_weight
        if not math.isfinite(converted):
            raise ValueError("Concentration is outside the supported numeric range.")
        return converted
    raise ValueError("Unsupported concentration unit: %s" % unit)


def molar_to_concentration(molar: float, unit: str,
                           molecular_weight: Optional[float] = None) -> float:
    """Convert mol/L to a selected molar or mass concentration unit."""
    molar = float(molar)
    if not math.isfinite(molar) or molar < 0:
        raise ValueError("Molar concentration must be finite and non-negative.")
    if unit in MOLAR_UNIT_FACTORS:
        converted = molar / MOLAR_UNIT_FACTORS[unit]
        if not math.isfinite(converted):
            raise ValueError("Concentration is outside the supported numeric range.")
        return converted
    if unit in MASS_UNIT_TO_G_PER_L:
        if molecular_weight is None or molecular_weight <= 0:
            raise ValueError("Molecular weight is required for a mass unit.")
        converted = molar * molecular_weight / MASS_UNIT_TO_G_PER_L[unit]
        if not math.isfinite(converted):
            raise ValueError("Concentration is outside the supported numeric range.")
        return converted
    raise ValueError("Unsupported concentration unit: %s" % unit)


def dose_to_display(dose_molar: float) -> str:
    """Return a readable molar concentration without hiding small values."""
    dose_molar = float(dose_molar)
    if dose_molar >= 1:
        return f"{dose_molar:.4g} M"
    if dose_molar >= 1e-3:
        return f"{dose_molar * 1e3:.4g} mM"
    if dose_molar >= 1e-6:
        return f"{dose_molar * 1e6:.4g} µM"
    if dose_molar >= 1e-9:
        return f"{dose_molar * 1e9:.4g} nM"
    return f"{dose_molar * 1e12:.4g} pM"


def hill_response(dose_molar: float, emax: float, ec50_molar: float,
                  hill_n: float = 1.0) -> float:
    """Deterministic monotonic saturable concentration response."""
    dose = float(dose_molar)
    if dose <= 0 or emax <= 0:
        return 0.0
    if ec50_molar <= 0 or hill_n <= 0:
        raise ValueError("EC50 and Hill coefficient must be positive.")
    # Log domain evaluation remains stable for any finite positive manual dose.
    log_ratio = hill_n * (math.log(ec50_molar) - math.log(dose))
    if log_ratio >= 709.0:
        return 0.0
    if log_ratio <= -709.0:
        return float(emax)
    response = emax / (1.0 + math.exp(log_ratio))
    return max(0.0, min(float(emax), response))


def response_height_mm(response_pct: float) -> float:
    """Convert percent maximum response to height above baseline in mm."""
    pct = max(0.0, min(100.0, float(response_pct)))
    return MAX_CONTRACTION_MM * pct / 100.0


@dataclass
class Drug:
    name: str
    drug_type: str
    emax: float = 100.0
    ec50: float = 1e-6
    hill_n: float = 1.5
    kb: float = 1e-8
    color: str = "#1769AA"
    molecular_weight: Optional[float] = None
    material_name: str = ""
    blocks_frog_rectus_nicotinic: bool = False

    def mean_response(self, dose: float, antagonist_conc: float = 0.0,
                      antagonist_kb: float = 1e-8,
                      antagonist_effective: bool = True) -> float:
        """Return the reproducible mean response used for teaching and assay."""
        ec50_app = self.ec50
        if antagonist_effective and antagonist_conc > 0:
            if antagonist_kb <= 0:
                raise ValueError("Antagonist KB must be positive.")
            ec50_app *= 1.0 + antagonist_conc / antagonist_kb
        return hill_response(dose, self.emax, ec50_app, self.hill_n)

    def response(self, dose: float, antagonist_conc: float = 0.0,
                 antagonist_kb: float = 1e-8,
                 antagonist_effective: bool = True,
                 variability_pct: float = 0.0,
                 rng: Optional[random.Random] = None) -> float:
        """Return response with optional explicitly requested biological noise.

        Noise is off by default so increasing ACh concentrations always give a
        monotonic teaching curve and bioassay calculations remain reusable.
        """
        mean = self.mean_response(
            dose, antagonist_conc, antagonist_kb, antagonist_effective
        )
        if variability_pct <= 0:
            return mean
        source = rng if rng is not None else random
        varied = mean * (1.0 + source.gauss(0.0, variability_pct / 100.0))
        return max(0.0, min(self.emax, varied))


DRUG_LIBRARY = {
    "Acetylcholine": Drug(
        name="Acetylcholine", drug_type="agonist", emax=100.0,
        ec50=3e-6, hill_n=1.6, color="#1565C0",
        molecular_weight=ACH_CHLORIDE_MW,
        material_name="Acetylcholine chloride",
    ),
    "Carbachol": Drug(
        name="Carbachol", drug_type="agonist", emax=100.0,
        ec50=1e-6, hill_n=1.5, color="#00897B",
        molecular_weight=182.65, material_name="Carbachol chloride",
    ),
    "Nicotine": Drug(
        name="Nicotine", drug_type="agonist", emax=85.0,
        ec50=5e-6, hill_n=1.3, color="#EF6C00",
        molecular_weight=162.23, material_name="Nicotine",
    ),
    "Succinylcholine": Drug(
        name="Succinylcholine", drug_type="agonist", emax=95.0,
        ec50=8e-6, hill_n=1.2, color="#2E7D32",
        molecular_weight=361.31, material_name="Succinylcholine chloride",
    ),
    "d-Tubocurarine": Drug(
        name="d-Tubocurarine", drug_type="antagonist", emax=0.0,
        ec50=1e-6, hill_n=1.0, kb=2e-7, color="#C62828",
        blocks_frog_rectus_nicotinic=True,
    ),
    "Atropine": Drug(
        name="Atropine", drug_type="antagonist", emax=0.0,
        ec50=1e-6, hill_n=1.0, kb=1e-9, color="#6A1B9A",
        blocks_frog_rectus_nicotinic=False,
    ),
}


def get_agonists():
    return {name: drug for name, drug in DRUG_LIBRARY.items()
            if drug.drug_type == "agonist"}


def get_antagonists():
    """Return blockers relevant to the frog skeletal nicotinic response."""
    return {name: drug for name, drug in DRUG_LIBRARY.items()
            if drug.drug_type == "antagonist"
            and drug.blocks_frog_rectus_nicotinic}


def generate_dose_series(start: float = 1e-8, end: float = 1e-3,
                         points_per_log: int = 4) -> list:
    if start <= 0 or end <= start or points_per_log < 1:
        raise ValueError("Use positive increasing limits and at least one point per log.")
    log_start = math.log10(start)
    log_end = math.log10(end)
    count = max(2, int((log_end - log_start) * points_per_log) + 1)
    return [10 ** (log_start + i * (log_end - log_start) / (count - 1))
            for i in range(count)]


def log_interpolate_concentration(low_conc: float, high_conc: float,
                                  low_response: float, high_response: float,
                                  test_response: float) -> float:
    """Estimate concentration between two standards on a log dose axis."""
    if low_conc <= 0 or high_conc <= low_conc:
        raise ValueError("Standard concentrations must be positive and increasing.")
    if high_response <= low_response:
        raise ValueError("Standard responses must be increasing.")
    if test_response < low_response or test_response > high_response:
        raise ValueError("Unknown response is not bracketed by the standards.")
    fraction = (test_response - low_response) / (high_response - low_response)
    return math.exp(math.log(low_conc) + fraction *
                    (math.log(high_conc) - math.log(low_conc)))


def interpolate_standard_curve(standards: Sequence[Tuple[float, float]],
                               test_response: float) -> float:
    """Find bracketing standards and perform local log interpolation."""
    points = sorted((float(c), float(r)) for c, r in standards)
    if len(points) < 2:
        raise ValueError("At least two standards are required.")
    for (c1, r1), (c2, r2) in zip(points, points[1:]):
        if r1 <= test_response <= r2:
            return log_interpolate_concentration(c1, c2, r1, r2, test_response)
    raise ValueError("Unknown response is outside the standard response range.")


def estimate_three_point_concentration(std_low_conc: float,
                                       std_high_conc: float,
                                       std_low_response: float,
                                       std_high_response: float,
                                       test_response: float) -> float:
    """Three point assay: two standards and one unknown response."""
    return log_interpolate_concentration(
        std_low_conc, std_high_conc,
        std_low_response, std_high_response, test_response,
    )


def estimate_four_point_concentration(std_low_conc: float,
                                      std_high_conc: float,
                                      std_low_response: float,
                                      std_high_response: float,
                                      test_low_response: float,
                                      test_high_response: float) -> float:
    """Parallel line estimate for a four point bioassay.

    S1 and S2 are standard doses. T1 and T2 are two proportional doses of the
    unknown sample with the same dose ratio. The result is the concentration
    represented by T1. Both pairs should lie in the approximately linear,
    submaximal part of the response curve.
    """
    if std_low_conc <= 0 or std_high_conc <= std_low_conc:
        raise ValueError("Standard concentrations must be positive and increasing.")
    log_ratio = math.log(std_high_conc / std_low_conc)
    standard_rise = std_high_response - std_low_response
    test_rise = test_high_response - test_low_response
    common_slope = (standard_rise + test_rise) / (2.0 * log_ratio)
    if common_slope <= 0:
        raise ValueError("Responses do not show a positive parallel slope.")
    shift = ((test_low_response - std_low_response) +
             (test_high_response - std_high_response)) / (2.0 * common_slope)
    return std_low_conc * math.exp(shift)


@dataclass
class ExperimentState:
    bath_drug: Optional[str] = None
    bath_dose: float = 0.0
    antagonist_name: Optional[str] = None
    antagonist_conc: float = 0.0
    current_response: float = 0.0
    tissue_sensitised: bool = True
    contact_time: float = 0.0
    dose_history: list = field(default_factory=list)
    response_history: list = field(default_factory=list)
    is_washed: bool = True

    def add_drug(self, drug_name: str, dose: float):
        drug = DRUG_LIBRARY.get(drug_name)
        if not drug or drug.drug_type != "agonist":
            raise ValueError("Select a valid agonist.")
        self.bath_drug = drug_name
        self.bath_dose = dose
        self.is_washed = False
        self.contact_time = 0.0

        antagonist = DRUG_LIBRARY.get(self.antagonist_name)
        effective = bool(antagonist and antagonist.blocks_frog_rectus_nicotinic)
        self.current_response = drug.mean_response(
            dose,
            antagonist_conc=self.antagonist_conc if effective else 0.0,
            antagonist_kb=antagonist.kb if effective else 1.0,
            antagonist_effective=effective,
        )
        self.dose_history.append(dose)
        self.response_history.append(self.current_response)

    def add_antagonist(self, drug_name: str, conc: float):
        drug = DRUG_LIBRARY.get(drug_name)
        if not drug or not drug.blocks_frog_rectus_nicotinic:
            raise ValueError("This drug is not a relevant nicotinic blocker here.")
        self.antagonist_name = drug_name
        self.antagonist_conc = conc

    def wash(self):
        self.bath_drug = None
        self.bath_dose = 0.0
        self.current_response = 0.0
        self.is_washed = True
        self.contact_time = 0.0

    def full_reset(self):
        self.wash()
        self.antagonist_name = None
        self.antagonist_conc = 0.0
        self.dose_history.clear()
        self.response_history.clear()
        self.tissue_sensitised = True


def generate_contraction_curve(response_pct: float, duration_frames: int = 100,
                               baseline: float = BASELINE_MM) -> list:
    """Generate a reproducible contracture trace in millimetres."""
    frames = max(20, int(duration_frames))
    height = response_height_mm(response_pct)
    trace = []
    for i in range(frames):
        t = i / float(frames - 1)
        if t < 0.08:
            y = baseline
        elif t < 0.34:
            u = (t - 0.08) / 0.26
            smooth = u * u * (3.0 - 2.0 * u)
            y = baseline + height * smooth
        elif t < 0.78:
            y = baseline + height + 0.10 * math.sin(t * 45.0)
        else:
            u = (t - 0.78) / 0.22
            y = baseline + height * (1.0 - 0.08 * u)
        trace.append((t, max(0.0, y)))
    return trace


def generate_wash_curve(current_height: float, baseline: float = BASELINE_MM,
                        duration_frames: int = 60) -> list:
    frames = max(15, int(duration_frames))
    start = max(baseline, float(current_height))
    trace = []
    for i in range(frames):
        t = i / float(frames - 1)
        y = baseline + (start - baseline) * math.exp(-4.5 * t)
        trace.append((t, y))
    trace[-1] = (1.0, baseline)
    return trace
