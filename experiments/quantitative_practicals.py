"""Examiner-configured quantitative frog rectus practicals.

This source-only module is opened from the suite examination menu. It provides
two public Tkinter classes, ``FrogRectusUnknownPractical`` and
``BioassayUnknownPractical``. Pure conversion, response, and calculation
helpers can be tested without creating a Tk window or writing a result file.
"""

import itertools
import math
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from experiments.bioassay import (
    ACH_CONCENTRATION_UNITS,
    ACH_EMAX_MM,
    BioassaySimulation,
    ach_response_from_micromolar,
    concentration_to_micromolar as ach_concentration_to_micromolar,
)
from experiments.combined_exams import examiner_password_is_valid, save_suite_result
from ui.display import set_window_size


FROG_CONCENTRATION_UNITS = ACH_CONCENTRATION_UNITS
DEFAULT_EXAM_SECONDS = 25 * 60
DEFAULT_BATH_VOLUME_ML = 10.0

# Direct nicotinic or depolarising agonists which contract frog rectus skeletal
# muscle.  These simulator EC50 values give distinct, monotonic comparison
# curves while preserving known differences in potency and maximal response.
FROG_DRUG_MODELS = {
    "Acetylcholine chloride": {
        "molecular_weight": 181.66, "emax_mm": 50.0,
        "ec50_um": 3.96, "hill": 1.35,
    },
    "Carbachol chloride": {
        "molecular_weight": 182.65, "emax_mm": 50.0,
        "ec50_um": 1.25, "hill": 1.25,
    },
    "Nicotine": {
        "molecular_weight": 162.23, "emax_mm": 34.0,
        "ec50_um": 9.0, "hill": 1.10,
    },
    "Succinylcholine chloride": {
        "molecular_weight": 397.34, "emax_mm": 43.0,
        "ec50_um": 14.0, "hill": 1.20,
    },
}


def _finite_positive(value, field_name):
    """Return a finite positive float or raise a readable ValueError."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError("{} must be a number.".format(field_name))
    if not math.isfinite(number) or number <= 0:
        raise ValueError("{} must be more than zero.".format(field_name))
    return number


def _format_number(value):
    value = float(value)
    if value and (abs(value) < 0.001 or abs(value) >= 10000):
        return "{:.4g}".format(value)
    return "{:.5f}".format(value).rstrip("0").rstrip(".")


def _safe_filename(value):
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value).strip())
    return value.strip("._") or "student"


def frog_concentration_to_micromolar(value, unit, drug):
    """Convert a named frog agonist concentration to micromole per litre."""
    if drug not in FROG_DRUG_MODELS:
        raise ValueError("Unsupported frog rectus agonist: {}".format(drug))
    aliases = {
        "uM": "µM", "μM": "µM", "umol/L": "µM", "mol/L": "M",
        "mmol/L": "mM", "nmol/L": "nM", "ug/mL": "µg/mL",
        "mcg/mL": "µg/mL",
    }
    unit = aliases.get(str(unit).strip(), str(unit).strip())
    molecular_weight = FROG_DRUG_MODELS[drug]["molecular_weight"]
    factors = {
        "M": 1.0e6,
        "mM": 1.0e3,
        "µM": 1.0,
        "nM": 1.0e-3,
        "mg/mL": 1.0e6 / molecular_weight,
        "µg/mL": 1.0e3 / molecular_weight,
        "ng/mL": 1.0 / molecular_weight,
        "g/L": 1.0e6 / molecular_weight,
    }
    if unit not in factors:
        raise ValueError("Unsupported concentration unit: {}".format(unit))
    converted = _finite_positive(value, "Concentration") * factors[unit]
    if not math.isfinite(converted):
        raise ValueError("Concentration is outside the supported numeric range.")
    return converted


def frog_micromolar_to_concentration(value_um, unit, drug):
    """Convert micromole per litre to a selected unit for a named agonist."""
    factor = frog_concentration_to_micromolar(1.0, unit, drug)
    return _finite_positive(value_um, "Concentration") / factor


def frog_response_mm(drug, concentration_um):
    """Return deterministic frog rectus contraction height in millimetres."""
    if drug not in FROG_DRUG_MODELS:
        raise ValueError("Unsupported frog rectus agonist: {}".format(drug))
    concentration_um = _finite_positive(concentration_um, "Concentration")
    model = FROG_DRUG_MODELS[drug]
    log_ratio = model["hill"] * (
        math.log(model["ec50_um"]) - math.log(concentration_um)
    )
    if log_ratio >= 709.0:
        return 0.0
    if log_ratio <= -709.0:
        return float(model["emax_mm"])
    return model["emax_mm"] / (1.0 + math.exp(log_ratio))


def inverse_frog_response_um(drug, response_mm):
    """Estimate concentration under a selected drug identity hypothesis."""
    if drug not in FROG_DRUG_MODELS:
        raise ValueError("Unsupported frog rectus agonist: {}".format(drug))
    response_mm = _finite_positive(response_mm, "Response")
    model = FROG_DRUG_MODELS[drug]
    if response_mm >= model["emax_mm"] * 0.98:
        raise ValueError(
            "This response is too close to the maximum for a reliable estimate."
        )
    ratio = response_mm / (model["emax_mm"] - response_mm)
    return model["ec50_um"] * ratio ** (1.0 / model["hill"])


def final_bath_concentration_um(stock_value, stock_unit, dose_volume_ml,
                                bath_volume_ml=DEFAULT_BATH_VOLUME_ML):
    """Calculate final ACh concentration in a fixed organ bath.

    The conventional approximation is used: final concentration is stock
    concentration multiplied by dose volume divided by bath volume.
    """
    stock_um = ach_concentration_to_micromolar(
        _finite_positive(stock_value, "Stock concentration"), stock_unit
    )
    dose_ml = _finite_positive(dose_volume_ml, "Dose volume")
    bath_ml = _finite_positive(bath_volume_ml, "Bath volume")
    return stock_um * dose_ml / bath_ml


def interpolation_estimate(standard_points, test_response, test_fraction):
    """Public pure wrapper for the stable log-dose interpolation helper."""
    return BioassaySimulation.interpolation_estimate(
        standard_points, float(test_response), float(test_fraction)
    )


def parallel_line_estimate(standard_points, test_points):
    """Public pure wrapper for the stable parallel-line calculation helper."""
    return BioassaySimulation.parallel_line_estimate(standard_points, test_points)


def _mean_levels(records, kind, level_field):
    grouped = {}
    for record in records:
        if record.get("kind") != kind:
            continue
        level = float(record[level_field])
        grouped.setdefault(level, []).append(float(record["response_mm"]))
    return [
        (level, sum(values) / float(len(values)), len(values))
        for level, values in sorted(grouped.items())
    ]


def assisted_bioassay_calculation(records, method, emax_mm=ACH_EMAX_MM):
    """Estimate unknown ACh stock concentration from recorded observations.

    Records use ``final_bath_um`` for standards and ``dose_fraction`` for
    unknowns.  Only readings between 10 and 90 percent of Emax are accepted.
    Interpolation and three point methods require a bracketing standard pair.
    Four point analysis selects the most parallel overlapping pair and rejects
    a slope difference above 35 percent.  The result is micromole per litre.
    """
    method_key = str(method).strip().lower()
    if method_key not in ("interpolation", "three point", "four point"):
        raise ValueError("Select Interpolation, Three point, or Four point.")
    standards = _mean_levels(records, "standard", "final_bath_um")
    tests = _mean_levels(records, "unknown", "dose_fraction")
    if len(standards) < 2:
        raise ValueError("Record at least two different standard dose levels.")
    if not tests:
        raise ValueError("Record at least one unknown dose level.")

    lower_useful = float(emax_mm) * 0.10
    upper_useful = float(emax_mm) * 0.90

    def useful(point):
        return lower_useful <= point[1] <= upper_useful

    if method_key in ("interpolation", "three point"):
        candidates = []
        response_sorted = sorted(standards, key=lambda point: point[1])
        for test in tests:
            if not useful(test):
                continue
            for lower, upper in zip(response_sorted[:-1], response_sorted[1:]):
                if not useful(lower) or not useful(upper):
                    continue
                if lower[1] <= test[1] <= upper[1] and upper[1] > lower[1]:
                    candidates.append((upper[1] - lower[1], lower, upper, test))
        if not candidates:
            raise ValueError(
                "Use submaximal readings and keep the unknown response between "
                "two standard responses."
            )
        _span, lower, upper, test = min(candidates, key=lambda item: item[0])
        estimate, _used_lower, _used_upper = interpolation_estimate(
            [(lower[0], lower[1]), (upper[0], upper[1])],
            test[1], test[0],
        )
        return estimate, {
            "method": "Interpolation" if method_key == "interpolation" else "Three point",
            "standard_levels_um": [lower[0], upper[0]],
            "standard_responses_mm": [lower[1], upper[1]],
            "unknown_dose_fraction": test[0],
            "unknown_response_mm": test[1],
            "replicates": [lower[2], upper[2], test[2]],
        }

    if len(tests) < 2:
        raise ValueError("Four point assay needs two different unknown dose volumes.")
    candidates = []
    rejected_for_parallelism = False
    for standard_pair in itertools.combinations(standards, 2):
        for test_pair in itertools.combinations(tests, 2):
            standard_pair = tuple(sorted(standard_pair, key=lambda point: point[0]))
            test_pair = tuple(sorted(test_pair, key=lambda point: point[0]))
            if not all(useful(point) for point in standard_pair + test_pair):
                continue
            if standard_pair[1][1] <= standard_pair[0][1]:
                continue
            if test_pair[1][1] <= test_pair[0][1]:
                continue
            standard_interval = (standard_pair[0][1], standard_pair[1][1])
            test_interval = (test_pair[0][1], test_pair[1][1])
            overlap = min(standard_interval[1], test_interval[1]) - max(
                standard_interval[0], test_interval[0]
            )
            if overlap <= 0:
                continue
            estimate, diagnostics = parallel_line_estimate(
                [(point[0], point[1]) for point in standard_pair],
                [(point[0], point[1]) for point in test_pair],
            )
            difference = diagnostics["slope_difference_percent"]
            if difference > 35.0:
                rejected_for_parallelism = True
                continue
            candidates.append((difference, estimate, diagnostics,
                               standard_pair, test_pair))
    if not candidates:
        if rejected_for_parallelism:
            raise ValueError(
                "The selected standard and unknown lines are not sufficiently parallel. "
                "Use dose pairs in the middle response range."
            )
        raise ValueError(
            "Four point assay needs two increasing standard levels and two increasing "
            "unknown levels with overlapping submaximal responses."
        )
    _difference, estimate, diagnostics, standard_pair, test_pair = min(
        candidates, key=lambda item: item[0]
    )
    result_diagnostics = dict(diagnostics)
    result_diagnostics.update({
        "method": "Four point",
        "standard_levels_um": [point[0] for point in standard_pair],
        "standard_responses_mm": [point[1] for point in standard_pair],
        "unknown_dose_fractions": [point[0] for point in test_pair],
        "unknown_responses_mm": [point[1] for point in test_pair],
        "replicates": [point[2] for point in standard_pair + test_pair],
    })
    return estimate, result_diagnostics


class _OrganBathDiagram(tk.Canvas):
    """Small responsive, coloured organ-bath illustration."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("height", 185)
        kwargs.setdefault("background", "#f6fbff")
        kwargs.setdefault("highlightthickness", 1)
        kwargs.setdefault("highlightbackground", "#cbd8e2")
        tk.Canvas.__init__(self, master, **kwargs)
        self.response_percent = 0.0
        self.solution_label = "Frog Ringer solution"
        self.washed = True
        self.bind("<Configure>", self._draw)

    def set_state(self, response_percent, solution_label, washed):
        self.response_percent = max(0.0, min(100.0, float(response_percent)))
        self.solution_label = str(solution_label)
        self.washed = bool(washed)
        self._draw()

    def _draw(self, _event=None):
        self.delete("all")
        width = max(250, self.winfo_width())
        height = max(175, self.winfo_height())
        left, right = width * 0.14, width * 0.86
        top, bottom = height * 0.30, height * 0.78
        centre = width / 2.0
        lever_y = top - 25
        tilt = self.response_percent * 0.035
        self.create_text(centre, 9, text="Frog rectus organ bath",
                         anchor="n", fill="#173b57",
                         font=("Segoe UI", 10, "bold"))
        self.create_line(centre - 70, lever_y + tilt, centre + 70,
                         lever_y - tilt, fill="#46515a", width=3)
        self.create_oval(centre - 4, lever_y - 4, centre + 4, lever_y + 4,
                         fill="#aeb8bf", outline="#46515a")
        water_top = top + 9
        self.create_rectangle(left + 2, water_top, right - 2, bottom - 2,
                              fill="#dcefff" if self.washed else "#dff3e4",
                              outline="")
        self.create_line(left, top, left, bottom, right, bottom, right, top,
                         fill="#5d91bd", width=3)
        muscle_top = water_top + 13
        shortening = (bottom - water_top) * 0.22 * self.response_percent / 100.0
        muscle_bottom = bottom - 18 - shortening
        self.create_line(centre, lever_y + 4, centre, muscle_top,
                         fill="#68747d", dash=(4, 3))
        self.create_rectangle(centre - 12, muscle_top, centre + 12,
                              muscle_bottom, fill="#f08080",
                              outline="#c94f5b", width=2)
        stripe_y = muscle_top + 5
        while stripe_y < muscle_bottom:
            self.create_line(centre - 9, stripe_y, centre + 9, stripe_y,
                             fill="#dc606b")
            stripe_y += 6
        self.create_line(centre, muscle_bottom, centre, bottom + 4,
                         fill="#68747d", width=2)
        for index in range(5):
            bubble_y = bottom - 14 - index * 14
            self.create_oval(right - 18, bubble_y, right - 13, bubble_y + 5,
                             outline="#8abfe6")
        self.create_text(centre + 19, (muscle_top + muscle_bottom) / 2.0,
                         text="Rectus abdominis", anchor="w", fill="#425d74",
                         font=("Segoe UI", 8))
        state = "Washed and ready" if self.washed else self.solution_label
        self.create_text(centre, bottom + 10, text=state, anchor="n",
                         fill="#237032" if self.washed else "#a13d2d",
                         font=("Segoe UI", 8, "bold"), width=width - 25)


