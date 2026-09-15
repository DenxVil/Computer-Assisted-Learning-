"""Mechanism-based response curves for the Dog BP teaching practical.

The values are deliberately schematic teaching values, not predictions for an
individual animal.  Dose-response relations are smooth and saturating within
the supported demonstration ranges, while the direction, relative timing and
major antagonist interactions follow classical autonomic pharmacology.
"""

from __future__ import annotations

import math

import numpy as np


BASELINE_SBP = 120.0
BASELINE_DBP = 80.0
BASELINE_HR = 80.0
BASELINE_MAP = (BASELINE_SBP + 2.0 * BASELINE_DBP) / 3.0


# ``display_factor`` converts the number shown in the teaching control to
# micrograms/kg, which is the common internal unit used by simulate_response.
DOSE_METADATA = {
    "Epinephrine": {
        "default_ug_kg": 2.0, "min_ug_kg": 0.1, "max_ug_kg": 10.0,
        "presets_ug_kg": (0.3, 1.0, 2.0, 3.0, 10.0),
        "display_unit": "µg/kg", "display_factor": 1.0, "step": 0.1,
    },
    "Norepinephrine": {
        "default_ug_kg": 2.0, "min_ug_kg": 0.1, "max_ug_kg": 10.0,
        "presets_ug_kg": (0.3, 1.0, 2.0, 3.0, 10.0),
        "display_unit": "µg/kg", "display_factor": 1.0, "step": 0.1,
    },
    "Isoprenaline": {
        "default_ug_kg": 0.5, "min_ug_kg": 0.05, "max_ug_kg": 2.0,
        "presets_ug_kg": (0.05, 0.1, 0.25, 0.5, 1.0, 2.0),
        "display_unit": "µg/kg", "display_factor": 1.0, "step": 0.05,
    },
    "Acetylcholine": {
        "default_ug_kg": 2.0, "min_ug_kg": 0.1, "max_ug_kg": 500.0,
        "presets_ug_kg": (1.0, 2.0, 5.0, 50.0, 500.0),
        "display_unit": "µg/kg", "display_factor": 1.0, "step": 0.5,
    },
    "Histamine": {
        "default_ug_kg": 1.0, "min_ug_kg": 0.1, "max_ug_kg": 10.0,
        "presets_ug_kg": (0.1, 0.3, 1.0, 3.0, 10.0),
        "display_unit": "µg/kg", "display_factor": 1.0, "step": 0.1,
    },
    "Ephedrine": {
        "default_ug_kg": 200.0, "min_ug_kg": 25.0, "max_ug_kg": 1000.0,
        "presets_ug_kg": (25.0, 50.0, 100.0, 200.0, 500.0, 1000.0),
        "display_unit": "mg/kg", "display_factor": 1000.0, "step": 0.05,
    },
    "Phenoxybenzamine": {
        "default_ug_kg": 1000.0, "min_ug_kg": 100.0, "max_ug_kg": 2000.0,
        "presets_ug_kg": (100.0, 250.0, 500.0, 1000.0, 2000.0),
        "display_unit": "mg/kg", "display_factor": 1000.0, "step": 0.1,
    },
    "Propranolol": {
        "default_ug_kg": 1000.0, "min_ug_kg": 100.0, "max_ug_kg": 2000.0,
        "presets_ug_kg": (100.0, 250.0, 500.0, 1000.0, 2000.0),
        "display_unit": "mg/kg", "display_factor": 1000.0, "step": 0.1,
    },
    "Atropine": {
        "default_ug_kg": 1000.0, "min_ug_kg": 100.0, "max_ug_kg": 2000.0,
        "presets_ug_kg": (100.0, 250.0, 500.0, 1000.0, 2000.0),
        "display_unit": "mg/kg", "display_factor": 1000.0, "step": 0.1,
    },
    "Saline": {
        "default_ug_kg": 0.1, "min_ug_kg": 0.05, "max_ug_kg": 1.0,
        "presets_ug_kg": (0.05, 0.1, 0.2, 0.5, 1.0),
        "display_unit": "mL/kg", "display_factor": 1.0, "step": 0.05,
    },
}


