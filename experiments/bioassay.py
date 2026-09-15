"""Acetylcholine bioassay on frog rectus abdominis.

Python 3.8 compatible source for the MAMC CAL launcher.
"""

import math
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from ui.display import set_window_size


ACH_CHLORIDE_MOLECULAR_WEIGHT = 181.66
ACH_EMAX_MM = 50.0
ACH_EC50_UG_ML = 0.72
ACH_HILL_COEFFICIENT = 1.35
ACH_CONCENTRATION_UNITS = (
    "M", "mM", "µM", "nM", "mg/mL", "µg/mL", "ng/mL", "g/L"
)


def concentration_to_micromolar(value, unit):
    """Convert acetylcholine chloride concentration to micromole per litre."""
    aliases = {
        "μM": "µM", "uM": "µM", "umol/L": "µM", "mol/L": "M",
        "mmol/L": "mM", "nmol/L": "nM", "ug/mL": "µg/mL",
        "mcg/mL": "µg/mL",
    }
    unit = aliases.get(str(unit).strip(), str(unit).strip())
    factors = {
        "M": 1.0e6,
        "mM": 1.0e3,
        "µM": 1.0,
        "nM": 1.0e-3,
        "mg/mL": 1.0e6 / ACH_CHLORIDE_MOLECULAR_WEIGHT,
        "µg/mL": 1.0e3 / ACH_CHLORIDE_MOLECULAR_WEIGHT,
        "ng/mL": 1.0 / ACH_CHLORIDE_MOLECULAR_WEIGHT,
        "g/L": 1.0e6 / ACH_CHLORIDE_MOLECULAR_WEIGHT,
    }
    if unit not in factors:
        raise ValueError("Unsupported concentration unit: {}".format(unit))
    numeric = float(value)
    if not np.isfinite(numeric) or numeric < 0:
        raise ValueError("Concentration must be finite and zero or more.")
    converted = numeric * factors[unit]
    if not np.isfinite(converted):
        raise ValueError("Concentration is outside the supported numeric range.")
    return converted


def micromolar_to_concentration(value_um, unit):
    """Convert micromole per litre to a supported concentration unit."""
    return float(value_um) / concentration_to_micromolar(1.0, unit)


def ach_response_from_micromolar(concentration_um, emax_mm=ACH_EMAX_MM,
                                  ec50_ug_ml=ACH_EC50_UG_ML,
                                  hill_coefficient=ACH_HILL_COEFFICIENT):
    """Deterministic Hill response for final bath concentration in micromolar."""
    concentration_um = float(concentration_um)
    if np.isnan(concentration_um) or concentration_um < 0:
        raise ValueError("Concentration must be zero or more.")
    if concentration_um == 0:
        return 0.0
    if np.isposinf(concentration_um):
        return float(emax_mm)
    ec50_um = concentration_to_micromolar(ec50_ug_ml, "µg/mL")
    log_ratio = float(hill_coefficient) * (
        math.log(ec50_um) - math.log(concentration_um)
    )
    if log_ratio >= 709.0:
        return 0.0
    if log_ratio <= -709.0:
        return float(emax_mm)
    return float(emax_mm) / (1.0 + math.exp(log_ratio))


def expected_ach_response(concentration, unit="µg/mL"):
    """Return deterministic contraction in mm for a concentration and unit."""
    return ach_response_from_micromolar(concentration_to_micromolar(concentration, unit))