class _RetainedKymograph(tk.Frame):
    """Matplotlib kymograph which retains and horizontally scrolls all doses."""

    SEGMENT_SECONDS = 20.0
    WINDOW_SECONDS = 80.0

    def __init__(self, master):
        tk.Frame.__init__(self, master, bg="white")
        self.records = []
        self.view_start = 0.0
        self.show_all = False
        # Keep the observation log visible at the 760 by 520 laptop profile.
        # The graph expands naturally when more screen space is available.
        self.figure = Figure(figsize=(7.2, 2.35), dpi=100)
        self.axis = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        bar = tk.Frame(self, bg="white")
        bar.pack(fill="x", padx=7, pady=(0, 4))
        self.scrollbar = ttk.Scrollbar(bar, orient="horizontal",
                                      command=self._on_scroll)
        self.scrollbar.pack(side="left", fill="x", expand=True)
        self.toggle_button = tk.Button(
            bar, text="Show all", command=self.toggle_show_all,
            font=("Segoe UI", 8, "bold"), bg="#e7eef4", fg="#173b57",
            padx=8, pady=2,
        )
        self.toggle_button.pack(side="left", padx=(8, 0))
        self.redraw()

    @property
    def total_seconds(self):
        return max(self.WINDOW_SECONDS,
                   len(self.records) * self.SEGMENT_SECONDS + 4.0)

    def clear(self):
        self.records = []
        self.view_start = 0.0
        self.show_all = False
        self.toggle_button.configure(text="Show all")
        self.redraw()

    def add_record(self, record):
        stored = dict(record)
        stored["trace_start"] = len(self.records) * self.SEGMENT_SECONDS
        self.records.append(stored)
        self.show_all = False
        self.toggle_button.configure(text="Show all")
        self.view_start = max(0.0, self.total_seconds - self.WINDOW_SECONDS)
        self.redraw()

    def toggle_show_all(self):
        self.show_all = not self.show_all
        self.toggle_button.configure(
            text="Window view" if self.show_all else "Show all"
        )
        if not self.show_all:
            self.view_start = max(0.0, self.total_seconds - self.WINDOW_SECONDS)
        self.redraw()

    def _on_scroll(self, *args):
        if not args or self.total_seconds <= self.WINDOW_SECONDS:
            return
        self.show_all = False
        self.toggle_button.configure(text="Show all")
        maximum = max(0.0, self.total_seconds - self.WINDOW_SECONDS)
        if args[0] == "moveto":
            self.view_start = max(0.0, min(maximum,
                                           float(args[1]) * self.total_seconds))
        elif args[0] == "scroll":
            amount = int(args[1])
            step = 5.0 if args[2] == "units" else self.WINDOW_SECONDS * 0.8
            self.view_start = max(0.0, min(maximum,
                                           self.view_start + amount * step))
        self.redraw()

    @staticmethod
    def _trace_arrays(record):
        local = np.linspace(0.0, _RetainedKymograph.SEGMENT_SECONDS, 240)
        peak = float(record["response_mm"])
        rise = 1.0 / (1.0 + np.exp(-(local - 3.1) * 2.0))
        fall = 1.0 / (1.0 + np.exp((local - 12.2) * 1.2))
        response = peak * rise * fall
        response -= response[0]
        response = np.maximum(response, 0.0)
        start = float(record.get("trace_start", 0.0))
        return local + start, response

    def draw_on_axis(self, axis, full_trace=True):
        axis.clear()
        if not self.records:
            axis.text(0.5, 0.5, "No contraction recorded",
                      transform=axis.transAxes, ha="center", va="center",
                      color="#607789", fontsize=11)
        for index, record in enumerate(self.records):
            x_values, y_values = self._trace_arrays(record)
            color = "#7b2cbf" if record.get("kind") == "unknown" else "#d1495b"
            axis.plot(x_values, y_values, color=color, linewidth=2.0)
            start = float(record["trace_start"])
            axis.plot([start + 1.0], [0.0], marker="v", color="#173b57",
                      markersize=6)
            peak_index = int(np.argmax(y_values))
            label = "{}  {}\n{} mm".format(
                index + 1, record["label"],
                _format_number(record["response_mm"]),
            )
            axis.annotate(
                label, xy=(x_values[peak_index], y_values[peak_index]),
                xytext=(0, 7 + (index % 2) * 12), textcoords="offset points",
                ha="center", va="bottom", fontsize=7,
                color="#4b244a" if record.get("kind") == "unknown" else "#762a35",
                arrowprops=dict(arrowstyle="-", color="#9aa9b5", lw=0.7),
            )
        axis.axhline(0.0, color="#607789", linewidth=0.8)
        axis.set_xlabel("Time (seconds)")
        axis.set_ylabel("Contraction height (mm)")
        axis.set_title("Continuous frog rectus kymograph")
        axis.set_ylim(-1.0, max(55.0, max(
            [float(record["response_mm"]) for record in self.records] or [50.0]
        ) * 1.35))
        axis.grid(True, color="#d9e4ec", linewidth=0.6, alpha=0.8)
        total = self.total_seconds
        if full_trace or self.show_all or total <= self.WINDOW_SECONDS:
            axis.set_xlim(0.0, total)
        else:
            axis.set_xlim(self.view_start, self.view_start + self.WINDOW_SECONDS)

    def redraw(self):
        self.draw_on_axis(self.axis, full_trace=False)
        total = self.total_seconds
        if self.show_all or total <= self.WINDOW_SECONDS:
            self.scrollbar.set(0.0, 1.0)
        else:
            first = self.view_start / total
            last = min(1.0, (self.view_start + self.WINDOW_SECONDS) / total)
            self.scrollbar.set(first, last)
        self.figure.tight_layout(pad=1.0)
        self.canvas.draw_idle()