def _hill(dose: float, ec50: float, coefficient: float = 1.15) -> float:
    """Return a bounded receptor-occupancy style dose response."""
    dose = max(0.0, float(dose))
    if dose == 0.0:
        return 0.0
    numerator = dose ** coefficient
    return float(numerator / (ec50 ** coefficient + numerator))


def _profile(t, onset: float, rise: float, decay: float) -> np.ndarray:
    values = np.asarray(t, dtype=float)
    elapsed = np.maximum(values - onset, 0.0)
    response = np.where(
        values >= onset,
        (1.0 - np.exp(-elapsed / rise)) * np.exp(-elapsed / decay),
        0.0,
    )
    peak = float(np.max(response)) if response.size else 0.0
    return response / peak if peak > 0.0 else response


def _history_item(item):
    if isinstance(item, str):
        return item, DOSE_METADATA.get(item, {}).get("default_ug_kg", 0.0)
    if isinstance(item, dict):
        drug = item.get("actual_drug") or item.get("drug") or ""
        dose = item.get("dose_ug_kg", item.get("dose", 0.0))
        try:
            return str(drug), float(dose)
        except (TypeError, ValueError):
            return str(drug), 0.0
    return "", 0.0


def _pretreatment_levels(prior_drugs):
    residual = {"alpha": 1.0, "beta": 1.0, "muscarinic": 1.0}
    ephedrine_count = 0
    ephedrine_remaining = 1.0
    for item in prior_drugs or ():
        drug, dose = _history_item(item)
        if drug == "Phenoxybenzamine":
            residual["alpha"] *= 1.0 - _hill(dose, 250.0)
        elif drug == "Propranolol":
            residual["beta"] *= 1.0 - _hill(dose, 200.0)
        elif drug == "Atropine":
            residual["muscarinic"] *= 1.0 - _hill(dose, 200.0)
        elif drug == "Ephedrine":
            ephedrine_count += 1
            # A larger preceding dose depletes more releasable transmitter;
            # repeated small doses therefore accumulate rather than acting as
            # one all-or-none exposure.
            ephedrine_remaining *= 1.0 - 0.72 * _hill(dose, 150.0)
    levels = {name: 1.0 - value for name, value in residual.items()}
    levels["ephedrine_count"] = ephedrine_count
    levels["ephedrine_remaining"] = max(0.08, ephedrine_remaining)
    return levels


def validate_dose(drug: str, dose_ug_kg: float) -> tuple[bool, str]:
    """Validate a dose against the supported demonstration range."""
    metadata = DOSE_METADATA.get(drug)
    if metadata is None:
        return False, "Select a supported drug."
    try:
        dose = float(dose_ug_kg)
    except (TypeError, ValueError):
        return False, "Enter a numeric dose."
    if not math.isfinite(dose):
        return False, "Enter a finite numeric dose."
    minimum = metadata["min_ug_kg"]
    maximum = metadata["max_ug_kg"]
    if minimum <= dose <= maximum:
        return True, ""
    factor = metadata["display_factor"]
    unit = metadata["display_unit"]
    return False, (
        f"Use {minimum / factor:g} to {maximum / factor:g} {unit} for {drug}."
    )