class OrganBathCanvas(tk.Canvas):
    """Responsive drawing of the frog rectus organ bath and writing lever."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("background", "#f8fbfe")
        kwargs.setdefault("highlightthickness", 0)
        tk.Canvas.__init__(self, master, **kwargs)
        self.response_percent = 0.0
        self.solution_label = "Frog Ringer solution"
        self.is_washed = True
        self.bind("<Configure>", self._redraw)

    def set_state(self, response_percent, solution_label, is_washed):
        self.response_percent = float(np.clip(response_percent, 0.0, 100.0))
        self.solution_label = solution_label
        self.is_washed = bool(is_washed)
        self._redraw()

    def _redraw(self, _event=None):
        self.delete("all")
        width = max(self.winfo_width(), 180)
        height = max(self.winfo_height(), 170)
        left, right = width * 0.16, width * 0.84
        top, bottom = height * 0.25, height * 0.79
        centre = (left + right) / 2.0
        self.create_text(width / 2.0, 15, text="Frog rectus organ bath",
                         fill="#173b57", font=("Segoe UI", 10, "bold"), anchor="n")
        lever_y = top - 35
        lever_half = (right - left) * 0.32
        tilt = self.response_percent * 0.055
        self.create_line(centre - lever_half, lever_y + tilt,
                         centre + lever_half, lever_y - tilt,
                         fill="#46515a", width=3)
        self.create_oval(centre - 5, lever_y - 5, centre + 5, lever_y + 5,
                         outline="#46515a", fill="#aeb8bf", width=2)
        self.create_line(centre + lever_half, lever_y - tilt,
                         centre + lever_half, lever_y - tilt + 11,
                         fill="#d62828", width=2)
        self.create_text(centre - lever_half - 5, lever_y, text="Lever",
                         fill="#607789", font=("Segoe UI", 8), anchor="e")

        water_top = top + (bottom - top) * 0.11
        self.create_rectangle(left + 2, water_top, right - 2, bottom - 2,
                              fill="#dcefff" if self.is_washed else "#d9f2e1",
                              outline="")
        wave = []
        for index in range(13):
            wave.extend((left + (right - left) * index / 12.0,
                         water_top + (2 if index % 2 else -2)))
        self.create_line(*wave, fill="#77add5", width=2, smooth=True)
        self.create_line(left, top, left, bottom, right, bottom, right, top,
                         fill="#5d91bd", width=3)
        for index in range(6):
            bubble_x = right - 30 + 5 * math.sin(index * 1.7)
            bubble_y = bottom - 25 - index * (bottom - water_top - 35) / 6.0
            radius = 2 + index % 2
            self.create_oval(bubble_x - radius, bubble_y - radius,
                             bubble_x + radius, bubble_y + radius,
                             outline="#9acaf0")

        shortening = (bottom - water_top) * 0.18 * self.response_percent / 100.0
        muscle_top = water_top + 20
        muscle_bottom = bottom - 28 - shortening
        muscle_width = max(16, min(24, width * 0.055))
        self.create_line(centre, lever_y + 6, centre, muscle_top,
                         fill="#59636b", dash=(4, 3))
        self.create_rectangle(centre - muscle_width / 2.0, muscle_top,
                              centre + muscle_width / 2.0, muscle_bottom,
                              fill="#f08080", outline="#c94f5b", width=2)
        stripe_y = muscle_top + 6
        while stripe_y < muscle_bottom - 4:
            self.create_line(centre - muscle_width / 2.0 + 3, stripe_y,
                             centre + muscle_width / 2.0 - 3, stripe_y,
                             fill="#df646d")
            stripe_y += 7
        self.create_text(centre + muscle_width / 2.0 + 8,
                         (muscle_top + muscle_bottom) / 2.0,
                         text="Rectus\nabdominis", justify="left", anchor="w",
                         fill="#425d74", font=("Segoe UI", 8))
        hook_y = bottom - 18
        self.create_arc(centre - 8, hook_y - 8, centre + 8, hook_y + 8,
                        start=0, extent=180, style="arc", outline="#68747d", width=2)
        self.create_line(centre, muscle_bottom, centre, hook_y - 5,
                         fill="#68747d", width=2)
        self.create_line(centre, hook_y + 7, centre, bottom + 8,
                         fill="#68747d", width=2)
        if self.response_percent > 0.5:
            self.create_text(width / 2.0, top - 8,
                             text="Contraction  {:.1f}%".format(self.response_percent),
                             fill="#a13d2d", font=("Segoe UI", 9, "bold"), anchor="s")
        self.create_text(width / 2.0, bottom + 14,
                         text="Organ bath with Frog Ringer solution",
                         fill="#425d74", font=("Segoe UI", 8), anchor="n")
        self.create_text(width / 2.0, bottom + 34, text=self.solution_label,
                         fill="#237032" if self.is_washed else "#a13d2d",
                         font=("Segoe UI", 8, "bold"), anchor="n", width=width * 0.85)


class BioassaySimulation:
    """Teaching simulation of ACh bioassay on frog rectus abdominis."""

    STANDARD_CONCENTRATIONS = (0.10, 0.20, 0.40, 0.80, 1.60, 3.20)
    UNKNOWN_CHOICES = (0.30, 0.50, 0.65, 1.00, 1.25, 2.00)
    EMAX_MM = ACH_EMAX_MM
    EC50 = ACH_EC50_UG_ML
    HILL_COEFFICIENT = ACH_HILL_COEFFICIENT
    ACH_CHLORIDE_MOLECULAR_WEIGHT = ACH_CHLORIDE_MOLECULAR_WEIGHT
    CONCENTRATION_UNITS = ACH_CONCENTRATION_UNITS
    TEST_DILUTION_UNITS = ("× stock", "% stock")
    METHODS = ("Interpolation", "Three point", "Four point")

    NAVY, BLUE, GREEN = "#173b57", "#1769aa", "#237032"
    RED, GOLD = "#a13d2d", "#d49b16"
    BG, CARD, TEXT, MUTED = "#eef4f8", "#ffffff", "#20394d", "#607789"

    THEORY_SECTIONS = (
        ("Aim", "The aim is to estimate the concentration of an unknown acetylcholine solution by comparing its response with a standard acetylcholine solution on frog rectus abdominis muscle."),
        ("Principle", "Acetylcholine produces a slow contracture of frog rectus abdominis by stimulating nicotinic receptors. Within a suitable range, a higher bath concentration gives a greater contraction. The same tissue, contact time, temperature and washing schedule must be used for standard and test solutions."),
        ("Concentration response relation", "The response follows a graded sigmoid relation when response is plotted against the logarithm of concentration. The simulation uses the Hill equation with a maximum contraction of 50 mm. Very low concentrations give little response and very high concentrations approach the maximum. Quantitative comparison is best made in the middle part of the curve."),
        ("Units and conversion", "Molar units and mass concentration units are accepted. Mass units are converted using the molecular weight of acetylcholine chloride, which is 181.66 gram per mole. The displayed response is calculated from the final bath concentration in micromole per litre."),
        ("Interpolation method", "The response of the unknown test is kept between the responses of two standard concentrations. Its equivalent final bath concentration is read on the logarithmic concentration scale. This value is divided by the test dilution fraction to estimate the concentration of the original unknown stock."),
        ("Three point and four point methods", "In the three point method, two standard concentrations and one test dilution are used. In the four point method, two standard concentrations and two test dilutions are used. The four point calculation compares two parallel lines in the middle response range. Repeated observations and alternate standard and test doses improve reliability."),
        ("Important precautions", "Use only positive concentration values. Keep the contact period constant. Wash the tissue after every dose and allow the baseline to return. Avoid comparing responses near zero or near the maximum. Use concentrations which give increasing and reproducible responses."),
    )
    PRACTICAL_SECTIONS = (
        ("Apparatus and preparation", "Mount the frog rectus abdominis in an organ bath containing Frog Ringer solution at 25 degree Celsius. Fix the lower end of the muscle to the tissue hook. Connect the upper end to the writing lever or force transducer. Apply a small resting tension and allow the tissue to stabilise."),
        ("Common procedure", "Before the student starts, the teacher uses Teacher Setup to enter the unknown acetylcholine stock concentration and its unit. No password is required in teaching mode. The value is then hidden from the student controls. Select the method and choose Standard ACh. Enter any positive final bath concentration and select its unit. Add the dose and record the height of contraction. Wash the tissue before every next dose. For the unknown sample, enter the fraction of the stock solution used."),
        ("Experiment 1  Standard concentration response curve", "Give four or more increasing standard concentrations. Wash after every response. Use values which cover the lower, middle and upper parts of the graded response. Open the Results tab to see the logarithmic concentration response curve and the measured height in mm."),
        ("Experiment 2  Interpolation bioassay", "Record at least two standard responses which lie below and above the unknown response. Record the unknown at a known stock fraction such as 0.5 times stock or 50 percent stock. Repeat the observations if required. Select Interpolation and calculate the unknown concentration."),
        ("Experiment 3  Three point bioassay", "Choose two standard concentrations S1 and S2 in the middle response range. Record one unknown test dilution T between their responses. It is better to repeat the sequence S1, T and S2. Select Three point and calculate. The program uses logarithmic interpolation and corrects for the test dilution."),
        ("Experiment 4  Four point bioassay", "Choose two standard concentrations S1 and S2. Choose two unknown test fractions T1 and T2. Keep the same dose ratio for both pairs when possible. Record S1, T1, S2 and T2 and repeat the sequence. Select Four point and calculate. The program checks the slopes and applies a parallel line calculation."),
        ("Saving the result", "Select Save result image after recording the observations. The saved PNG contains the complete kymograph, every dose label, response percentage, measured height in mm, the labelled vertical axis, the concentration response plot and the observation table."),
    )

    def __init__(self, master):
        self.master = master
        self.master.title("Bioassay of Acetylcholine on Frog Rectus Abdominis")
        set_window_size(
            master, 1320, 830, 760, 520,
            margin_x=36, margin_y=70, expand_large=True,
        )
        master.configure(bg=self.BG)
        self.rng = np.random.default_rng()
        self.records, self.trace_segments = [], []
        self.time_cursor = 0.0
        self.is_washed, self.current_peak, self.trial_number = True, 0.0, 0
        self.trace_view_start, self.trace_window_seconds = 0.0, 420.0
        self.show_all_trace = False
        self.last_estimate_um = None
        self.last_result_text, self.last_calculation = "", None
        self.unknown_concentration_um = None
        self.unknown_concentration = None
        self.teacher_stock_value = "0.72"
        self.teacher_stock_unit = "µg/mL"
        self.teacher_setup_window = None
        self._control_solution = "Standard ACh"
        self._standard_entry, self._test_entry = ("0.20", "µg/mL"), ("0.50", "× stock")
        self._live_compact = None
        self._compact_panel = "organ"
        self._configure_styles()
        self.build_interface()
        self.reset_experiment(confirm=False)

    @classmethod
    def convert_to_micromolar(cls, value, unit):
        return concentration_to_micromolar(value, unit)

    @classmethod
    def micromolar_to_value(cls, value_um, unit):
        return micromolar_to_concentration(value_um, unit)

    @classmethod
    def response_from_micromolar(cls, concentration_um):
        return ach_response_from_micromolar(concentration_um, cls.EMAX_MM,
                                             cls.EC50, cls.HILL_COEFFICIENT)

    @classmethod
    def expected_response(cls, concentration):
        """Return contraction for microgram per mL, preserving the old API."""
        return expected_ach_response(max(float(concentration), 0.0), "µg/mL")

    @staticmethod
    def _format_number(value):
        value = float(value)
        if value and (abs(value) < 0.001 or abs(value) >= 10000):
            return "{:.3g}".format(value)
        return "{:.4f}".format(value).rstrip("0").rstrip(".")

    @staticmethod
    def interpolation_estimate(standard_points, test_response, test_fraction=1.0):
        if not np.isfinite(test_fraction) or test_fraction <= 0:
            raise ValueError("The unknown test fraction must be positive.")
        points = sorted(((float(x), float(y)) for x, y in standard_points),
                        key=lambda point: point[1])
        if len(points) < 2:
            raise ValueError("At least two different standard concentrations are required.")
        for lower, upper in zip(points[:-1], points[1:]):
            if lower[0] > 0 and upper[0] > 0 and lower[1] <= test_response <= upper[1] and upper[1] > lower[1]:
                fraction = (test_response - lower[1]) / (upper[1] - lower[1])
                log_value = math.log10(lower[0]) + fraction * (math.log10(upper[0]) - math.log10(lower[0]))
                return (10.0 ** log_value) / test_fraction, lower, upper
        raise ValueError("The unknown response must lie between two standard responses.")

    @staticmethod
    def parallel_line_estimate(standard_points, test_points):
        if len(standard_points) < 2 or len(test_points) < 2:
            raise ValueError("Two standard levels and two test levels are required.")
        sx = np.log10(np.asarray([p[0] for p in standard_points], dtype=float))
        sy = np.asarray([p[1] for p in standard_points], dtype=float)
        tx = np.log10(np.asarray([p[0] for p in test_points], dtype=float))
        ty = np.asarray([p[1] for p in test_points], dtype=float)
        if not np.all(np.isfinite(sx)) or not np.all(np.isfinite(tx)):
            raise ValueError("All concentration and dilution values must be positive.")
        if np.ptp(sx) == 0 or np.ptp(tx) == 0:
            raise ValueError("Use two different levels for both standard and test.")
        standard_slope = float(np.polyfit(sx, sy, 1)[0])
        test_slope = float(np.polyfit(tx, ty, 1)[0])
        if standard_slope <= 0 or test_slope <= 0:
            raise ValueError("Responses must increase with concentration and test fraction.")
        numerator = float(np.sum((sx - sx.mean()) * (sy - sy.mean())))
        numerator += float(np.sum((tx - tx.mean()) * (ty - ty.mean())))
        denominator = float(np.sum((sx - sx.mean()) ** 2) + np.sum((tx - tx.mean()) ** 2))
        if denominator <= 0:
            raise ValueError("The selected levels do not permit a slope calculation.")
        common_slope = numerator / denominator
        if common_slope <= 0:
            raise ValueError("A positive common slope could not be calculated.")
        standard_intercept = float(sy.mean() - common_slope * sx.mean())
        test_intercept = float(ty.mean() - common_slope * tx.mean())
        unknown_um = 10.0 ** ((test_intercept - standard_intercept) / common_slope)
        slope_difference = abs(standard_slope - test_slope) / max(
            abs((standard_slope + test_slope) / 2.0), 1.0e-12) * 100.0
        return unknown_um, {
            "standard_slope": standard_slope, "test_slope": test_slope,
            "common_slope": common_slope,
            "slope_difference_percent": slope_difference,
        }

    def _configure_styles(self):
        style = ttk.Style(self.master)
        style.configure("Bio.TNotebook", background=self.BG, borderwidth=0)
        style.configure("Bio.TNotebook.Tab", padding=(14, 7), font=("Segoe UI", 10, "bold"))
        style.configure("Bio.Treeview", rowheight=26, font=("Segoe UI", 9))
        style.configure("Bio.Treeview.Heading", font=("Segoe UI", 9, "bold"))

    def build_interface(self):
        self.header = tk.Frame(self.master, bg=self.NAVY, padx=18, pady=9)
        self.header.pack(fill="x")
        self.title_label = tk.Label(self.header, text="BIOASSAY OF ACETYLCHOLINE",
                                    font=("Segoe UI", 18, "bold"), bg=self.NAVY,
                                    fg="white", justify="left", anchor="w")
        self.title_label.pack(fill="x")
        self.subtitle_label = tk.Label(
            self.header,
            text="Frog rectus abdominis organ bath  |  Interpolation, three point and four point methods",
            font=("Segoe UI", 9), bg=self.NAVY, fg="#d8e8f5", justify="left", anchor="w")
        self.subtitle_label.pack(fill="x", pady=(2, 0))
        self.header.bind("<Configure>", self._resize_header_labels)
        self.notebook = ttk.Notebook(self.master, style="Bio.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=8, pady=(6, 8))
        experiment_tab = tk.Frame(self.notebook, bg=self.BG)
        theory_tab = tk.Frame(self.notebook, bg=self.BG)
        practical_tab = tk.Frame(self.notebook, bg=self.BG)
        self.notebook.add(experiment_tab, text="Experiment")
        self.notebook.add(theory_tab, text="Theory")
        self.notebook.add(practical_tab, text="Practical and how to perform")
        self.build_experiment_tab(experiment_tab)
        self._build_reading_page(theory_tab, "THEORY", self.THEORY_SECTIONS)
        self._build_reading_page(practical_tab, "PRACTICAL PROCEDURE", self.PRACTICAL_SECTIONS)

    def _resize_header_labels(self, event):
        wrap = max(260, event.width - 36)
        self.title_label.configure(wraplength=wrap)
        self.subtitle_label.configure(wraplength=wrap)

    def _build_reading_page(self, parent, title, sections):
        card = tk.Frame(parent, bg=self.CARD, highlightbackground="#cbd8e2", highlightthickness=1)
        card.pack(fill="both", expand=True, padx=8, pady=8)
        tk.Label(card, text=title, font=("Segoe UI", 16, "bold"), bg=self.CARD,
                 fg=self.NAVY, anchor="w", padx=18, pady=12).pack(fill="x")
        holder = tk.Frame(card, bg=self.CARD)
        holder.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        scrollbar = ttk.Scrollbar(holder, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        text_widget = tk.Text(holder, wrap="word", yscrollcommand=scrollbar.set,
                              bg="#fbfdff", fg=self.TEXT, relief="flat", borderwidth=0,
                              padx=18, pady=12, font=("Segoe UI", 11), spacing1=2, spacing3=8)
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=text_widget.yview)
        text_widget.tag_configure("section", font=("Segoe UI", 12, "bold"),
                                  foreground=self.BLUE, spacing1=10, spacing3=4)
        text_widget.tag_configure("body", lmargin1=4, lmargin2=4, rmargin=12)
        for heading, body in sections:
            text_widget.insert("end", heading + "\n", "section")
            text_widget.insert("end", body + "\n\n", "body")
        text_widget.configure(state="disabled")

    def build_experiment_tab(self, parent):
        body = tk.Frame(parent, bg=self.BG)
        body.pack(fill="both", expand=True)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        shell = tk.Frame(body, bg=self.CARD, width=330,
                         highlightbackground="#cbd8e2", highlightthickness=1)
        shell.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        shell.grid_propagate(False)
        self.control_canvas = tk.Canvas(shell, bg=self.CARD, highlightthickness=0, width=330)
        scroll = ttk.Scrollbar(shell, orient="vertical", command=self.control_canvas.yview)
        self.control_canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.control_canvas.pack(side="left", fill="both", expand=True)
        self.control_inner = tk.Frame(self.control_canvas, bg=self.CARD)
        self.control_window = self.control_canvas.create_window((0, 0), window=self.control_inner, anchor="nw")
        self.control_inner.bind("<Configure>", self._update_control_scrollregion)
        self.control_canvas.bind("<Configure>", self._resize_control_inner)
        self.build_control_panel(self.control_inner)
        self._bind_control_wheel_tree(self.control_canvas)
        workspace = tk.Frame(body, bg=self.BG)
        workspace.grid(row=0, column=1, sticky="nsew")
        self.build_workspace(workspace)

    def _update_control_scrollregion(self, _event=None):
        self.control_canvas.configure(scrollregion=self.control_canvas.bbox("all"))

    def _resize_control_inner(self, event):
        self.control_canvas.itemconfigure(self.control_window, width=max(event.width, 280))

    def _bind_control_wheel_tree(self, widget):
        """Keep wheel scrolling local so other screens retain their bindings."""
        widget.bind("<MouseWheel>", self._scroll_control_wheel, add="+")
        for child in widget.winfo_children():
            self._bind_control_wheel_tree(child)

    def _scroll_control_wheel(self, event):
        self.control_canvas.yview_scroll(int(-event.delta / 120), "units")

    def _section(self, parent, title):
        frame = tk.LabelFrame(parent, text=title, bg=self.CARD, fg=self.NAVY,
                              font=("Segoe UI", 9, "bold"), padx=10, pady=8)
        frame.pack(fill="x", padx=11, pady=(8, 0))
        return frame

    def _teacher_stock_is_configured(self):
        value = self.unknown_concentration_um
        return value is not None and np.isfinite(value) and value > 0

    def set_teacher_stock(self, value, unit):
        """Validate and store the hidden teaching stock; return it in µM."""
        display_value = self._parse_positive(value, "unknown stock concentration")
        concentration_um = self.convert_to_micromolar(display_value, unit)
        if not np.isfinite(concentration_um) or concentration_um <= 0:
            raise ValueError(
                "Unknown stock concentration must be a positive finite number."
            )
        self.unknown_concentration_um = float(concentration_um)
        self.unknown_concentration = self.micromolar_to_value(
            self.unknown_concentration_um, "µg/mL"
        )
        self.teacher_stock_value = self._format_number(display_value)
        self.teacher_stock_unit = unit
        self._update_teacher_setup_state()
        return self.unknown_concentration_um

    def _update_teacher_setup_state(self):
        """Keep the hidden-stock status and dose lock in sync."""
        configured = self._teacher_stock_is_configured()
        if hasattr(self, "teacher_setup_status"):
            if configured:
                self.teacher_setup_status.configure(
                    text=("Hidden unknown stock is configured. Its value is "
                          "concealed from the student controls."),
                    bg="#eef7f0", fg=self.GREEN,
                )
            else:
                self.teacher_setup_status.configure(
                    text="Hidden unknown stock is not configured. Dosing is locked.",
                    bg="#fff3f0", fg=self.RED,
                )
        if hasattr(self, "add_dose_button"):
            self.add_dose_button.configure(
                state="normal" if configured else "disabled"
            )

    def open_teacher_setup(self):
        """Let a teacher configure the hidden stock without a password.

        Examination mode has a separate password-protected examiner setup in
        ``quantitative_practicals.py``.  This dialog belongs only to the guided
        teaching simulator.
        """
        if (self.teacher_setup_window is not None and
                self.teacher_setup_window.winfo_exists()):
            self.teacher_setup_window.deiconify()
            self.teacher_setup_window.lift()
            self.teacher_setup_window.focus_force()
            return

        setup = tk.Toplevel(self.master)
        self.teacher_setup_window = setup
        setup.title("Teacher Setup - Hidden ACh Stock")
        set_window_size(
            setup, 580, 410, 480, 340,
            margin_x=30, margin_y=60, expand_large=False,
        )
        setup.configure(bg=self.BG)
        setup.transient(self.master)
        setup.grab_set()

        header = tk.Frame(setup, bg=self.NAVY, padx=17, pady=11)
        header.pack(fill="x")
        title = tk.Label(
            header, text="TEACHER SETUP",
            font=("Segoe UI", 16, "bold"), bg=self.NAVY, fg="white",
            justify="left", anchor="w",
        )
        title.pack(fill="x")
        subtitle = tk.Label(
            header,
            text="Enter the unknown acetylcholine chloride stock before dosing",
            font=("Segoe UI", 9), bg=self.NAVY, fg="#d8e8f5",
            justify="left", anchor="w",
        )
        subtitle.pack(fill="x", pady=(2, 0))
        header.bind(
            "<Configure>",
            lambda event: (
                title.configure(wraplength=max(260, event.width - 34)),
                subtitle.configure(wraplength=max(260, event.width - 34)),
            ),
        )

        body = tk.Frame(
            setup, bg=self.CARD, padx=22, pady=18,
            highlightbackground="#cbd8e2", highlightthickness=1,
        )
        body.pack(fill="both", expand=True, padx=14, pady=14)
        body.grid_columnconfigure(1, weight=1)
        tk.Label(
            body, text="Unknown ACh stock concentration",
            bg=self.CARD, fg=self.TEXT, font=("Segoe UI", 10, "bold"),
            justify="left", anchor="w",
        ).grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 4))

        concentration_var = tk.StringVar(value=self.teacher_stock_value)
        unit_var = tk.StringVar(value=self.teacher_stock_unit)
        concentration_entry = ttk.Entry(
            body, textvariable=concentration_var, width=18,
        )
        concentration_entry.grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=(0, 7), pady=3,
        )
        ttk.Combobox(
            body, textvariable=unit_var, values=self.CONCENTRATION_UNITS,
            state="readonly", width=10,
        ).grid(row=1, column=2, sticky="ew", pady=3)

        info = tk.Label(
            body,
            text=("This value determines every response to the unknown sample "
                  "and the expected final estimate. After saving, the value is "
                  "hidden on the student screen."),
            bg="#eaf3fa", fg=self.NAVY, justify="left", anchor="w",
            wraplength=490, padx=10, pady=9, font=("Segoe UI", 9),
        )
        info.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(11, 9))
        body.bind(
            "<Configure>",
            lambda event: info.configure(wraplength=max(260, event.width - 64)),
        )

        caution = tk.Label(
            body,
            text=("Use any positive finite concentration in the selected unit. "
                  "Changing a stock after observations have been recorded will "
                  "clear those observations so results cannot be mixed."),
            bg=self.CARD, fg=self.MUTED, justify="left", anchor="w",
            wraplength=390, font=("Segoe UI", 8),
        )
        caution.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        body.bind(
            "<Configure>",
            lambda event: (
                info.configure(wraplength=max(260, event.width - 64)),
                caution.configure(wraplength=max(260, event.width - 48)),
            ),
        )

        buttons = tk.Frame(body, bg=self.CARD)
        buttons.grid(row=4, column=0, columnspan=3, sticky="ew")

        def close_setup():
            if setup.winfo_exists():
                try:
                    setup.grab_release()
                except tk.TclError:
                    pass
                setup.destroy()
            self.teacher_setup_window = None
            if not self._teacher_stock_is_configured():
                self.teaching_note.configure(
                    text=("Teacher setup was cancelled. Configure the hidden "
                          "unknown stock before any dose can be recorded.")
                )
            self._update_teacher_setup_state()

        def save_setup():
            try:
                display_value = self._parse_positive(
                    concentration_var.get(), "unknown stock concentration"
                )
                display_unit = unit_var.get()
                concentration_um = self.convert_to_micromolar(
                    display_value, display_unit
                )
                if not np.isfinite(concentration_um) or concentration_um <= 0:
                    raise ValueError(
                        "Unknown stock concentration must be a positive finite number."
                    )
            except ValueError as error:
                messagebox.showwarning("Teacher setup", str(error), parent=setup)
                return

            changed = (
                not self._teacher_stock_is_configured() or
                not math.isclose(
                    concentration_um, self.unknown_concentration_um,
                    rel_tol=1.0e-12, abs_tol=1.0e-12,
                )
            )
            if changed and self.records and not messagebox.askyesno(
                    "Change hidden stock",
                    "Changing the hidden stock will clear all recorded observations. Continue?",
                    parent=setup):
                return

            self.set_teacher_stock(display_value, display_unit)
            try:
                setup.grab_release()
            except tk.TclError:
                pass
            setup.destroy()
            self.teacher_setup_window = None

            if changed:
                self.reset_experiment(confirm=False)
            else:
                self._update_teacher_setup_state()
            self.teaching_note.configure(
                text=("Teacher setup complete. The hidden stock is ready. "
                      "Begin with standards in the middle response range.")
            )
            messagebox.showinfo(
                "Teacher setup saved",
                ("Hidden ACh stock configured as {} {}.\n\nThe value is now "
                 "concealed from student controls. Dosing is enabled.").format(
                     self.teacher_stock_value, self.teacher_stock_unit
                 ),
                parent=self.master,
            )

        tk.Button(
            buttons, text="Save Hidden Stock", command=save_setup,
            bg=self.GREEN, fg="white", font=("Segoe UI", 10, "bold"),
            padx=14, pady=7,
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        tk.Button(
            buttons, text="Cancel", command=close_setup,
            bg="#6c757d", fg="white", font=("Segoe UI", 10),
            padx=14, pady=7,
        ).pack(side="left", fill="x", expand=True, padx=(4, 0))
        setup.protocol("WM_DELETE_WINDOW", close_setup)
        setup.bind("<Escape>", lambda _event: close_setup())
        setup.bind("<Return>", lambda _event: save_setup())
        concentration_entry.focus_set()
        concentration_entry.selection_range(0, "end")

    def build_control_panel(self, parent):
        teacher = self._section(parent, "TEACHER SETUP — REQUIRED FIRST")
        self.teacher_setup_status = tk.Label(
            teacher,
            text="Hidden unknown stock is not configured. Dosing is locked.",
            bg="#fff3f0", fg=self.RED, justify="left", anchor="w",
            wraplength=275, padx=8, pady=7, font=("Segoe UI", 9, "bold"),
        )
        self.teacher_setup_status.pack(fill="x", pady=(0, 6))
        tk.Button(
            teacher, text="Teacher: Set or Change Hidden Stock",
            command=self.open_teacher_setup, bg="#6a3d8f", fg="white",
            font=("Segoe UI", 9, "bold"), pady=6,
        ).pack(fill="x")
        tk.Label(
            teacher,
            text="Teaching mode: no password is requested. Configure the stock before handing the experiment to the student.",
            bg=self.CARD, fg=self.MUTED, justify="left", anchor="w",
            wraplength=275, font=("Segoe UI", 8),
        ).pack(fill="x", pady=(6, 0))

        objective = self._section(parent, "OBJECTIVE")
        tk.Label(objective,
                 text="Estimate an unknown ACh stock concentration from graded contractions of frog rectus abdominis.",
                 bg=self.CARD, fg=self.TEXT, justify="left", anchor="w",
                 wraplength=275, font=("Segoe UI", 9)).pack(fill="x")
        design = self._section(parent, "ASSAY DESIGN")
        design.grid_columnconfigure(1, weight=1)
        tk.Label(design, text="Method", bg=self.CARD, fg=self.TEXT).grid(row=0, column=0, sticky="w", pady=3)
        self.method_var = tk.StringVar(value=self.METHODS[0])
        self.method_box = ttk.Combobox(design, textvariable=self.method_var,
                                       values=self.METHODS, state="readonly", width=18)
        self.method_box.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=3)
        self.method_box.bind("<<ComboboxSelected>>", self._method_changed)
        tk.Label(design, text="Solution", bg=self.CARD, fg=self.TEXT).grid(row=1, column=0, sticky="w", pady=3)
        self.solution_var = tk.StringVar(value="Standard ACh")
        self.solution_box = ttk.Combobox(design, textvariable=self.solution_var,
                                         values=("Standard ACh", "Unknown ACh test"),
                                         state="readonly", width=18)
        self.solution_box.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=3)
        self.solution_box.bind("<<ComboboxSelected>>", self.update_solution_controls)

        dose = self._section(parent, "FINAL BATH CONCENTRATION")
        dose.grid_columnconfigure(1, weight=1)
        self.dose_field_label = tk.Label(dose, text="ACh concentration",
                                         bg=self.CARD, fg=self.TEXT, justify="left", anchor="w")
        self.dose_field_label.grid(row=0, column=0, columnspan=3, sticky="w", pady=(2, 1))
        self.dose_var = tk.StringVar(value="0.20")
        self.dose_entry = ttk.Combobox(dose, textvariable=self.dose_var,
                                       values=("0.05", "0.10", "0.20", "0.40", "0.80", "1.60", "3.20"),
                                       state="normal", width=11)
        self.dose_entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(0, 4), pady=3)
        self.unit_var = tk.StringVar(value="µg/mL")
        self.unit_box = ttk.Combobox(dose, textvariable=self.unit_var,
                                     values=self.CONCENTRATION_UNITS, state="readonly", width=9)
        self.unit_box.grid(row=1, column=2, sticky="ew", pady=3)
        self.dose_help = tk.Label(dose,
                                  text="Enter the final concentration present in the organ bath. No bath volume is assumed.",
                                  bg=self.CARD, fg=self.MUTED, justify="left", anchor="w",
                                  wraplength=280, font=("Segoe UI", 8))
        self.dose_help.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(1, 6))
        row = tk.Frame(dose, bg=self.CARD)
        row.grid(row=3, column=0, columnspan=3, sticky="ew")
        self.add_dose_button = tk.Button(
            row, text="Add dose and record", command=self.administer_solution,
            bg=self.BLUE, fg="white", font=("Segoe UI", 10, "bold"), pady=7,
        )
        self.add_dose_button.pack(
            side="left", fill="x", expand=True, padx=(0, 4))
        tk.Button(row, text="Wash tissue", command=self.wash_tissue,
                  bg=self.GREEN, fg="white", font=("Segoe UI", 10, "bold"), pady=7).pack(
                      side="left", fill="x", expand=True, padx=(4, 0))

        analysis = self._section(parent, "UNKNOWN CONCENTRATION")
        analysis.grid_columnconfigure(1, weight=1)
        tk.Button(analysis, text="Calculate unknown concentration",
                  command=self.calculate_unknown, bg=self.GOLD, fg="#17202a",
                  font=("Segoe UI", 9, "bold"), pady=6).grid(
                      row=0, column=0, columnspan=3, sticky="ew", pady=(0, 7))
        tk.Label(analysis, text="Your estimate", bg=self.CARD, fg=self.TEXT).grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(2, 1))
        self.student_estimate_var = tk.StringVar()
        ttk.Entry(analysis, textvariable=self.student_estimate_var, width=11).grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=(0, 4), pady=3)
        self.student_unit_var = tk.StringVar(value="µg/mL")
        ttk.Combobox(analysis, textvariable=self.student_unit_var,
                     values=self.CONCENTRATION_UNITS, state="readonly", width=9).grid(
                         row=2, column=2, sticky="ew", pady=3)
        tk.Button(analysis, text="Check my estimate", command=self.check_student_estimate,
                  bg="#6f42c1", fg="white", font=("Segoe UI", 9, "bold"), pady=5).grid(
                      row=3, column=0, columnspan=3, sticky="ew", pady=(5, 0))

        actions = self._section(parent, "RESULT AND CONTROLS")
        tk.Button(actions, text="Save result image", command=self.export_results_image,
                  bg="#0f7c90", fg="white", font=("Segoe UI", 9, "bold"), pady=6).pack(fill="x")
        tk.Button(actions, text="Reset observations (keep hidden stock)", command=self.reset_experiment,
                  bg="#6c757d", fg="white", font=("Segoe UI", 9), pady=5).pack(
                      fill="x", pady=(6, 0))
        note = self._section(parent, "GUIDANCE")
        self.teaching_note = tk.Label(note, text="", bg="#fff8e1", fg="#594a18",
                                      justify="left", anchor="w", wraplength=275,
                                      padx=8, pady=7, font=("Segoe UI", 9))
        self.teaching_note.pack(fill="x")
        conditions = self._section(parent, "FIXED CONDITIONS")
        tk.Label(conditions,
                 text="Preparation: Frog rectus abdominis\nBath fluid: Frog Ringer solution\nTemperature: 25 ± 1 °C\nContact time: 90 seconds\nResponse: Isotonic contraction in mm",
                 bg=self.CARD, fg=self.TEXT, justify="left", anchor="w",
                 font=("Segoe UI", 8)).pack(fill="x")
        tk.Frame(parent, bg=self.CARD, height=10).pack(fill="x")

    def build_workspace(self, parent):
        self.workspace_notebook = ttk.Notebook(parent)
        self.workspace_notebook.pack(fill="both", expand=True)
        live_tab = tk.Frame(self.workspace_notebook, bg=self.BG)
        results_tab = tk.Frame(self.workspace_notebook, bg=self.BG)
        self.workspace_notebook.add(live_tab, text="Live organ bath and kymograph")
        self.workspace_notebook.add(results_tab, text="Results and observations")

        self.live_area = tk.Frame(live_tab, bg=self.BG)
        self.live_area.pack(fill="both", expand=True)
        self.live_area.bind("<Configure>", self._reflow_live_area)
        self.compact_switch = tk.Frame(self.live_area, bg=self.BG)
        self.organ_view_button = tk.Button(
            self.compact_switch, text="Organ bath", command=lambda: self._show_compact_panel("organ"),
            bg="#e8f1f8", fg=self.NAVY, font=("Segoe UI", 9, "bold"), pady=4,
        )
        self.organ_view_button.pack(side="left", fill="x", expand=True, padx=(0, 3))
        self.trace_view_button = tk.Button(
            self.compact_switch, text="Kymograph and scrolling",
            command=lambda: self._show_compact_panel("trace"),
            bg=self.BLUE, fg="white", font=("Segoe UI", 9, "bold"), pady=4,
        )
        self.trace_view_button.pack(side="left", fill="x", expand=True, padx=(3, 0))
        self.organ_card = tk.Frame(self.live_area, bg=self.CARD,
                                   highlightbackground="#cbd8e2", highlightthickness=1)
        self.organ_bath = OrganBathCanvas(self.organ_card, width=285, height=500)
        self.organ_bath.pack(fill="both", expand=True, padx=5, pady=5)
        self.trace_card = tk.Frame(self.live_area, bg=self.CARD,
                                   highlightbackground="#cbd8e2", highlightthickness=1)
        trace_top = tk.Frame(self.trace_card, bg=self.CARD, padx=8, pady=5)
        trace_top.pack(fill="x")
        tk.Label(trace_top, text="CONTINUOUS KYMOGRAPH RECORDING",
                 bg=self.CARD, fg=self.NAVY,
                 font=("Segoe UI", 9, "bold")).pack(fill="x")
        trace_actions = tk.Frame(trace_top, bg=self.CARD)
        trace_actions.pack(fill="x", pady=(3, 0))
        tk.Button(trace_actions, text="Show all", command=self.show_all_recordings,
                   bg="#e8f1f8", fg=self.NAVY, relief="groove", padx=8).pack(
                       side="left", fill="x", expand=True, padx=(0, 3))
        tk.Button(trace_actions, text="Latest", command=self.show_latest_recordings,
                  bg="#e8f1f8", fg=self.NAVY, relief="groove", padx=10).pack(
                      side="left", fill="x", expand=True, padx=(3, 0))
        self.trace_figure = Figure(figsize=(7.4, 5.2), dpi=100, facecolor=self.CARD)
        self.trace_axis = self.trace_figure.add_subplot(111)
        self.trace_canvas = FigureCanvasTkAgg(self.trace_figure, master=self.trace_card)
        self.trace_canvas.get_tk_widget().pack(fill="both", expand=True, padx=4)
        self.trace_scrollbar = ttk.Scrollbar(self.trace_card, orient="horizontal",
                                             command=self._scroll_trace)
        self.trace_scrollbar.pack(fill="x", padx=10, pady=(1, 7))

        results_tab.grid_rowconfigure(1, weight=1)
        results_tab.grid_columnconfigure(0, weight=1)
        result_header = tk.Frame(results_tab, bg=self.CARD,
                                 highlightbackground="#cbd8e2", highlightthickness=1)
        result_header.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self.result_label = tk.Label(result_header,
                                     text="Unknown concentration: Not estimated",
                                     bg=self.CARD, fg=self.RED,
                                     font=("Segoe UI", 10, "bold"),
                                     justify="left", anchor="w", wraplength=720,
                                     padx=10, pady=7)
        self.result_label.pack(fill="x")
        result_header.bind("<Configure>", self._resize_result_label)

        result_body = tk.Frame(results_tab, bg=self.BG)
        result_body.grid(row=1, column=0, sticky="nsew")
        result_body.grid_rowconfigure(0, weight=3)
        result_body.grid_rowconfigure(1, weight=2)
        result_body.grid_columnconfigure(0, weight=1)
        drc_card = tk.Frame(result_body, bg=self.CARD,
                            highlightbackground="#cbd8e2", highlightthickness=1)
        drc_card.grid(row=0, column=0, sticky="nsew")
        self.drc_figure = Figure(figsize=(8.2, 3.7), dpi=100, facecolor=self.CARD)
        self.drc_axis = self.drc_figure.add_subplot(111)
        self.drc_canvas = FigureCanvasTkAgg(self.drc_figure, master=drc_card)
        self.drc_canvas.get_tk_widget().pack(fill="both", expand=True)

        record_card = tk.Frame(result_body, bg=self.CARD,
                               highlightbackground="#cbd8e2", highlightthickness=1)
        record_card.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        tk.Label(record_card, text="OBSERVATION TABLE", bg=self.CARD, fg=self.NAVY,
                 font=("Segoe UI", 9, "bold"), anchor="w", padx=9, pady=5).pack(fill="x")
        holder = tk.Frame(record_card, bg=self.CARD)
        holder.pack(fill="both", expand=True, padx=8, pady=(0, 7))
        columns = ("trial", "solution", "dose", "response", "height", "wash")
        self.record_table = ttk.Treeview(holder, columns=columns, show="headings",
                                         height=6, style="Bio.Treeview")
        headings = {"trial": "Trial", "solution": "Solution", "dose": "Dose added",
                    "response": "Response", "height": "Measured height", "wash": "Cycle"}
        widths = {"trial": 55, "solution": 125, "dose": 170,
                  "response": 105, "height": 125, "wash": 105}
        for column in columns:
            self.record_table.heading(column, text=headings[column])
            self.record_table.column(column, width=widths[column], minwidth=50,
                                     anchor="center", stretch=True)
        scroll_y = ttk.Scrollbar(holder, orient="vertical", command=self.record_table.yview)
        scroll_x = ttk.Scrollbar(holder, orient="horizontal", command=self.record_table.xview)
        self.record_table.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        self.record_table.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        holder.grid_rowconfigure(0, weight=1)
        holder.grid_columnconfigure(0, weight=1)

    def _resize_result_label(self, event):
        self.result_label.configure(wraplength=max(250, event.width - 24))

    def _reflow_live_area(self, event):
        compact = event.width < 780
        if compact == self._live_compact:
            return
        self._live_compact = compact
        self.organ_card.grid_forget()
        self.trace_card.grid_forget()
        self.compact_switch.grid_forget()
        for row in (0, 1, 2):
            self.live_area.grid_rowconfigure(row, weight=0)
        for column in (0, 1):
            self.live_area.grid_columnconfigure(column, weight=0)
        if compact:
            self.compact_switch.grid(row=0, column=0, sticky="ew", pady=(0, 5))
            self.live_area.grid_rowconfigure(1, weight=1)
            self.live_area.grid_columnconfigure(0, weight=1)
            self._show_compact_panel(self._compact_panel)
        else:
            self.organ_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
            self.trace_card.grid(row=0, column=1, sticky="nsew")
            self.live_area.grid_rowconfigure(0, weight=1)
            self.live_area.grid_columnconfigure(0, weight=2)
            self.live_area.grid_columnconfigure(1, weight=5)

    def _show_compact_panel(self, panel):
        """Give each live display enough height on a small laptop screen."""
        self._compact_panel = "organ" if panel == "organ" else "trace"
        if not self._live_compact:
            return
        self.organ_card.grid_forget()
        self.trace_card.grid_forget()
        if self._compact_panel == "organ":
            self.organ_card.grid(row=1, column=0, sticky="nsew")
            self.organ_view_button.configure(bg=self.BLUE, fg="white")
            self.trace_view_button.configure(bg="#e8f1f8", fg=self.NAVY)
        else:
            self.trace_card.grid(row=1, column=0, sticky="nsew")
            self.organ_view_button.configure(bg="#e8f1f8", fg=self.NAVY)
            self.trace_view_button.configure(bg=self.BLUE, fg="white")

    def _method_changed(self, _event=None):
        notes = {
            "Interpolation": "Use standards below and above one unknown test response.",
            "Three point": "Use two standard levels and one unknown test fraction in the middle response range.",
            "Four point": "Use two standard levels and two test fractions. Similar slopes are required.",
        }
        self.teaching_note.configure(text=notes[self.method_var.get()])

    def update_solution_controls(self, _event=None):
        if self._control_solution == "Standard ACh":
            self._standard_entry = (self.dose_var.get(), self.unit_var.get())
        else:
            self._test_entry = (self.dose_var.get(), self.unit_var.get())
        current = self.solution_var.get()
        self._control_solution = current
        if current == "Standard ACh":
            self.dose_field_label.configure(text="ACh concentration")
            self.dose_var.set(self._standard_entry[0])
            self.unit_box.configure(values=self.CONCENTRATION_UNITS)
            unit = self._standard_entry[1]
            self.unit_var.set(unit if unit in self.CONCENTRATION_UNITS else "µg/mL")
            self.dose_entry.configure(values=("0.05", "0.10", "0.20", "0.40", "0.80", "1.60", "3.20"))
            self.dose_help.configure(
                text="Enter the final concentration present in the organ bath. No bath volume is assumed.")
        else:
            self.dose_field_label.configure(text="Unknown dose fraction")
            self.dose_var.set(self._test_entry[0])
            self.unit_box.configure(values=self.TEST_DILUTION_UNITS)
            unit = self._test_entry[1]
            self.unit_var.set(unit if unit in self.TEST_DILUTION_UNITS else "× stock")
            self.dose_entry.configure(values=("0.25", "0.50", "0.75", "1.00"))
            self.dose_help.configure(
                text="Enter the fraction of hidden stock used, for example 0.5 times stock or 50 percent stock.")

    def _parse_positive(self, value, field_name):
        try:
            numeric = float(str(value).strip())
        except (TypeError, ValueError):
            raise ValueError("Enter a valid number for {}.".format(field_name))
        if not np.isfinite(numeric) or numeric <= 0:
            raise ValueError("{} must be a positive finite number.".format(field_name))
        return numeric

    def _test_fraction(self, value, unit):
        numeric = self._parse_positive(value, "unknown dose fraction")
        if unit == "% stock":
            return numeric / 100.0
        if unit == "× stock":
            return numeric
        raise ValueError("Select a valid unknown stock fraction unit.")

    def measured_response(self, concentration_um):
        # Keep the measured peak on the scientific Hill relation so every
        # increase in ACh concentration gives a nondecreasing response. A tiny
        # pen movement is added only to the drawn trace, not to the measured
        # contraction used for calculation.
        return float(self.response_from_micromolar(concentration_um))

    def contraction_segment(self, peak):
        local_time = np.linspace(0.0, 90.0, 181)
        response = np.zeros_like(local_time)
        active = local_time >= 5.0
        response[active] = peak * (1.0 - np.exp(-(local_time[active] - 5.0) / 8.0))
        late = local_time >= 35.0
        response[late] = peak * (0.985 + 0.012 * np.sin(local_time[late] / 5.5))
        response += self.rng.normal(0.0, 0.045, size=response.shape)
        return local_time, np.clip(response, 0.0, peak)

    def administer_solution(self):
        if not self._teacher_stock_is_configured():
            messagebox.showwarning(
                "Teacher setup required",
                "A teacher must configure the hidden unknown ACh stock before any dose can be recorded.",
                parent=self.master,
            )
            self.teaching_note.configure(
                text="Open Teacher Setup and save a positive stock concentration first."
            )
            return
        if not self.is_washed:
            messagebox.showwarning(
                "Wash required",
                "Wash the tissue and allow the tracing to return to baseline before the next dose.",
                parent=self.master)
            return
        try:
            input_value = self._parse_positive(self.dose_var.get(), "dose or concentration")
            unit = self.unit_var.get()
            is_standard = self.solution_var.get() == "Standard ACh"
            if is_standard:
                effective_um = self.convert_to_micromolar(input_value, unit)
                dose_label = "{} {} final bath".format(self._format_number(input_value), unit)
                solution, test_fraction = "Standard ACh", None
                short_label = "S {} {}".format(self._format_number(input_value), unit)
                self._standard_entry = (self.dose_var.get(), unit)
            else:
                test_fraction = self._test_fraction(input_value, unit)
                effective_um = self.unknown_concentration_um * test_fraction
                dose_label = "{} {}".format(self._format_number(input_value), unit)
                solution = "Unknown ACh test"
                short_label = "T {}".format(dose_label)
                self._test_entry = (self.dose_var.get(), unit)
        except ValueError as error:
            messagebox.showerror("Invalid dose", str(error), parent=self.master)
            return

        response = self.measured_response(effective_um)
        local_time, contraction = self.contraction_segment(response)
        shifted_time = local_time + self.time_cursor
        colour = self.BLUE if is_standard else self.RED
        self.trace_segments.append({
            "time": shifted_time, "response": contraction, "label": short_label,
            "colour": colour, "peak": response, "trial": self.trial_number + 1,
            "is_wash": False,
        })
        self.time_cursor = float(shifted_time[-1])
        self.current_peak = response
        self.is_washed = False
        self.trial_number += 1
        self.records.append({
            "trial": self.trial_number, "solution": solution,
            "input_value": input_value, "input_unit": unit,
            "dose_label": dose_label, "effective_um": effective_um,
            "test_fraction": test_fraction, "response": response, "washed": False,
        })
        self.last_estimate_um, self.last_calculation, self.last_result_text = None, None, ""
        self.result_label.configure(text="Unknown concentration: Not estimated", fg=self.RED)
        self.show_latest_recordings(redraw=False)
        self.refresh_table()
        self.refresh_graphs()
        self.organ_bath.set_state(response / self.EMAX_MM * 100.0,
                                  "In bath: {}".format(short_label), False)
        if response < self.EMAX_MM * 0.10:
            guidance = "The response is very low. Use a higher level for reliable quantitative comparison."
        elif response > self.EMAX_MM * 0.90:
            guidance = "The response is near maximum. Use a lower level in the middle response range."
        elif is_standard:
            guidance = "Standard response recorded. Wash the tissue, then continue the planned standard and test sequence."
        else:
            guidance = "Unknown test response recorded without revealing the stock concentration. Wash before the next dose."
        self.teaching_note.configure(text=guidance)

    def wash_tissue(self):
        if self.is_washed:
            messagebox.showinfo("Wash", "The tissue is already at baseline.", parent=self.master)
            return
        local_time = np.linspace(0.0, 45.0, 91)
        relaxation = self.current_peak * np.exp(-local_time / 8.5)
        shifted_time = local_time + self.time_cursor
        self.trace_segments.append({
            "time": shifted_time, "response": relaxation, "label": "Wash",
            "colour": self.GREEN, "peak": self.current_peak,
            "trial": self.trial_number, "is_wash": True,
        })
        self.time_cursor = float(shifted_time[-1]) + 10.0
        self.current_peak, self.is_washed = 0.0, True
        if self.records:
            self.records[-1]["washed"] = True
        self.show_latest_recordings(redraw=False)
        self.refresh_table()
        self.refresh_graphs()
        self.organ_bath.set_state(0.0, "Bath washed and baseline restored", True)
        self.teaching_note.configure(
            text="Washing removes acetylcholine and reduces carry over and desensitisation. The next dose may now be added.")

    def _group_means(self, records, key):
        keys, grouped = [], []
        for record in records:
            value = float(record[key])
            found = None
            for index, existing in enumerate(keys):
                if math.isclose(value, existing, rel_tol=1.0e-9, abs_tol=1.0e-12):
                    found = index
                    break
            if found is None:
                keys.append(value)
                grouped.append([float(record["response"])])
            else:
                grouped[found].append(float(record["response"]))
        return [(keys[index], float(np.mean(values))) for index, values in enumerate(grouped)]

    def _latest_distinct_points(self, records, key, count):
        selected = []
        for record in reversed(records):
            value = float(record[key])
            if not any(math.isclose(value, item, rel_tol=1.0e-9, abs_tol=1.0e-12)
                       for item in selected):
                selected.append(value)
            if len(selected) == count:
                break
        if len(selected) < count:
            return []
        chosen = [record for record in records
                  if any(math.isclose(float(record[key]), item,
                                      rel_tol=1.0e-9, abs_tol=1.0e-12)
                         for item in selected)]
        return self._group_means(chosen, key)

    def calculate_unknown(self):
        if not self._teacher_stock_is_configured():
            messagebox.showwarning(
                "Teacher setup required",
                "Configure the hidden unknown ACh stock before calculating an estimate.",
                parent=self.master,
            )
            return
        standards = [r for r in self.records if r["solution"] == "Standard ACh"]
        tests = [r for r in self.records if r["solution"] == "Unknown ACh test"]
        method = self.method_var.get()
        try:
            if method == "Four point":
                standard_points = self._latest_distinct_points(standards, "effective_um", 2)
                test_points = self._latest_distinct_points(tests, "test_fraction", 2)
                if len(standard_points) < 2 or len(test_points) < 2:
                    raise ValueError("Record two different standard levels and two different unknown test fractions.")
                estimate_um, diagnostics = self.parallel_line_estimate(standard_points, test_points)
                caution = ""
                if diagnostics["slope_difference_percent"] > 30.0:
                    caution = " Slopes differ by {:.1f} percent. Repeat with middle range responses.".format(
                        diagnostics["slope_difference_percent"])
                details = ("Four point parallel line estimate using S1, S2, T1 and T2. "
                           "Common slope {:.2f}.{}").format(diagnostics["common_slope"], caution)
                calculation = {"method": method, "standard_points": standard_points,
                               "test_points": test_points, "diagnostics": diagnostics}
            else:
                standard_points = self._group_means(standards, "effective_um")
                if len(standard_points) < 2 or not tests:
                    if method == "Three point":
                        raise ValueError("Record two different standard levels and one unknown test fraction.")
                    raise ValueError("Record at least two different standards and one unknown test response.")
                if method == "Three point":
                    standard_points = self._latest_distinct_points(standards, "effective_um", 2)
                latest_fraction = float(tests[-1]["test_fraction"])
                matching = [r for r in tests
                            if math.isclose(float(r["test_fraction"]), latest_fraction,
                                            rel_tol=1.0e-9, abs_tol=1.0e-12)]
                test_response = float(np.mean([r["response"] for r in matching]))
                estimate_um, lower, upper = self.interpolation_estimate(
                    standard_points, test_response, latest_fraction)
                details = ("{} estimate from a {:.1f} mm test response bracketed by "
                           "{:.1f} mm and {:.1f} mm standards.").format(
                               method, test_response, lower[1], upper[1])
                calculation = {"method": method, "standard_points": standard_points,
                               "test_points": [(latest_fraction, test_response)],
                               "lower": lower, "upper": upper}
        except (ValueError, OverflowError, FloatingPointError) as error:
            messagebox.showwarning("Cannot calculate", str(error), parent=self.master)
            return
        if not np.isfinite(estimate_um) or estimate_um <= 0:
            messagebox.showwarning("Cannot calculate",
                                   "The observations did not give a valid positive concentration.",
                                   parent=self.master)
            return
        self.last_estimate_um = float(estimate_um)
        self.last_calculation = calculation
        estimate_ug_ml = self.micromolar_to_value(estimate_um, "µg/mL")
        self.last_result_text = (
            "Estimated unknown stock: {} µM  |  {} µg/mL  |  Method: {}"
        ).format(self._format_number(estimate_um), self._format_number(estimate_ug_ml), method)
        self.result_label.configure(text=self.last_result_text, fg=self.GREEN)
        self.teaching_note.configure(text=details)
        self.workspace_notebook.select(1)
        self.refresh_graphs()
        messagebox.showinfo("Bioassay result", self.last_result_text + "\n\n" + details,
                            parent=self.master)

    def estimate_unknown(self):
        """Compatibility alias for the former interpolation button."""
        self.calculate_unknown()

    def check_student_estimate(self):
        if not self._teacher_stock_is_configured():
            messagebox.showwarning(
                "Teacher setup required",
                "Configure the hidden unknown ACh stock before checking an estimate.",
                parent=self.master,
            )
            return
        try:
            entered = self._parse_positive(self.student_estimate_var.get(), "your estimate")
            entered_um = self.convert_to_micromolar(entered, self.student_unit_var.get())
        except ValueError as error:
            messagebox.showerror("Invalid estimate", str(error), parent=self.master)
            return
        error_percent = abs(entered_um - self.unknown_concentration_um) / self.unknown_concentration_um * 100.0
        if error_percent <= 15.0:
            title = "Correct estimate"
            text = "Your estimate is acceptable. Percentage error is {:.1f}.".format(error_percent)
        else:
            title = "Review the calculation"
            text = ("Your estimate is outside the accepted 15 percent range. Percentage error is {:.1f}. "
                    "Check the bracketing responses, dilution correction and wash cycles.").format(error_percent)
        messagebox.showinfo(title, text, parent=self.master)
        self.teaching_note.configure(text=text)

    def refresh_table(self):
        for item in self.record_table.get_children():
            self.record_table.delete(item)
        for record in self.records:
            self.record_table.insert("", "end", values=(
                record["trial"],
                "Standard" if record["solution"] == "Standard ACh" else "Unknown test",
                record["dose_label"],
                "{:.1f}%".format(record["response"] / self.EMAX_MM * 100.0),
                "{:.2f} mm".format(record["response"]),
                "Washed" if record["washed"] else "Wash required"))
        children = self.record_table.get_children()
        if children:
            self.record_table.see(children[-1])

    def _draw_trace_axis(self, axis, show_all=False, annotate=True):
        axis.clear()
        for segment in self.trace_segments:
            axis.plot(segment["time"], segment["response"],
                      color=segment["colour"], linewidth=1.7)
            if annotate and not segment["is_wash"]:
                peak_index = int(np.argmax(segment["response"]))
                peak_time = float(segment["time"][peak_index])
                peak_value = float(segment["peak"])
                axis.vlines(peak_time, 0, peak_value, color=segment["colour"],
                            linestyle=":", linewidth=0.9, alpha=0.65)
                axis.annotate("{}\n{:.2f} mm".format(segment["label"], peak_value),
                              xy=(peak_time, peak_value), xytext=(0, 7),
                              textcoords="offset points", ha="center", va="bottom",
                              fontsize=7, color=segment["colour"])
        axis.set_title("Continuous kymograph recording", fontsize=10, color=self.NAVY)
        axis.set_xlabel("Time in seconds", fontsize=9)
        axis.set_ylabel("Contraction height in mm", fontsize=9)
        axis.set_ylim(0, self.EMAX_MM * 1.18)
        axis.grid(True, alpha=0.17)
        total = max(self.time_cursor, self.trace_window_seconds)
        if show_all or self.show_all_trace:
            axis.set_xlim(0, max(total, 90.0))
        else:
            max_start = max(0.0, total - self.trace_window_seconds)
            self.trace_view_start = float(np.clip(self.trace_view_start, 0.0, max_start))
            axis.set_xlim(self.trace_view_start,
                          self.trace_view_start + self.trace_window_seconds)

    def _standard_plot_points(self):
        standards = [r for r in self.records if r["solution"] == "Standard ACh"]
        return sorted(self._group_means(standards, "effective_um"), key=lambda point: point[0])

    def _test_plot_points(self):
        if self.last_estimate_um is None:
            return []
        tests = [r for r in self.records if r["solution"] == "Unknown ACh test"]
        means = self._group_means(tests, "test_fraction")
        return sorted(((self.last_estimate_um * fraction, response, fraction)
                       for fraction, response in means), key=lambda point: point[0])

    def _draw_drc_axis(self, axis, annotate=True):
        axis.clear()
        standards, tests = self._standard_plot_points(), self._test_plot_points()
        all_x = [p[0] for p in standards] + [p[0] for p in tests]
        if all_x:
            minimum = max(min(all_x) / 4.0, 1.0e-6)
            maximum = max(max(all_x) * 4.0, minimum * 100.0)
        else:
            minimum, maximum = 0.05, 50.0
        curve_x = np.logspace(math.log10(minimum), math.log10(maximum), 220)
        curve_y = [self.response_from_micromolar(value) for value in curve_x]
        axis.semilogx(curve_x, curve_y, linestyle="--", color="#9aa9b5",
                      linewidth=1.1, label="Expected graded response")
        if standards:
            axis.semilogx([p[0] for p in standards], [p[1] for p in standards],
                          "o-", color=self.BLUE, linewidth=1.8, markersize=5,
                          label="Standard ACh")
            if annotate:
                for concentration, response in standards:
                    axis.annotate("S\n{:.2f} mm".format(response),
                                  (concentration, response), xytext=(0, 7),
                                  textcoords="offset points", ha="center",
                                  fontsize=7, color=self.BLUE)
        if tests:
            axis.semilogx([p[0] for p in tests], [p[1] for p in tests],
                          "s-", color=self.RED, linewidth=1.6, markersize=5,
                          label="Unknown test at estimated concentration")
            if annotate:
                for concentration, response, fraction in tests:
                    axis.annotate("T {}×\n{:.2f} mm".format(
                        self._format_number(fraction), response),
                        (concentration, response), xytext=(0, -20),
                        textcoords="offset points", ha="center",
                        fontsize=7, color=self.RED)
        axis.set_title("Acetylcholine concentration response curve", fontsize=10,
                       color=self.NAVY)
        axis.set_xlabel("Final bath concentration of ACh in µM  logarithmic scale",
                        fontsize=9)
        axis.set_ylabel("Contraction height in mm", fontsize=9)
        axis.set_ylim(0, self.EMAX_MM * 1.18)
        axis.grid(True, which="both", alpha=0.17)
        axis.legend(fontsize=7, loc="best")

    def refresh_graphs(self):
        self._draw_trace_axis(self.trace_axis, show_all=False, annotate=True)
        self.trace_figure.tight_layout(pad=1.1)
        self.trace_canvas.draw_idle()
        self._update_trace_scrollbar()
        self._draw_drc_axis(self.drc_axis, annotate=True)
        self.drc_figure.tight_layout(pad=1.1)
        self.drc_canvas.draw_idle()

    def _update_trace_scrollbar(self):
        total = max(self.time_cursor, self.trace_window_seconds)
        if self.show_all_trace or total <= self.trace_window_seconds:
            self.trace_scrollbar.set(0.0, 1.0)
            return
        first = self.trace_view_start / total
        last = min(1.0, (self.trace_view_start + self.trace_window_seconds) / total)
        self.trace_scrollbar.set(first, last)

    def _scroll_trace(self, *args):
        total = max(self.time_cursor, self.trace_window_seconds)
        max_start = max(0.0, total - self.trace_window_seconds)
        if max_start <= 0:
            return
        self.show_all_trace = False
        if args[0] == "moveto":
            self.trace_view_start = float(np.clip(float(args[1]) * total, 0.0, max_start))
        elif args[0] == "scroll":
            step = self.trace_window_seconds * (0.78 if args[2] == "pages" else 0.10)
            self.trace_view_start = float(np.clip(
                self.trace_view_start + int(args[1]) * step, 0.0, max_start))
        self._draw_trace_axis(self.trace_axis, show_all=False, annotate=True)
        self.trace_figure.tight_layout(pad=1.1)
        self.trace_canvas.draw_idle()
        self._update_trace_scrollbar()

    def show_all_recordings(self):
        self.show_all_trace, self.trace_view_start = True, 0.0
        self._draw_trace_axis(self.trace_axis, show_all=True, annotate=True)
        self.trace_figure.tight_layout(pad=1.1)
        self.trace_canvas.draw_idle()
        self._update_trace_scrollbar()

    def show_latest_recordings(self, redraw=True):
        self.show_all_trace = False
        total = max(self.time_cursor, self.trace_window_seconds)
        self.trace_view_start = max(0.0, total - self.trace_window_seconds)
        if redraw:
            self._draw_trace_axis(self.trace_axis, show_all=False, annotate=True)
            self.trace_figure.tight_layout(pad=1.1)
            self.trace_canvas.draw_idle()
            self._update_trace_scrollbar()

    def _build_export_figure(self):
        row_count = max(len(self.records), 1)
        figure_width = max(12.0, min(24.0, 8.0 + row_count * 0.65))
        figure_height = max(9.0, min(22.0, 7.2 + row_count * 0.30))
        figure = Figure(figsize=(figure_width, figure_height), dpi=160, facecolor="white")
        trace_axis = figure.add_axes((0.08, 0.66, 0.88, 0.25))
        drc_axis = figure.add_axes((0.08, 0.37, 0.88, 0.21))
        table_axis = figure.add_axes((0.04, 0.04, 0.92, 0.25))
        self._draw_trace_axis(trace_axis, show_all=True, annotate=True)
        self._draw_drc_axis(drc_axis, annotate=True)
        table_axis.axis("off")
        rows = []
        for record in self.records:
            rows.append([
                str(record["trial"]),
                "Standard" if record["solution"] == "Standard ACh" else "Unknown test",
                record["dose_label"],
                "{:.1f}%".format(record["response"] / self.EMAX_MM * 100.0),
                "{:.2f} mm".format(record["response"]),
                "Washed" if record["washed"] else "Wash required",
            ])
        if not rows:
            rows = [["", "No observation recorded", "", "", "", ""]]
        table = table_axis.table(
            cellText=rows,
            colLabels=("Trial", "Solution", "Dose added", "Response",
                       "Measured height", "Cycle"),
            cellLoc="center", colLoc="center", loc="center",
            colWidths=(0.07, 0.16, 0.24, 0.13, 0.17, 0.15))
        table.auto_set_font_size(False)
        table.set_fontsize(7.5)
        table.scale(1.0, 1.25)
        for (row, _column), cell in table.get_celld().items():
            if row == 0:
                cell.set_facecolor("#dceaf5")
                cell.set_text_props(weight="bold", color=self.NAVY)
            elif row % 2 == 0:
                cell.set_facecolor("#f5f9fc")
        table_axis.set_title("Observation table", color=self.NAVY, fontsize=11, pad=5)
        subtitle = self.last_result_text or "Unknown concentration not yet estimated"
        figure.suptitle("Bioassay of acetylcholine on frog rectus abdominis\n{}".format(subtitle),
                        fontsize=14, fontweight="bold", color=self.NAVY, y=0.98)
        return figure

    def export_results_to(self, path):
        """Save a complete labelled PNG result sheet and return its path."""
        path = os.path.abspath(path)
        root, extension = os.path.splitext(path)
        if extension.lower() != ".png":
            path = root + ".png"
        figure = self._build_export_figure()
        figure.savefig(path, dpi=180, facecolor="white")
        figure.clear()
        return path

    def export_results_image(self):
        if not self.records:
            messagebox.showwarning("No observations",
                                   "Record at least one dose before saving the result image.",
                                   parent=self.master)
            return
        path = filedialog.asksaveasfilename(
            parent=self.master, title="Save bioassay result image",
            defaultextension=".png", filetypes=(("PNG image", "*.png"),),
            initialfile="ACh_bioassay_results.png")
        if not path:
            return
        try:
            saved_path = self.export_results_to(path)
        except (OSError, ValueError) as error:
            messagebox.showerror("Could not save image", str(error), parent=self.master)
            return
        messagebox.showinfo("Image saved",
                            "The complete labelled result image was saved at:\n{}".format(saved_path),
                            parent=self.master)

    def reset_experiment(self, confirm=True):
        if confirm and self.records and not messagebox.askyesno(
                "Reset observations",
                "Clear all observations? The teacher-configured hidden stock will be kept.",
                parent=self.master):
            return
        self.records, self.trace_segments = [], []
        self.time_cursor, self.current_peak, self.trial_number = 0.0, 0.0, 0
        self.is_washed, self.show_all_trace, self.trace_view_start = True, False, 0.0
        self.last_estimate_um, self.last_calculation, self.last_result_text = None, None, ""
        self.solution_var.set("Standard ACh")
        self._control_solution = "Standard ACh"
        self._standard_entry, self._test_entry = ("0.20", "µg/mL"), ("0.50", "× stock")
        self.dose_var.set("0.20")
        self.unit_box.configure(values=self.CONCENTRATION_UNITS)
        self.unit_var.set("µg/mL")
        self.dose_field_label.configure(text="ACh concentration")
        self.dose_help.configure(
            text="Enter the final concentration present in the organ bath. No bath volume is assumed.")
        self.student_estimate_var.set("")
        self.result_label.configure(text="Unknown concentration: Not estimated", fg=self.RED)
        self._update_teacher_setup_state()
        if self._teacher_stock_is_configured():
            note = ("Observations cleared. The teacher-configured hidden stock was retained. "
                    "Start with submaximal standards and wash after every dose.")
        else:
            note = ("Teacher setup is required first. Configure the hidden unknown "
                    "stock before any dose can be recorded.")
        self.teaching_note.configure(text=note)
        self.refresh_table()
        self.refresh_graphs()
        self.organ_bath.set_state(0.0, "Bath ready with Frog Ringer solution", True)