class _BaseUnknownPractical:
    """Responsive exam shell shared by both quantitative practicals."""

    title = "Quantitative Practical"
    subtitle = "Examiner-configured student practical"
    experiment_name = "Quantitative practical"
    NAVY = "#173b57"
    BLUE = "#1769aa"
    GREEN = "#237032"
    RED = "#a13d2d"
    PURPLE = "#6a3d8f"
    BG = "#eef4f8"
    TEXT = "#20394d"
    MUTED = "#607789"

    def __init__(self, master, level="PG", exam_seconds=None, configuration=None):
        self.master = master
        self.level = str(level).upper()
        self.exam_seconds = int(exam_seconds or DEFAULT_EXAM_SECONDS)
        if self.exam_seconds <= 0:
            raise ValueError("exam_seconds must be more than zero.")
        self.seconds_left = self.exam_seconds
        self.timer_job = None
        self.exam_in_progress = False
        self.student_name = ""
        self.roll_number = ""
        self.records = []
        self.ready_for_dose = True
        self.configuration = None
        if configuration is not None:
            self.configuration = self._validate_configuration(configuration)
        self.master.title("{} - {}".format(self.title, self.level))
        set_window_size(
            self.master, 1280, 790, 760, 520,
            margin_x=36, margin_y=70, expand_large=True,
        )
        self.master.configure(bg=self.BG)
        self.master.protocol("WM_DELETE_WINDOW", self.close)
        self.show_start_screen()

    def _validate_configuration(self, configuration):
        raise NotImplementedError

    def _clear_window(self):
        for widget in self.master.winfo_children():
            widget.destroy()

    def show_start_screen(self):
        self.cancel_timer()
        self.exam_in_progress = False
        self._clear_window()
        header = tk.Frame(self.master, bg=self.NAVY, padx=20, pady=13)
        header.pack(fill="x")
        title_label = tk.Label(
            header, text=self.title, font=("Segoe UI", 20, "bold"),
            bg=self.NAVY, fg="white", justify="left", anchor="w",
        )
        title_label.pack(fill="x")
        subtitle_label = tk.Label(
            header, text=self.subtitle, font=("Segoe UI", 9),
            bg=self.NAVY, fg="#cfe2f3", justify="left", anchor="w",
        )
        subtitle_label.pack(fill="x", pady=(2, 0))

        def wrap_header(event):
            wrap = max(260, event.width - 40)
            title_label.configure(wraplength=wrap)
            subtitle_label.configure(wraplength=wrap)

        header.bind("<Configure>", wrap_header)
        outer = tk.Frame(self.master, bg=self.BG)
        outer.pack(fill="both", expand=True, padx=12, pady=12)
        card = tk.Frame(
            outer, bg="white", padx=34, pady=22,
            highlightbackground="#cbd8e2", highlightthickness=1,
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(card, text="STUDENT ENTRY", font=("Segoe UI", 10, "bold"),
                 bg="white", fg=self.MUTED).pack(pady=(0, 10))
        form = tk.Frame(card, bg="white")
        form.pack(fill="x")
        tk.Label(form, text="Student name", font=("Segoe UI", 10, "bold"),
                 bg="white", fg=self.TEXT).grid(row=0, column=0, sticky="w", pady=5)
        self.name_entry = tk.Entry(form, width=30, font=("Segoe UI", 10))
        self.name_entry.grid(row=0, column=1, padx=(14, 0), pady=5, sticky="ew")
        tk.Label(form, text="Roll number", font=("Segoe UI", 10, "bold"),
                 bg="white", fg=self.TEXT).grid(row=1, column=0, sticky="w", pady=5)
        self.roll_entry = tk.Entry(form, width=30, font=("Segoe UI", 10))
        self.roll_entry.grid(row=1, column=1, padx=(14, 0), pady=5, sticky="ew")
        form.grid_columnconfigure(1, weight=1)
        ready = self.configuration is not None
        tk.Label(
            card,
            text=("Practical ready. The unknown has been configured."
                  if ready else "Examiner setup is required before the student can begin."),
            font=("Segoe UI", 9, "bold"),
            bg="#eef7f0" if ready else "#fff3f0",
            fg=self.GREEN if ready else self.RED,
            padx=13, pady=8,
        ).pack(fill="x", pady=(14, 6))
        tk.Label(
            card,
            text="{} minutes  |  Unlimited observations  |  answer and marks remain hidden"
                 .format(self.exam_seconds // 60),
            font=("Segoe UI", 9), bg="#f4f8fb", fg=self.MUTED,
            padx=13, pady=8, wraplength=470, justify="center",
        ).pack(fill="x", pady=(0, 14))
        buttons = tk.Frame(card, bg="white")
        buttons.pack()
        tk.Button(
            buttons, text="Start Practical", command=self.start_practical,
            state="normal" if ready else "disabled",
            font=("Segoe UI", 10, "bold"), bg=self.BLUE, fg="white",
            disabledforeground="#d7e1e8", padx=18, pady=7,
        ).pack(side="left", padx=5)
        tk.Button(
            buttons, text="Examiner Setup", command=self.open_examiner_setup,
            font=("Segoe UI", 10, "bold"), bg=self.PURPLE, fg="white",
            padx=18, pady=7,
        ).pack(side="left", padx=5)
        self.name_entry.focus_set()

    def open_examiner_setup(self):
        if examiner_password_is_valid(self.master):
            self._build_examiner_setup()

    def _build_examiner_setup(self):
        raise NotImplementedError

    def start_practical(self):
        name = self.name_entry.get().strip()
        roll = self.roll_entry.get().strip()
        if self.configuration is None:
            messagebox.showwarning(
                "Examiner setup", "The examiner must configure the unknown first.",
                parent=self.master,
            )
            return
        if not name or not roll:
            messagebox.showwarning(
                "Student details", "Enter both student name and roll number.",
                parent=self.master,
            )
            return
        self.student_name = name
        self.roll_number = roll
        self.seconds_left = self.exam_seconds
        self.records = []
        self.ready_for_dose = True
        self.exam_in_progress = True
        self._build_exam_screen()
        self.update_timer()

    def _build_exam_screen(self):
        self._clear_window()
        header = tk.Frame(self.master, bg=self.NAVY, padx=11, pady=7)
        header.pack(fill="x")
        left = tk.Frame(header, bg=self.NAVY)
        left.pack(side="left", fill="x", expand=True)
        self.exam_title_label = tk.Label(
            left, text="{}  |  {}".format(self.title, self.level),
            font=("Segoe UI", 11, "bold"), bg=self.NAVY, fg="white",
            anchor="w", justify="left",
        )
        self.exam_title_label.pack(fill="x")
        tk.Label(
            left, text="{}  |  Roll No. {}".format(self.student_name, self.roll_number),
            font=("Segoe UI", 8), bg=self.NAVY, fg="#cfe2f3", anchor="w",
        ).pack(fill="x")
        right = tk.Frame(header, bg=self.NAVY)
        right.pack(side="right")
        tk.Button(
            right, text="Save Image", command=self.save_image,
            font=("Segoe UI", 8, "bold"), bg="#f0ad4e", fg="#182b3a",
            padx=8, pady=4,
        ).pack(side="left", padx=4)
        tk.Button(
            right, text="Submit", command=self.submit_practical,
            font=("Segoe UI", 8, "bold"), bg=self.RED, fg="white",
            padx=9, pady=4,
        ).pack(side="left", padx=4)
        self.timer_label = tk.Label(
            right, text="", font=("Segoe UI", 11, "bold"),
            bg=self.NAVY, fg="#ffd166", width=7,
        )
        self.timer_label.pack(side="left", padx=(6, 0))
        header.bind(
            "<Configure>",
            lambda event: self.exam_title_label.configure(
                wraplength=max(180, event.width - 285)
            ),
        )

        body = tk.PanedWindow(
            self.master, orient="horizontal", bg="#d5e0e8", bd=0,
            sashwidth=7, sashrelief="flat",
        )
        body.pack(fill="both", expand=True, padx=9, pady=8)
        controls_card = tk.Frame(
            body, bg="white", highlightbackground="#cbd8e2",
            highlightthickness=1,
        )
        body.add(controls_card, minsize=270, width=315)
        controls_canvas = tk.Canvas(
            controls_card, bg="white", highlightthickness=0, width=315,
        )
        controls_scroll = ttk.Scrollbar(
            controls_card, orient="vertical", command=controls_canvas.yview,
        )
        controls_canvas.configure(yscrollcommand=controls_scroll.set)
        controls_scroll.pack(side="right", fill="y")
        controls_canvas.pack(side="left", fill="both", expand=True)
        controls = tk.Frame(controls_canvas, bg="white", padx=13, pady=10)
        controls_window = controls_canvas.create_window(
            (0, 0), window=controls, anchor="nw"
        )
        controls.bind(
            "<Configure>",
            lambda _event: controls_canvas.configure(
                scrollregion=controls_canvas.bbox("all")
            ),
        )
        controls_canvas.bind(
            "<Configure>",
            lambda event: controls_canvas.itemconfigure(
                controls_window, width=max(1, event.width)
            ),
        )
        self.controls_canvas = controls_canvas
        self.controls_frame = controls
        self.organ_bath = _OrganBathDiagram(controls)
        self.organ_bath.pack(fill="x", pady=(0, 10))
        self._build_controls(controls)

        scroll_tag = "QuantitativeControls{}".format(id(self))

        def scroll_controls(event):
            controls_canvas.yview_scroll(int(-event.delta / 120), "units")

        controls_canvas.bind_class(scroll_tag, "<MouseWheel>", scroll_controls)

        def attach_scroll_tag(widget):
            tags = list(widget.bindtags())
            if scroll_tag not in tags:
                tags.insert(max(len(tags) - 1, 0), scroll_tag)
                widget.bindtags(tuple(tags))
            for child in widget.winfo_children():
                attach_scroll_tag(child)

        attach_scroll_tag(controls_canvas)

        workspace = tk.Frame(body, bg=self.BG)
        body.add(workspace, minsize=390)
        graph_card = tk.Frame(
            workspace, bg="white", highlightbackground="#cbd8e2",
            highlightthickness=1,
        )
        graph_card.pack(fill="both", expand=True)
        self.kymograph = _RetainedKymograph(graph_card)
        self.kymograph.pack(fill="both", expand=True)
        log_card = tk.Frame(
            workspace, bg="white", padx=7, pady=6,
            highlightbackground="#cbd8e2", highlightthickness=1,
        )
        log_card.pack(fill="x", pady=(6, 0))
        log_top = tk.Frame(log_card, bg="white")
        log_top.pack(fill="x", pady=(0, 4))
        tk.Label(log_top, text="Labelled Observation Log",
                 font=("Segoe UI", 9, "bold"), bg="white",
                 fg=self.NAVY).pack(side="left")
        self.status_label = tk.Label(
            log_top, text="Bath washed and ready", font=("Segoe UI", 8, "bold"),
            bg="white", fg=self.GREEN,
        )
        self.status_label.pack(side="right")
        table_frame = tk.Frame(log_card, bg="white")
        table_frame.pack(fill="x")
        columns, headings, widths = self._observation_columns()
        self.observation_table = ttk.Treeview(
            table_frame, columns=columns, show="headings", height=3,
        )
        for column in columns:
            self.observation_table.heading(column, text=headings[column])
            self.observation_table.column(
                column, width=widths.get(column, 100), minwidth=65,
                anchor="center", stretch=True,
            )
        vertical = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.observation_table.yview,
        )
        horizontal = ttk.Scrollbar(
            table_frame, orient="horizontal", command=self.observation_table.xview,
        )
        self.observation_table.configure(
            yscrollcommand=vertical.set, xscrollcommand=horizontal.set
        )
        self.observation_table.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        table_frame.grid_columnconfigure(0, weight=1)
        self.organ_bath.set_state(0.0, "Frog Ringer solution", True)

    def _section_title(self, parent, text):
        tk.Label(
            parent, text=text, font=("Segoe UI", 9, "bold"),
            bg="white", fg=self.MUTED,
        ).pack(anchor="w", pady=(8, 4))

    def _build_controls(self, parent):
        raise NotImplementedError

    def _observation_columns(self):
        raise NotImplementedError

    def _observation_values(self, record):
        raise NotImplementedError

    def _record(self, record):
        stored = dict(record)
        stored["trial"] = len(self.records) + 1
        stored["response_mm"] = float(stored["response_mm"])
        self.records.append(stored)
        self.ready_for_dose = False
        self.kymograph.add_record(stored)
        self.observation_table.insert("", "end",
                                      values=self._observation_values(stored))
        children = self.observation_table.get_children()
        if children:
            self.observation_table.see(children[-1])
        response_percent = min(100.0, stored["response_mm"] / 50.0 * 100.0)
        self.organ_bath.set_state(
            response_percent, stored.get("bath_label", stored["label"]), False
        )
        self.status_label.configure(
            text="Dose recorded. Wash before next dose.", fg=self.RED
        )

    def require_washed_bath(self):
        if not self.ready_for_dose:
            messagebox.showwarning(
                "Wash required",
                "Wash the tissue and allow the baseline to return before the next dose.",
                parent=self.master,
            )
            return False
        return True

    def wash_tissue(self):
        self.ready_for_dose = True
        self.organ_bath.set_state(0.0, "Frog Ringer solution", True)
        self.status_label.configure(text="Bath washed and ready", fg=self.GREEN)

    def reset_observations(self):
        if self.records and not messagebox.askyesno(
                "Reset observations", "Remove all observations from this practical?",
                parent=self.master):
            return
        self.records = []
        self.ready_for_dose = True
        self.kymograph.clear()
        for item in self.observation_table.get_children():
            self.observation_table.delete(item)
        self.organ_bath.set_state(0.0, "Frog Ringer solution", True)
        self.status_label.configure(text="Bath washed and ready", fg=self.GREEN)
        self._after_reset()

    def _after_reset(self):
        pass

    def update_timer(self):
        if not self.exam_in_progress:
            return
        minutes, seconds = divmod(max(0, self.seconds_left), 60)
        self.timer_label.configure(text="{:02d}:{:02d}".format(minutes, seconds))
        if self.seconds_left <= 0:
            self.submit_practical(timed_out=True)
            return
        self.seconds_left -= 1
        self.timer_job = self.master.after(1000, self.update_timer)

    def cancel_timer(self):
        if self.timer_job is not None:
            try:
                self.master.after_cancel(self.timer_job)
            except tk.TclError:
                pass
            self.timer_job = None

    def _answer_is_blank(self):
        raise NotImplementedError

    def _score_and_details(self):
        raise NotImplementedError

    def submit_practical(self, timed_out=False):
        if not self.exam_in_progress:
            return
        if not timed_out:
            if self._answer_is_blank():
                if not messagebox.askyesno(
                        "Submit practical", "The final answer is incomplete. Submit now?",
                        parent=self.master):
                    return
            elif not messagebox.askyesno(
                    "Submit practical", "Submit your final answer? It cannot be changed.",
                    parent=self.master):
                return
        self.cancel_timer()
        score, total, details = self._score_and_details()
        duration = self.exam_seconds - max(0, self.seconds_left)
        storage_error = None
        try:
            save_suite_result(
                self.experiment_name, self.level, self.student_name,
                self.roll_number, int(score), int(total), int(duration), details,
            )
        except Exception as error:
            storage_error = str(error)
        self.exam_in_progress = False
        self._show_submission_screen(bool(timed_out), storage_error)

    def _show_submission_screen(self, timed_out, storage_error):
        self._clear_window()
        card = tk.Frame(
            self.master, bg="white", padx=42, pady=30,
            highlightbackground="#cbd8e2", highlightthickness=1,
        )
        card.place(relx=0.5, rely=0.48, anchor="center")
        tk.Label(card, text="Practical Submitted",
                 font=("Segoe UI", 22, "bold"), bg="white",
                 fg=self.GREEN).pack(pady=(0, 10))
        tk.Label(
            card,
            text="{}  |  Roll No. {}\n{}".format(
                self.student_name, self.roll_number, self.title
            ),
            font=("Segoe UI", 11), bg="white", fg=self.TEXT,
            justify="center",
        ).pack(pady=6)
        message = (
            "Time expired. The available final answer was submitted."
            if timed_out else "The final answer was saved successfully."
        )
        message += "\nThe correct answer and marks are visible only to the examiner."
        if storage_error:
            message += "\n\nThe local result could not be saved. Please inform the examiner."
        tk.Label(
            card, text=message, font=("Segoe UI", 10),
            bg="#f4f8fb", fg=self.MUTED, justify="center",
            wraplength=520, padx=18, pady=12,
        ).pack(pady=12)
        buttons = tk.Frame(card, bg="white")
        buttons.pack()
        tk.Button(
            buttons, text="Save Result Image", command=self.save_image,
            bg="#f0ad4e", fg="#182b3a", font=("Segoe UI", 9, "bold"),
            padx=13, pady=7,
        ).pack(side="left", padx=5)
        tk.Button(
            buttons, text="New Student", command=self.show_start_screen,
            bg=self.BLUE, fg="white", font=("Segoe UI", 9, "bold"),
            padx=13, pady=7,
        ).pack(side="left", padx=5)
        tk.Button(
            buttons, text="Close", command=self.master.destroy,
            bg="#6c757d", fg="white", font=("Segoe UI", 9),
            padx=13, pady=7,
        ).pack(side="left", padx=5)

    def _summary_title(self):
        return self.title

    def _draw_summary(self, axis):
        raise NotImplementedError

    def save_image(self):
        if not self.records:
            messagebox.showwarning(
                "Save image", "Record at least one response before saving an image.",
                parent=self.master,
            )
            return
        initial = "{}_{}_result.png".format(
            _safe_filename(self.experiment_name), _safe_filename(self.roll_number)
        )
        path = filedialog.asksaveasfilename(
            parent=self.master, title="Save labelled practical result",
            defaultextension=".png", initialfile=initial,
            filetypes=(("PNG image", "*.png"),),
        )
        if not path:
            return
        figure_height = max(9.0, 7.5 + len(self.records) * 0.18)
        figure = Figure(figsize=(15.5, figure_height), dpi=150)
        grid = figure.add_gridspec(2, 2, height_ratios=(1.45, 1.0),
                                   width_ratios=(1.05, 0.95))
        trace_axis = figure.add_subplot(grid[0, :])
        summary_axis = figure.add_subplot(grid[1, 0])
        table_axis = figure.add_subplot(grid[1, 1])
        temporary = object.__new__(_RetainedKymograph)
        temporary.records = []
        for index, record in enumerate(self.records):
            stored = dict(record)
            stored["trace_start"] = index * _RetainedKymograph.SEGMENT_SECONDS
            temporary.records.append(stored)
        temporary.view_start = 0.0
        temporary.show_all = True
        _RetainedKymograph.draw_on_axis(temporary, trace_axis, full_trace=True)
        self._draw_summary(summary_axis)
        table_axis.axis("off")
        columns, headings, _widths = self._observation_columns()
        rows = [list(self._observation_values(record)) for record in self.records]
        table = table_axis.table(
            cellText=rows, colLabels=[headings[column] for column in columns],
            loc="center", cellLoc="center"
        )
        table.auto_set_font_size(False)
        table.set_fontsize(7.2)
        table.scale(1.0, 1.18)
        table_axis.set_title("Recorded observations", fontsize=11, pad=8)
        figure.suptitle(
            "{}\nStudent: {}    Roll No.: {}    Level: {}".format(
                self._summary_title(), self.student_name,
                self.roll_number, self.level,
            ),
            fontsize=15, fontweight="bold", color=self.NAVY,
        )
        figure.tight_layout(rect=(0.02, 0.02, 0.98, 0.93))
        try:
            figure.savefig(path, dpi=150, facecolor="white")
        except (OSError, ValueError) as error:
            messagebox.showerror(
                "Save image", "Could not save the image:\n{}".format(error),
                parent=self.master,
            )
            return
        messagebox.showinfo(
            "Image saved", "Labelled result saved as:\n{}".format(os.path.normpath(path)),
            parent=self.master,
        )

    def close(self):
        if self.exam_in_progress and not messagebox.askyesno(
                "Close practical", "The practical is incomplete. Close without submitting?",
                parent=self.master):
            return
        self.cancel_timer()
        self.master.destroy()


class FrogRectusUnknownPractical(_BaseUnknownPractical):
    """Unknown frog rectus agonist identity and concentration practical.

    Constructor API::

        FrogRectusUnknownPractical(master, level="PG", exam_seconds=None,
                                    configuration=None)

    ``configuration`` may contain ``drug``, ``concentration``, and ``unit`` or
    the internal ``concentration_um``.  Without it, the examiner uses the
    password-protected setup page before the first student.
    """

    title = "Frog Rectus Unknown Agonist Practical"
    subtitle = (
        "Compare a hidden nicotinic agonist with known concentration-response "
        "observations and identify its concentration"
    )
    experiment_name = "Frog Rectus Unknown Agonist"

    def _validate_configuration(self, configuration):
        if not isinstance(configuration, dict):
            raise ValueError("Frog configuration must be a dictionary.")
        drug = str(configuration.get("drug", "")).strip()
        if drug not in FROG_DRUG_MODELS:
            raise ValueError("Select a supported frog rectus agonist.")
        if "concentration_um" in configuration:
            concentration_um = _finite_positive(
                configuration["concentration_um"], "Unknown concentration"
            )
        else:
            concentration_um = frog_concentration_to_micromolar(
                configuration.get("concentration"),
                configuration.get("unit", "µM"), drug,
            )
        return {"drug": drug, "concentration_um": concentration_um}

    def _build_examiner_setup(self):
        setup = tk.Toplevel(self.master)
        setup.title("Examiner Setup - Frog Rectus Unknown")
        set_window_size(setup, 555, 395, 500, 360)
        setup.configure(bg=self.BG)
        setup.transient(self.master)
        setup.grab_set()
        header = tk.Frame(setup, bg=self.NAVY, padx=17, pady=11)
        header.pack(fill="x")
        tk.Label(header, text="Configure Hidden Frog Rectus Agonist",
                 font=("Segoe UI", 16, "bold"), bg=self.NAVY,
                 fg="white").pack(anchor="w")
        tk.Label(header, text="Identity and concentration remain hidden from the student",
                 font=("Segoe UI", 9), bg=self.NAVY,
                 fg="#cfe2f3").pack(anchor="w")
        body = tk.Frame(setup, bg="white", padx=25, pady=20,
                        highlightbackground="#cbd8e2", highlightthickness=1)
        body.pack(fill="both", expand=True, padx=16, pady=16)
        current = self.configuration or {
            "drug": "Acetylcholine chloride", "concentration_um": 4.0
        }
        drug_var = tk.StringVar(value=current["drug"])
        concentration_var = tk.StringVar(value=_format_number(
            frog_micromolar_to_concentration(
                current["concentration_um"], "µM", current["drug"]
            )
        ))
        unit_var = tk.StringVar(value="µM")
        tk.Label(body, text="Unknown agonist", font=("Segoe UI", 10, "bold"),
                 bg="white", fg=self.TEXT).grid(row=0, column=0, sticky="w", pady=7)
        ttk.Combobox(body, textvariable=drug_var,
                     values=tuple(FROG_DRUG_MODELS.keys()), state="readonly",
                     width=29).grid(row=0, column=1, columnspan=2,
                                    sticky="ew", padx=(14, 0), pady=7)
        tk.Label(body, text="Unknown concentration",
                 font=("Segoe UI", 10, "bold"), bg="white",
                 fg=self.TEXT).grid(row=1, column=0, sticky="w", pady=7)
        tk.Entry(body, textvariable=concentration_var, width=16).grid(
            row=1, column=1, sticky="ew", padx=(14, 5), pady=7
        )
        ttk.Combobox(body, textvariable=unit_var,
                     values=FROG_CONCENTRATION_UNITS, state="readonly",
                     width=10).grid(row=1, column=2, sticky="ew", pady=7)
        tk.Label(
            body,
            text="Use a concentration which gives a measurable, preferably middle-range response. "
                 "Molar and mass concentration units are accepted.",
            font=("Segoe UI", 9), bg="#fff8e1", fg="#6b5a20",
            justify="left", wraplength=440, padx=10, pady=8,
        ).grid(row=2, column=0, columnspan=3, sticky="ew", pady=(8, 13))

        def save_setup():
            try:
                configuration = self._validate_configuration({
                    "drug": drug_var.get(),
                    "concentration": concentration_var.get(),
                    "unit": unit_var.get(),
                })
                response = frog_response_mm(
                    configuration["drug"], configuration["concentration_um"]
                )
            except ValueError as error:
                messagebox.showwarning("Unknown setup", str(error), parent=setup)
                return
            if response < 5.0 or response > 46.0:
                if not messagebox.askyesno(
                        "Extreme response",
                        "This setting gives {:.1f} mm contraction. A middle-range response "
                        "is easier to compare. Save it anyway?".format(response),
                        parent=setup):
                    return
            self.configuration = configuration
            messagebox.showinfo(
                "Practical configured",
                "Unknown: {}\nConcentration: {} µM\nExpected height: {:.2f} mm\n\n"
                "These values will remain hidden on the student screen.".format(
                    configuration["drug"],
                    _format_number(configuration["concentration_um"]), response,
                ), parent=setup,
            )
            setup.destroy()
            self.show_start_screen()

        tk.Button(body, text="Save Hidden Unknown", command=save_setup,
                  font=("Segoe UI", 10, "bold"), bg=self.GREEN, fg="white",
                  padx=18, pady=7).grid(row=3, column=0, columnspan=3)
        body.grid_columnconfigure(1, weight=1)

    def _build_controls(self, parent):
        self._section_title(parent, "KNOWN COMPARISON")
        tk.Label(
            parent,
            text="Enter any concentration and unit. The value is the final bath concentration.",
            font=("Segoe UI", 8), bg="#f4f8fb", fg=self.MUTED,
            justify="left", wraplength=265, padx=7, pady=6,
        ).pack(fill="x", pady=(0, 5))
        self.known_drug_var = tk.StringVar(value="Acetylcholine chloride")
        ttk.Combobox(
            parent, textvariable=self.known_drug_var,
            values=tuple(FROG_DRUG_MODELS.keys()), state="readonly",
        ).pack(fill="x", pady=2)
        dose_row = tk.Frame(parent, bg="white")
        dose_row.pack(fill="x", pady=3)
        self.known_concentration_var = tk.StringVar(value="4")
        tk.Entry(dose_row, textvariable=self.known_concentration_var,
                 width=13).pack(side="left", fill="x", expand=True)
        self.known_unit_var = tk.StringVar(value="µM")
        ttk.Combobox(
            dose_row, textvariable=self.known_unit_var,
            values=FROG_CONCENTRATION_UNITS, state="readonly", width=9,
        ).pack(side="left", padx=(5, 0))
        tk.Button(
            parent, text="Add Known Drug to Bath", command=self.add_known,
            font=("Segoe UI", 9, "bold"), bg=self.BLUE, fg="white", pady=6,
        ).pack(fill="x", pady=(3, 7))

        self._section_title(parent, "HIDDEN TEST SOLUTION")
        tk.Label(
            parent, text="Dilution fraction of unknown stock",
            font=("Segoe UI", 8, "bold"), bg="white", fg=self.TEXT,
        ).pack(anchor="w")
        self.unknown_fraction_var = tk.StringVar(value="1")
        tk.Entry(parent, textvariable=self.unknown_fraction_var).pack(
            fill="x", pady=(2, 2)
        )
        tk.Label(
            parent,
            text="Use 1 for full stock, 0.5 for half strength or another fraction up to 1.",
            font=("Segoe UI", 8), bg="#f3ebff", fg="#513274",
            justify="left", wraplength=265, padx=7, pady=5,
        ).pack(fill="x", pady=(0, 5))
        tk.Button(
            parent, text="Add Unknown to Bath", command=self.add_unknown,
            font=("Segoe UI", 9, "bold"), bg=self.PURPLE, fg="white", pady=7,
        ).pack(fill="x", pady=(0, 6))
        tk.Button(
            parent, text="Wash Tissue", command=self.wash_tissue,
            font=("Segoe UI", 9, "bold"), bg=self.GREEN, fg="white", pady=6,
        ).pack(fill="x", pady=2)
        tk.Button(
            parent, text="Reset All Observations", command=self.reset_observations,
            font=("Segoe UI", 8, "bold"), bg="#6c757d", fg="white", pady=5,
        ).pack(fill="x", pady=(2, 7))

        self._section_title(parent, "ASSISTED ESTIMATE")
        tk.Label(
            parent,
            text="Choose an identity hypothesis. The estimate does not confirm whether the identity is correct.",
            font=("Segoe UI", 8), bg="#fff8e1", fg="#6b5a20",
            justify="left", wraplength=265, padx=7, pady=6,
        ).pack(fill="x")
        self.hypothesis_var = tk.StringVar(value="Acetylcholine chloride")
        ttk.Combobox(
            parent, textvariable=self.hypothesis_var,
            values=tuple(FROG_DRUG_MODELS.keys()), state="readonly",
        ).pack(fill="x", pady=4)
        tk.Button(
            parent, text="Calculate Under This Hypothesis",
            command=self.calculate_assisted_estimate,
            font=("Segoe UI", 8, "bold"), bg="#d49b16", fg="#182b3a",
            pady=5,
        ).pack(fill="x")
        self.assisted_result_var = tk.StringVar(value="No estimate calculated")
        tk.Label(
            parent, textvariable=self.assisted_result_var,
            font=("Segoe UI", 8, "bold"), bg="#f4f8fb", fg=self.TEXT,
            justify="left", wraplength=265, padx=7, pady=6,
        ).pack(fill="x", pady=(4, 5))

        self._section_title(parent, "FINAL ANSWER")
        tk.Label(parent, text="Identified agonist", font=("Segoe UI", 8, "bold"),
                 bg="white", fg=self.TEXT).pack(anchor="w")
        self.answer_identity_var = tk.StringVar(value="")
        ttk.Combobox(
            parent, textvariable=self.answer_identity_var,
            values=tuple(FROG_DRUG_MODELS.keys()), state="readonly",
        ).pack(fill="x", pady=(2, 5))
        tk.Label(parent, text="Estimated concentration",
                 font=("Segoe UI", 8, "bold"), bg="white",
                 fg=self.TEXT).pack(anchor="w")
        answer_row = tk.Frame(parent, bg="white")
        answer_row.pack(fill="x", pady=2)
        self.answer_concentration_var = tk.StringVar(value="")
        tk.Entry(answer_row, textvariable=self.answer_concentration_var,
                 width=13).pack(side="left", fill="x", expand=True)
        self.answer_unit_var = tk.StringVar(value="µM")
        ttk.Combobox(
            answer_row, textvariable=self.answer_unit_var,
            values=FROG_CONCENTRATION_UNITS, state="readonly", width=9,
        ).pack(side="left", padx=(5, 0))
        tk.Button(
            parent, text="Submit Final Answer", command=self.submit_practical,
            font=("Segoe UI", 9, "bold"), bg=self.RED, fg="white", pady=7,
        ).pack(fill="x", pady=(7, 4))

    def add_known(self):
        if not self.require_washed_bath():
            return
        drug = self.known_drug_var.get()
        try:
            entered_value = _finite_positive(
                self.known_concentration_var.get(), "Known concentration"
            )
            concentration_um = frog_concentration_to_micromolar(
                entered_value, self.known_unit_var.get(), drug
            )
            response = frog_response_mm(drug, concentration_um)
        except ValueError as error:
            messagebox.showwarning("Known concentration", str(error), parent=self.master)
            return
        display = "{} {}".format(
            _format_number(entered_value), self.known_unit_var.get()
        )
        self._record({
            "kind": "standard", "drug": drug,
            "concentration_um": concentration_um,
            "display_concentration": display,
            "response_mm": response,
            "label": "Known {} | {}".format(drug, display),
            "bath_label": "Known {} in bath".format(drug),
        })

    def add_unknown(self):
        if not self.require_washed_bath():
            return
        drug = self.configuration["drug"]
        try:
            dose_fraction = _finite_positive(
                self.unknown_fraction_var.get(), "Unknown dilution fraction"
            )
            if dose_fraction > 1.0:
                raise ValueError("Unknown dilution fraction must not exceed 1.")
        except ValueError as error:
            messagebox.showwarning("Unknown dilution", str(error), parent=self.master)
            return
        final_um = self.configuration["concentration_um"] * dose_fraction
        response = frog_response_mm(drug, final_um)
        self._record({
            "kind": "unknown", "response_mm": response,
            "dose_fraction": dose_fraction,
            "label": "Unknown {} x stock".format(_format_number(dose_fraction)),
            "bath_label": "Diluted unknown solution in bath",
        })

    def calculate_assisted_estimate(self):
        unknowns = [record for record in self.records if record["kind"] == "unknown"]
        if not unknowns:
            messagebox.showwarning(
                "Assisted estimate", "Record the unknown response first.",
                parent=self.master,
            )
            return
        drug = self.hypothesis_var.get()
        try:
            effective_um = inverse_frog_response_um(
                drug, unknowns[-1]["response_mm"]
            )
            estimate_um = effective_um / unknowns[-1]["dose_fraction"]
        except ValueError as error:
            messagebox.showwarning("Assisted estimate", str(error), parent=self.master)
            return
        self.assisted_result_var.set(
            "Under the {} hypothesis: {} µM".format(
                drug, _format_number(estimate_um)
            )
        )
        self.answer_identity_var.set(drug)
        self.answer_concentration_var.set(_format_number(estimate_um))
        self.answer_unit_var.set("µM")

    def _after_reset(self):
        if hasattr(self, "assisted_result_var"):
            self.assisted_result_var.set("No estimate calculated")

    def _observation_columns(self):
        columns = ("trial", "preparation", "concentration", "micromolar", "height")
        headings = {
            "trial": "Trial", "preparation": "Preparation",
            "concentration": "Concentration shown", "micromolar": "Final bath µM",
            "height": "Height (mm)",
        }
        widths = {"trial": 50, "preparation": 170, "concentration": 125,
                  "micromolar": 95, "height": 85}
        return columns, headings, widths

    def _observation_values(self, record):
        if record["kind"] == "unknown":
            preparation = "Unknown solution"
            display = "{} x stock".format(_format_number(record["dose_fraction"]))
            micromolar = "Hidden"
        else:
            preparation = record["drug"]
            display = record["display_concentration"]
            micromolar = _format_number(record["concentration_um"])
        return (
            record["trial"], preparation, display, micromolar,
            "{:.2f}".format(record["response_mm"]),
        )

    def _answer_is_blank(self):
        return (not self.answer_identity_var.get().strip() or
                not self.answer_concentration_var.get().strip())

    def _score_and_details(self):
        identity = self.answer_identity_var.get().strip()
        answer_text = self.answer_concentration_var.get().strip()
        answer_unit = self.answer_unit_var.get()
        answer_um = None
        try:
            # Mass units refer to the actual unknown salt. Identity is separate.
            answer_um = frog_concentration_to_micromolar(
                answer_text, answer_unit, self.configuration["drug"]
            )
        except ValueError:
            pass
        correct_um = self.configuration["concentration_um"]
        relative_error = None
        concentration_score = 0
        if answer_um is not None:
            relative_error = abs(answer_um - correct_um) / correct_um
            if relative_error <= 0.10:
                concentration_score = 5
            elif relative_error <= 0.20:
                concentration_score = 4
            elif relative_error <= 0.30:
                concentration_score = 2
        identity_score = 5 if identity == self.configuration["drug"] else 0
        details = {
            "practical": self.experiment_name,
            "student_answer": {
                "identity": identity or "Not answered",
                "concentration_value": answer_text or "Not answered",
                "concentration_unit": answer_unit,
                "concentration_um": answer_um,
            },
            "correct_answer": {
                "identity": self.configuration["drug"],
                "concentration_um": correct_um,
            },
            "relative_concentration_error": relative_error,
            "score_breakdown": {
                "identity": identity_score, "identity_total": 5,
                "concentration": concentration_score, "concentration_total": 5,
                "concentration_tolerance": "5 within 10%, 4 within 20%, 2 within 30%",
            },
            "observation_count": len(self.records),
            "observations": [self._result_record(record) for record in self.records],
        }
        return identity_score + concentration_score, 10, details

    @staticmethod
    def _result_record(record):
        result = {
            "trial": record["trial"], "kind": record["kind"],
            "response_mm": record["response_mm"], "label": record["label"],
        }
        if record["kind"] == "standard":
            result.update({
                "drug": record["drug"],
                "concentration_um": record["concentration_um"],
                "display_concentration": record["display_concentration"],
            })
        else:
            result["dose_fraction"] = record["dose_fraction"]
        return result

    def _draw_summary(self, axis):
        axis.clear()
        standards = [record for record in self.records if record["kind"] == "standard"]
        unknowns = [record for record in self.records if record["kind"] == "unknown"]
        for drug in FROG_DRUG_MODELS:
            points = sorted(
                [(record["concentration_um"], record["response_mm"])
                 for record in standards if record["drug"] == drug],
                key=lambda point: point[0],
            )
            if points:
                axis.plot([point[0] for point in points],
                          [point[1] for point in points], marker="o", label=drug)
        for index, record in enumerate(unknowns, 1):
            axis.axhline(record["response_mm"], color="#7b2cbf", linestyle="--",
                         alpha=0.65,
                         label="Unknown {} x stock".format(
                             _format_number(record["dose_fraction"])
                         ))
        axis.set_xscale("log")
        axis.set_xlabel("Known final bath concentration (µM, log scale)")
        axis.set_ylabel("Contraction height (mm)")
        axis.set_title("Known concentration-response comparisons")
        axis.grid(True, which="both", alpha=0.3)
        if standards or unknowns:
            axis.legend(fontsize=7, loc="best")


class BioassayUnknownPractical(_BaseUnknownPractical):
    """Unknown ACh stock bioassay with interpolation and parallel-line methods.

    Constructor API::

        BioassayUnknownPractical(master, level="PG", exam_seconds=None,
                                  configuration=None,
                                  bath_volume_ml=10.0)

    ``configuration`` may contain ``concentration`` and ``unit`` or the internal
    ``concentration_um``.  The bath volume is fixed for the practical and is
    continuously visible to the student.
    """

    title = "Acetylcholine Unknown Concentration Bioassay"
    subtitle = (
        "Frog rectus organ bath | Interpolation, three point, and four point "
        "quantitative assay"
    )
    experiment_name = "ACh Frog Rectus Quantitative Bioassay"

    def __init__(self, master, level="PG", exam_seconds=None,
                 configuration=None, bath_volume_ml=DEFAULT_BATH_VOLUME_ML):
        self.bath_volume_ml = _finite_positive(bath_volume_ml, "Bath volume")
        self.last_estimate_um = None
        self.last_calculation = None
        _BaseUnknownPractical.__init__(
            self, master, level=level, exam_seconds=exam_seconds,
            configuration=configuration,
        )

    def _validate_configuration(self, configuration):
        if not isinstance(configuration, dict):
            raise ValueError("Bioassay configuration must be a dictionary.")
        if "concentration_um" in configuration:
            concentration_um = _finite_positive(
                configuration["concentration_um"], "Unknown stock concentration"
            )
        else:
            concentration_um = ach_concentration_to_micromolar(
                _finite_positive(configuration.get("concentration"),
                                 "Unknown stock concentration"),
                configuration.get("unit", "µM"),
            )
        return {"concentration_um": concentration_um}

    def _build_examiner_setup(self):
        setup = tk.Toplevel(self.master)
        setup.title("Examiner Setup - Unknown ACh Stock")
        set_window_size(setup, 550, 380, 500, 350)
        setup.configure(bg=self.BG)
        setup.transient(self.master)
        setup.grab_set()
        header = tk.Frame(setup, bg=self.NAVY, padx=17, pady=11)
        header.pack(fill="x")
        tk.Label(header, text="Configure Hidden ACh Stock",
                 font=("Segoe UI", 16, "bold"), bg=self.NAVY,
                 fg="white").pack(anchor="w")
        tk.Label(header, text="Acetylcholine chloride concentration remains hidden",
                 font=("Segoe UI", 9), bg=self.NAVY,
                 fg="#cfe2f3").pack(anchor="w")
        body = tk.Frame(setup, bg="white", padx=25, pady=20,
                        highlightbackground="#cbd8e2", highlightthickness=1)
        body.pack(fill="both", expand=True, padx=16, pady=16)
        current_um = (self.configuration or {"concentration_um": 100.0})[
            "concentration_um"
        ]
        concentration_var = tk.StringVar(value=_format_number(current_um))
        unit_var = tk.StringVar(value="µM")
        tk.Label(body, text="Unknown ACh stock",
                 font=("Segoe UI", 10, "bold"), bg="white",
                 fg=self.TEXT).grid(row=0, column=0, sticky="w", pady=8)
        tk.Entry(body, textvariable=concentration_var, width=17).grid(
            row=0, column=1, sticky="ew", padx=(15, 5), pady=8
        )
        ttk.Combobox(body, textvariable=unit_var,
                     values=ACH_CONCENTRATION_UNITS, state="readonly",
                     width=10).grid(row=0, column=2, sticky="ew", pady=8)
        tk.Label(
            body,
            text="Fixed bath volume: {} mL\nStudents may use any standard stock concentration and any positive dose volume."
                 .format(_format_number(self.bath_volume_ml)),
            font=("Segoe UI", 9), bg="#eaf3fa", fg=self.NAVY,
            justify="left", wraplength=430, padx=10, pady=9,
        ).grid(row=1, column=0, columnspan=3, sticky="ew", pady=(8, 14))

        def save_setup():
            try:
                configuration = self._validate_configuration({
                    "concentration": concentration_var.get(), "unit": unit_var.get()
                })
            except ValueError as error:
                messagebox.showwarning("Unknown setup", str(error), parent=setup)
                return
            self.configuration = configuration
            messagebox.showinfo(
                "Practical configured",
                "Unknown acetylcholine chloride stock: {} µM\nBath volume: {} mL\n\n"
                "The stock concentration remains hidden on the student screen.".format(
                    _format_number(configuration["concentration_um"]),
                    _format_number(self.bath_volume_ml),
                ), parent=setup,
            )
            setup.destroy()
            self.show_start_screen()

        tk.Button(body, text="Save Hidden ACh Stock", command=save_setup,
                  font=("Segoe UI", 10, "bold"), bg=self.GREEN, fg="white",
                  padx=18, pady=7).grid(row=2, column=0, columnspan=3)
        body.grid_columnconfigure(1, weight=1)

    def _build_controls(self, parent):
        tk.Label(
            parent,
            text="FIXED BATH VOLUME  {} mL".format(_format_number(self.bath_volume_ml)),
            font=("Segoe UI", 10, "bold"), bg="#eaf3fa", fg=self.NAVY,
            padx=8, pady=7,
        ).pack(fill="x", pady=(0, 7))
        self._section_title(parent, "STANDARD ACh CHLORIDE")
        tk.Label(parent, text="Stock concentration and unit",
                 font=("Segoe UI", 8, "bold"), bg="white",
                 fg=self.TEXT).pack(anchor="w")
        stock_row = tk.Frame(parent, bg="white")
        stock_row.pack(fill="x", pady=2)
        self.standard_stock_var = tk.StringVar(value="20")
        tk.Entry(stock_row, textvariable=self.standard_stock_var,
                 width=13).pack(side="left", fill="x", expand=True)
        self.standard_unit_var = tk.StringVar(value="µM")
        ttk.Combobox(
            stock_row, textvariable=self.standard_unit_var,
            values=ACH_CONCENTRATION_UNITS, state="readonly", width=9,
        ).pack(side="left", padx=(5, 0))
        tk.Label(parent, text="Dose volume added to bath (mL)",
                 font=("Segoe UI", 8, "bold"), bg="white",
                 fg=self.TEXT).pack(anchor="w", pady=(4, 0))
        self.standard_volume_var = tk.StringVar(value="1")
        tk.Entry(parent, textvariable=self.standard_volume_var).pack(fill="x", pady=2)
        tk.Button(
            parent, text="Add Standard Dose", command=self.add_standard,
            font=("Segoe UI", 9, "bold"), bg=self.BLUE, fg="white", pady=6,
        ).pack(fill="x", pady=(2, 7))

        self._section_title(parent, "HIDDEN ACh TEST STOCK")
        tk.Label(parent, text="Unknown dose volume added to bath (mL)",
                 font=("Segoe UI", 8, "bold"), bg="white",
                 fg=self.TEXT).pack(anchor="w")
        self.unknown_volume_var = tk.StringVar(value="0.25")
        tk.Entry(parent, textvariable=self.unknown_volume_var).pack(fill="x", pady=2)
        tk.Button(
            parent, text="Add Unknown Dose", command=self.add_unknown,
            font=("Segoe UI", 9, "bold"), bg=self.PURPLE, fg="white", pady=6,
        ).pack(fill="x", pady=(2, 5))
        tk.Button(
            parent, text="Wash Tissue", command=self.wash_tissue,
            font=("Segoe UI", 9, "bold"), bg=self.GREEN, fg="white", pady=6,
        ).pack(fill="x", pady=2)
        tk.Button(
            parent, text="Reset All Observations", command=self.reset_observations,
            font=("Segoe UI", 8, "bold"), bg="#6c757d", fg="white", pady=5,
        ).pack(fill="x", pady=(2, 7))

        self._section_title(parent, "ASSISTED CALCULATION")
        self.method_var = tk.StringVar(value="Interpolation")
        ttk.Combobox(
            parent, textvariable=self.method_var,
            values=("Interpolation", "Three point", "Four point"),
            state="readonly",
        ).pack(fill="x", pady=2)
        tk.Button(
            parent, text="Calculate From Observations",
            command=self.calculate_from_observations,
            font=("Segoe UI", 8, "bold"), bg="#d49b16", fg="#182b3a",
            pady=5,
        ).pack(fill="x", pady=(2, 3))
        self.calculation_result_var = tk.StringVar(
            value="Use responses between 10% and 90% of maximum."
        )
        tk.Label(
            parent, textvariable=self.calculation_result_var,
            font=("Segoe UI", 8, "bold"), bg="#fff8e1", fg="#6b5a20",
            justify="left", wraplength=265, padx=7, pady=6,
        ).pack(fill="x", pady=(2, 6))

        self._section_title(parent, "FINAL ANSWER")
        tk.Label(parent, text="Estimated unknown stock concentration",
                 font=("Segoe UI", 8, "bold"), bg="white",
                 fg=self.TEXT).pack(anchor="w")
        answer_row = tk.Frame(parent, bg="white")
        answer_row.pack(fill="x", pady=2)
        self.answer_concentration_var = tk.StringVar(value="")
        tk.Entry(answer_row, textvariable=self.answer_concentration_var,
                 width=13).pack(side="left", fill="x", expand=True)
        self.answer_unit_var = tk.StringVar(value="µM")
        ttk.Combobox(
            answer_row, textvariable=self.answer_unit_var,
            values=ACH_CONCENTRATION_UNITS, state="readonly", width=9,
        ).pack(side="left", padx=(5, 0))
        tk.Button(
            parent, text="Submit Final Answer", command=self.submit_practical,
            font=("Segoe UI", 9, "bold"), bg=self.RED, fg="white", pady=7,
        ).pack(fill="x", pady=(7, 4))

    def add_standard(self):
        if not self.require_washed_bath():
            return
        try:
            stock_value = _finite_positive(
                self.standard_stock_var.get(), "Standard stock concentration"
            )
            stock_unit = self.standard_unit_var.get()
            stock_um = ach_concentration_to_micromolar(stock_value, stock_unit)
            dose_ml = _finite_positive(self.standard_volume_var.get(), "Dose volume")
            final_um = stock_um * dose_ml / self.bath_volume_ml
            response = ach_response_from_micromolar(final_um)
        except ValueError as error:
            messagebox.showwarning("Standard dose", str(error), parent=self.master)
            return
        display_stock = "{} {}".format(_format_number(stock_value), stock_unit)
        self._record({
            "kind": "standard", "stock_um": stock_um,
            "display_stock": display_stock, "dose_ml": dose_ml,
            "dose_fraction": dose_ml / self.bath_volume_ml,
            "final_bath_um": final_um, "response_mm": response,
            "label": "S: {} | {} mL".format(display_stock, _format_number(dose_ml)),
            "bath_label": "Standard ACh dose in bath",
        })

    def add_unknown(self):
        if not self.require_washed_bath():
            return
        try:
            dose_ml = _finite_positive(self.unknown_volume_var.get(),
                                       "Unknown dose volume")
        except ValueError as error:
            messagebox.showwarning("Unknown dose", str(error), parent=self.master)
            return
        fraction = dose_ml / self.bath_volume_ml
        final_um = self.configuration["concentration_um"] * fraction
        response = ach_response_from_micromolar(final_um)
        self._record({
            "kind": "unknown", "dose_ml": dose_ml, "dose_fraction": fraction,
            "response_mm": response,
            "label": "T: Unknown | {} mL".format(_format_number(dose_ml)),
            "bath_label": "Unknown ACh dose in bath",
        })

    def calculate_from_observations(self):
        try:
            estimate_um, diagnostics = assisted_bioassay_calculation(
                self.records, self.method_var.get()
            )
        except ValueError as error:
            self.last_estimate_um = None
            self.last_calculation = None
            self.calculation_result_var.set(str(error))
            messagebox.showwarning("Assisted calculation", str(error), parent=self.master)
            return
        self.last_estimate_um = estimate_um
        self.last_calculation = diagnostics
        text = "{} estimate: {} µM".format(
            diagnostics["method"], _format_number(estimate_um)
        )
        if diagnostics["method"] == "Four point":
            text += "\nSlope difference: {:.1f}%".format(
                diagnostics["slope_difference_percent"]
            )
        else:
            text += "\nUnknown response was bracketed by the selected standards."
        self.calculation_result_var.set(text)
        self.answer_concentration_var.set(_format_number(estimate_um))
        self.answer_unit_var.set("µM")

    def _after_reset(self):
        self.last_estimate_um = None
        self.last_calculation = None
        if hasattr(self, "calculation_result_var"):
            self.calculation_result_var.set(
                "Use responses between 10% and 90% of maximum."
            )

    def _observation_columns(self):
        columns = ("trial", "solution", "stock", "volume", "bath", "height")
        headings = {
            "trial": "Trial", "solution": "Solution",
            "stock": "Stock concentration", "volume": "Dose (mL)",
            "bath": "Final bath (µM)", "height": "Height (mm)",
        }
        widths = {"trial": 48, "solution": 90, "stock": 135,
                  "volume": 82, "bath": 105, "height": 86}
        return columns, headings, widths

    def _observation_values(self, record):
        if record["kind"] == "standard":
            solution = "Standard"
            stock = record["display_stock"]
            final_bath = _format_number(record["final_bath_um"])
        else:
            solution = "Unknown"
            stock = "Hidden"
            final_bath = "Hidden"
        return (
            record["trial"], solution, stock,
            _format_number(record["dose_ml"]), final_bath,
            "{:.2f}".format(record["response_mm"]),
        )

    def _answer_is_blank(self):
        return not self.answer_concentration_var.get().strip()

    def _score_and_details(self):
        answer_text = self.answer_concentration_var.get().strip()
        answer_unit = self.answer_unit_var.get()
        answer_um = None
        try:
            answer_um = ach_concentration_to_micromolar(
                _finite_positive(answer_text, "Answer concentration"), answer_unit
            )
        except ValueError:
            pass
        correct_um = self.configuration["concentration_um"]
        relative_error = None
        score = 0
        if answer_um is not None:
            relative_error = abs(answer_um - correct_um) / correct_um
            if relative_error <= 0.10:
                score = 10
            elif relative_error <= 0.20:
                score = 8
            elif relative_error <= 0.30:
                score = 5
            elif relative_error <= 0.50:
                score = 2
        details = {
            "practical": self.experiment_name,
            "bath_volume_ml": self.bath_volume_ml,
            "student_answer": {
                "concentration_value": answer_text or "Not answered",
                "concentration_unit": answer_unit,
                "concentration_um": answer_um,
                "selected_method": self.method_var.get(),
            },
            "correct_answer": {"unknown_stock_concentration_um": correct_um},
            "relative_concentration_error": relative_error,
            "score_policy": "10 within 10%, 8 within 20%, 5 within 30%, 2 within 50%",
            "assisted_estimate_um": self.last_estimate_um,
            "assisted_calculation": self.last_calculation,
            "observation_count": len(self.records),
            "observations": [self._result_record(record) for record in self.records],
        }
        return score, 10, details

    @staticmethod
    def _result_record(record):
        result = {
            "trial": record["trial"], "kind": record["kind"],
            "dose_volume_ml": record["dose_ml"],
            "dose_fraction": record["dose_fraction"],
            "response_mm": record["response_mm"],
            "label": record["label"],
        }
        if record["kind"] == "standard":
            result.update({
                "stock_concentration_um": record["stock_um"],
                "display_stock": record["display_stock"],
                "final_bath_concentration_um": record["final_bath_um"],
            })
        return result

    def _summary_title(self):
        result = "{} | Fixed bath volume {} mL".format(
            self.title, _format_number(self.bath_volume_ml)
        )
        if self.last_estimate_um is not None and self.last_calculation:
            result += "\n{} assisted estimate: {} µM".format(
                self.last_calculation["method"], _format_number(self.last_estimate_um)
            )
        return result

    def _draw_summary(self, axis):
        axis.clear()
        standards = _mean_levels(self.records, "standard", "final_bath_um")
        unknowns = _mean_levels(self.records, "unknown", "dose_fraction")
        if standards:
            axis.plot([point[0] for point in standards],
                      [point[1] for point in standards], "o-",
                      color=self.BLUE, label="Standard ACh")
        for point in unknowns:
            axis.axhline(
                point[1], color=self.PURPLE, linestyle="--", alpha=0.65,
                label="Unknown {} mL, {:.2f} mm".format(
                    _format_number(point[0] * self.bath_volume_ml), point[1]
                ),
            )
        axis.axhspan(ACH_EMAX_MM * 0.10, ACH_EMAX_MM * 0.90,
                     color="#dff3e4", alpha=0.25, label="Useful range")
        axis.set_xscale("log")
        axis.set_xlabel("Standard final bath concentration (µM, log scale)")
        axis.set_ylabel("Contraction height (mm)")
        axis.set_title("Standard curve and labelled unknown responses")
        axis.grid(True, which="both", alpha=0.3)
        if standards or unknowns:
            axis.legend(fontsize=7, loc="best")


__all__ = [
    "FrogRectusUnknownPractical",
    "BioassayUnknownPractical",
    "FROG_DRUG_MODELS",
    "frog_concentration_to_micromolar",
    "frog_micromolar_to_concentration",
    "frog_response_mm",
    "inverse_frog_response_um",
    "final_bath_concentration_um",
    "interpolation_estimate",
    "parallel_line_estimate",
    "assisted_bioassay_calculation",
]