def simulate_response(drug, dose_ug_kg, time, prior_drugs=None):
    """Generate SBP, DBP, MAP and HR arrays for one intravenous injection."""
    t = np.asarray(time, dtype=float)
    dose = max(0.0, float(dose_ug_kg))
    block = _pretreatment_levels(prior_drugs)
    # A near-saturating antagonist dose leaves only a small receptor reserve;
    # repeated submaximal doses progressively reduce that reserve.
    alpha_open = max(0.02, (1.0 - block["alpha"]) ** 1.35)
    beta_open = max(0.02, (1.0 - block["beta"]) ** 1.30)
    muscarinic_open = max(0.01, (1.0 - block["muscarinic"]) ** 1.35)

    # Persistent pretreatment shifts make the next trace start from the state
    # left by the blocker, without accumulating unbounded pressure changes.
    base_sbp = BASELINE_SBP - 8.0 * block["alpha"] - 9.0 * block["beta"]
    base_dbp = BASELINE_DBP - 11.0 * block["alpha"] - 3.0 * block["beta"]
    base_hr = (BASELINE_HR + 6.0 * block["alpha"] - 18.0 * block["beta"]
               + 15.0 * block["muscarinic"])

    sharp = _profile(t, 2.0, 0.35, 4.8)
    direct = _profile(t, 2.0, 1.1, 10.0)
    pressor = _profile(t, 2.0, 0.55, 5.7)
    delayed = _profile(t, 6.0, 1.8, 14.0)
    gradual = _profile(t, 2.0, 7.0, 38.0)
    sustained = _profile(t, 2.0, 8.0, 70.0)

    sbp_delta = np.zeros_like(t)
    dbp_delta = np.zeros_like(t)
    hr_delta = np.zeros_like(t)
    explanation = "Saline control: no important pharmacological response."

    if drug == "Epinephrine":
        alpha = _hill(dose, 1.3) * alpha_open
        beta1 = _hill(dose, 0.35) * beta_open
        beta2 = _hill(dose, 0.25) * beta_open
        sbp_delta = (42.0 * alpha + 14.0 * beta1) * pressor - 14.0 * beta2 * delayed
        dbp_delta = 43.0 * alpha * pressor - 31.0 * beta2 * delayed
        reflex = 1.0 - block["muscarinic"]
        hr_delta = 25.0 * beta1 * direct - 16.0 * alpha * reflex * delayed
        if block["alpha"] > 0.45:
            explanation = (
                "Epinephrine after alpha blockade shows Dale's vasomotor reversal: "
                "the pressor phase is suppressed and beta-2 vasodilatation lowers BP."
            )
        elif block["beta"] > 0.45:
            explanation = (
                "Epinephrine after beta blockade shows a dominant alpha pressor response "
                "with reflex slowing of heart rate."
            )
        else:
            explanation = (
                "Epinephrine is biphasic: an early alpha-1/beta-1 pressor phase is "
                "followed by a beta-2 depressor phase. Dose changes their relative size."
            )
    elif drug == "Norepinephrine":
        alpha = _hill(dose, 0.9) * alpha_open
        beta1 = _hill(dose, 0.55) * beta_open
        sbp_delta = (50.0 * alpha + 7.0 * beta1) * direct
        dbp_delta = 45.0 * alpha * direct
        hr_delta = 9.0 * beta1 * direct - 24.0 * alpha * (1.0 - block["muscarinic"]) * delayed
        explanation = (
            "Alpha blockade markedly attenuates norepinephrine's pressor response."
            if block["alpha"] > 0.45 else
            "Norepinephrine gives a rapid, dose-dependent systolic and diastolic "
            "pressor response; baroreflex bradycardia usually predominates."
        )
    elif drug == "Isoprenaline":
        beta = _hill(dose, 0.18) * beta_open
        # Increased cardiac output keeps SBP unchanged or slightly raised even
        # while beta-2 vasodilatation lowers DBP and calculated MAP.
        sbp_delta = 10.0 * beta * pressor
        dbp_delta = -42.0 * beta * direct
        hr_delta = 48.0 * beta * direct
        explanation = (
            "Propranolol markedly attenuates the isoprenaline response."
            if block["beta"] > 0.45 else
            "Isoprenaline leaves systolic BP unchanged or slightly raised, lowers "
            "diastolic and mean BP through beta-2 vasodilatation, and raises heart rate."
        )
    elif drug == "Acetylcholine":
        muscarinic = _hill(dose, 1.2) * muscarinic_open
        nicotinic = _hill(max(0.0, dose - 40.0), 140.0) * block["muscarinic"]
        sympathetic_pressor = 0.78 * alpha_open + 0.22 * beta_open
        sbp_delta = (-44.0 * muscarinic * sharp
                     + 30.0 * nicotinic * sympathetic_pressor * direct)
        dbp_delta = (-38.0 * muscarinic * sharp
                     + 24.0 * nicotinic * alpha_open * direct)
        hr_delta = (-31.0 * muscarinic * sharp
                    + 17.0 * nicotinic * beta_open * direct)
        if block["muscarinic"] > 0.45:
            explanation = (
                "Atropine suppresses the muscarinic depressor response. A sufficiently "
                "large acetylcholine dose can reveal a nicotinic pressor response."
            )
        else:
            explanation = (
                "Acetylcholine gives a sharp, brief, dose-dependent fall in BP and "
                "heart rate through vascular M3 and cardiac M2 receptors."
            )
    elif drug == "Histamine":
        effect = _hill(dose, 0.7)
        sbp_delta = -37.0 * effect * sharp
        dbp_delta = -33.0 * effect * sharp
        hr_delta = 9.0 * effect * direct
        explanation = (
            "Histamine gives a sharp, short-lived, dose-dependent depressor response "
            "through vascular H1 and H2 receptors. Heart-rate direction can vary in vivo."
        )
    elif drug == "Ephedrine":
        effect = _hill(dose, 150.0) * block["ephedrine_remaining"]
        mixed_pressor = 0.78 * alpha_open + 0.22 * beta_open
        sbp_delta = 38.0 * effect * mixed_pressor * sustained
        dbp_delta = 27.0 * effect * alpha_open * sustained
        hr_delta = 12.0 * effect * beta_open * gradual
        explanation = (
            "Ephedrine's indirect alpha/beta response is attenuated by the retained blockade."
            if block["alpha"] > 0.45 or block["beta"] > 0.45 else
            "Ephedrine gives a gradual, sustained pressor response. Larger or repeated "
            "doses deplete more releasable norepinephrine and produce tachyphylaxis."
        )
    elif drug == "Phenoxybenzamine":
        effect = _hill(dose, 350.0)
        sbp_delta = -12.0 * effect * gradual
        dbp_delta = -17.0 * effect * gradual
        hr_delta = 9.0 * effect * gradual
        explanation = (
            "Phenoxybenzamine develops a gradual fall in BP from alpha blockade, "
            "with modest reflex tachycardia."
        )
    elif drug == "Propranolol":
        effect = _hill(dose, 300.0)
        sbp_delta = -15.0 * effect * gradual
        dbp_delta = -6.0 * effect * gradual
        hr_delta = -24.0 * effect * gradual
        explanation = (
            "Propranolol gradually lowers heart rate and cardiac output. The simulated "
            "BP fall is smaller than the HR fall because acute pressure effects vary."
        )
    elif drug == "Atropine":
        effect = _hill(dose, 250.0)
        sbp_delta = 3.0 * effect * direct
        dbp_delta = 1.0 * effect * direct
        hr_delta = 22.0 * effect * direct
        explanation = (
            "Atropine removes resting vagal tone, increasing heart rate with little "
            "direct change in arterial pressure."
        )
    elif drug != "Saline":
        explanation = "Unsupported drug: no response was generated."

    # A tiny deterministic respiratory oscillation keeps the recording alive
    # without obscuring the pharmacological direction or making tests random.
    oscillation = 0.35 * np.sin(2.0 * np.pi * t / 5.0)
    sbp = np.clip(base_sbp + sbp_delta + oscillation, 45.0, 210.0)
    dbp = np.clip(base_dbp + dbp_delta + 0.55 * oscillation, 25.0, 150.0)
    dbp = np.minimum(dbp, sbp - 8.0)
    hr = np.clip(base_hr + hr_delta + 0.35 * np.sin(2.0 * np.pi * t / 4.2), 25.0, 210.0)
    mean_pressure = (sbp + 2.0 * dbp) / 3.0

    return {
        "sbp": sbp,
        "dbp": dbp,
        "map": mean_pressure,
        "hr": hr,
        "explanation": explanation,
        "baseline": {"sbp": base_sbp, "dbp": base_dbp, "map": (base_sbp + 2.0 * base_dbp) / 3.0, "hr": base_hr},
        "blockades": block,
    }
