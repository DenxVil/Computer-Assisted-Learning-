import tkinter as tk
from tkinter import messagebox, ttk

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ui.display import set_window_size
from experiments.dog_bp_model import (
    BASELINE_DBP,
    BASELINE_HR,
    BASELINE_MAP,
    BASELINE_SBP,
    DOSE_METADATA,
    simulate_response,
    validate_dose,
)

class DogBPSimulation:
    """Teaching practical for the simulated dog blood pressure experiment."""

    WINDOW_DURATION = 60
    BASELINE_SBP = BASELINE_SBP
    BASELINE_DBP = BASELINE_DBP
    BASELINE_MEAN_BP = BASELINE_MAP
    BASELINE_HR = BASELINE_HR
    NORMAL_MEAN_BP_RANGE = (80.0, 120.0)
    AGONISTS = [
        "Epinephrine", "Norepinephrine", "Isoprenaline",
        "Acetylcholine", "Histamine", "Ephedrine", "Saline",
    ]
    BLOCKERS = ["Phenoxybenzamine", "Propranolol", "Atropine", "Saline"]

    THEORY_TEXT = """DOG BLOOD PRESSURE EXPERIMENT

Aim

This experiment demonstrates the effect of autonomic drugs on arterial blood pressure and pulse rate. The simulator gives the expected pattern without using a live animal.

Basic principle

Arterial blood pressure depends mainly on cardiac output and total peripheral resistance. Cardiac output depends on heart rate and stroke volume. Sympathetic and parasympathetic drugs can change one or more of these factors.

In the classical experiment, an anaesthetised dog was used. The carotid artery was connected to a pressure recording system. Drugs were injected through a venous cannula and the blood pressure response was recorded on a kymograph. This computer practical reproduces the important response patterns for teaching.

Epinephrine

Epinephrine stimulates alpha 1, beta 1 and beta 2 receptors. The teaching trace shows its classical biphasic response after an intravenous dose: an early pressor phase from alpha 1 vasoconstriction and beta 1 cardiac stimulation, followed by a beta 2 depressor phase. Changing the dose changes the relative size of these components. After alpha blockade the depressor component becomes dominant.

Norepinephrine

Norepinephrine mainly stimulates alpha receptors and beta 1 receptors. It produces a marked rise in blood pressure. The baroreceptor reflex usually causes bradycardia even though the drug has a direct cardiac stimulant action.

Isoprenaline

Isoprenaline stimulates beta 1 and beta 2 receptors. Beta 2 vasodilatation lowers peripheral resistance and blood pressure. Beta 1 stimulation produces a marked increase in pulse rate.

Acetylcholine

Acetylcholine stimulates muscarinic M3 receptors in blood vessels and releases nitric oxide. This lowers blood pressure. Stimulation of cardiac M2 receptors slows the pulse. Atropine blocks these muscarinic responses. After sufficient atropine, a large dose of acetylcholine may show a nicotinic pressor response due to autonomic ganglia and adrenal medulla stimulation.

Histamine

Histamine activates vascular H1 and H2 receptors and produces a rapid, short-lived fall in mean blood pressure through vasodilatation. Pulse rate may rise modestly through the baroreceptor reflex, although the cardiac response can vary with anaesthesia and experimental conditions.

Ephedrine

Ephedrine acts mainly by releasing stored norepinephrine from sympathetic nerve endings. It raises blood pressure and pulse rate. Repeated equal doses give progressively smaller responses because the stored transmitter becomes depleted. This is called tachyphylaxis.

Antagonists

Phenoxybenzamine produces long lasting alpha receptor blockade. After this drug, the alpha pressor action of epinephrine is blocked and the beta 2 depressor action becomes prominent. This is called vasomotor reversal of Dale.

Propranolol blocks beta 1 and beta 2 receptors. Its beta 1 action lowers pulse rate and cardiac output, so the simulator now shows a modest, gradual fall in mean blood pressure as well as a clearer fall in pulse rate. The acute pressure change is smaller and more variable than the pulse-rate change. It also reduces the response to isoprenaline and removes the beta component of the epinephrine response.

Atropine blocks muscarinic receptors. It prevents the usual fall in blood pressure and bradycardia produced by acetylcholine.

Saline is used as a control and should not produce an important pharmacological response.

Interpretation

The graph shows systolic blood pressure (SBP) and diastolic blood pressure (DBP) in mmHg, with heart rate on the right axis. The teaching baseline is 120/80 mmHg, giving a calculated mean arterial pressure (MAP) of about 93 mmHg. The observation log reports the maximum rise and fall in MAP rather than replacing the arterial-pressure traces with a mean-only line. The response pattern, direction, time course and effect of pretreatment help identify receptor action. These are mechanism-consistent teaching curves, not predictions for an individual animal.
"""

    PRACTICAL_TEXT = """DOG BLOOD PRESSURE TEACHING PRACTICAL

Aim

To observe the effects of autonomic drugs on blood pressure and pulse rate and to demonstrate receptor blockade, vasomotor reversal and tachyphylaxis.

Simulated setup

The baseline arterial pressure is 120/80 mmHg, the calculated baseline MAP is about 93 mmHg and the baseline heart rate is 80 beats per minute. The left axis shows SBP and DBP in mmHg. The right axis shows heart rate. Each injection is recorded for 60 seconds. The observation table gives the dose and the rise/fall in calculated MAP.

How to perform the practical

Step 1

Allow the baseline recording to be seen. Select Saline and inject it as a control. There should be no important change.

Step 2

Select a drug and enter a dose within the displayed teaching range. Catecholamines and similar agonists are entered in microgram/kg; the larger blocker and ephedrine doses are displayed in mg/kg. Observe the direction and size of the systolic, diastolic and heart-rate responses.

Step 3

Use Reset Preparation before starting an independent comparison. Resetting removes all earlier pretreatment and returns the preparation to baseline.

Step 4

For a blockade study, first inject the selected blocker. Do not reset. Then inject the agonist. The simulator remembers the blocker given in the same preparation.

Suggested study one

Compare epinephrine, norepinephrine, isoprenaline, acetylcholine and histamine in separate preparations. Note whether mean blood pressure rises or falls, whether the response is sharp or gradual, and whether the pulse becomes faster or slower. Acetylcholine and histamine give rapid depressor responses; ephedrine and the blocker responses develop more gradually.

Suggested study two

Inject phenoxybenzamine and then inject epinephrine without resetting. The pressor response changes to a depressor response because beta 2 vasodilatation remains. This demonstrates vasomotor reversal of Dale.

Suggested study three

Inject propranolol and then inject isoprenaline without resetting. The fall in blood pressure and the rise in pulse should be markedly reduced because beta receptors are blocked.

Suggested study four

Inject atropine and then inject acetylcholine without resetting. The usual muscarinic fall in blood pressure and pulse is blocked. A sufficiently large acetylcholine dose may show a nicotinic pressor response.

Tachyphylaxis study

Reset the preparation. Give the same dose of ephedrine repeatedly without resetting. Compare each peak with the previous peak. The response becomes smaller with repeated doses.

Recording the observation

For every injection, record the drug name, dose, maximum rise and fall in MAP, heart-rate change and the direction and time course of the response. Read the explanation below the graph. Use the complete SBP/DBP pattern and not only one value while interpreting the drug action.

Important points

Use the same dose when comparing responses. Give the blocker before the agonist. Do not reset between pretreatment and the test agonist. Reset before starting a new independent experiment. This is a teaching simulation and no clinical dose decision should be made from it.
"""

    def __init__(self, master):
        self.master = master
        self.master.title("Dog Blood Pressure Teaching Practical")
        set_window_size(
            self.master, 1180, 760, 720, 520,
            margin_x=50, margin_y=70, expand_large=True,
        )
        self.master.configure(bg="#eef4f8")

        self.baseline_sbp = self.BASELINE_SBP
        self.baseline_dbp = self.BASELINE_DBP
        self.baseline_map = self.BASELINE_MEAN_BP
        self.baseline_hr = self.BASELINE_HR
        self.current_explanation = (
            "Baseline state. Select a known drug, choose the dose and inject it."
        )
        self.injection_history = []
        self.current_offset = 0

        self._build_screen()
        self.update_continuous_graph()

    @staticmethod
    def response_profile(t, onset=3.0, rise=1.5, decay=11.0):
        """Return a normalised injection response with separate rise/decay rates."""
        values = np.asarray(t, dtype=float)
        elapsed = np.maximum(values - onset, 0.0)
        profile = np.where(
            values >= onset,
            (1.0 - np.exp(-elapsed / rise)) * np.exp(-elapsed / decay),
            0.0,
        )
        peak = float(np.max(profile)) if profile.size else 0.0
        return profile / peak if peak > 0.0 else profile

    def _legacy_simulate_drug_effect(self, drug, dose, t, previous_map=None, previous_hr=None):
        t = np.asarray(t, dtype=float)
        noise_map = np.random.normal(0, 0.35, size=t.shape)
        noise_hr = np.random.normal(0, 0.4, size=t.shape)
        if previous_map is None or previous_hr is None:
            previous_map = np.full_like(t, self.baseline_map, dtype=float)
            previous_hr = np.full_like(t, self.baseline_hr, dtype=float)

        # A square-root dose scale keeps the full teaching control responsive
        # without allowing large entries to create impossible negative pressure.
        dose_value = max(0.0, float(dose))
        dose_factor = float(np.sqrt(min(dose_value, 2.25)))
        sharp = self.response_profile(t, onset=3.0, rise=0.45, decay=4.5)
        direct = self.response_profile(t, onset=3.0, rise=1.4, decay=11.0)
        gradual = self.response_profile(t, onset=3.0, rise=6.0, decay=25.0)
        delayed = self.response_profile(t, onset=10.0, rise=2.0, decay=13.0)

        previous_drugs = [event.get("drug") for event in self.injection_history]
        alpha_blocked = "Phenoxybenzamine" in previous_drugs
        beta_blocked = "Propranolol" in previous_drugs
        muscarinic_blocked = "Atropine" in previous_drugs

        if drug == "Phenoxybenzamine":
            map_effect = -12 * dose_factor * gradual
            hr_effect = +8 * dose_factor * gradual
            explanation = (
                "Phenoxybenzamine produces a gradual fall in mean BP as alpha "
                "blockade develops; modest reflex tachycardia may occur."
            )
        elif drug == "Propranolol":
            map_effect = -10 * dose_factor * gradual
            hr_effect = -18 * dose_factor * gradual
            explanation = (
                "Propranolol produces a modest, gradual fall in mean BP by "
                "reducing cardiac output, with a clearer fall in pulse rate. "
                "The acute pressure effect is smaller and can vary experimentally."
            )
        elif drug == "Atropine":
            map_effect = np.zeros_like(t)
            hr_effect = +14 * dose_factor * direct
            explanation = (
                "Atropine blocks muscarinic receptors and removes resting vagal "
                "tone, so pulse rate increases with little direct mean-BP change."
            )
        elif drug == "Epinephrine":
            if alpha_blocked:
                map_effect = -38 * dose_factor * direct
                hr_effect = +25 * dose_factor * direct
                explanation = (
                    "Epinephrine after phenoxybenzamine shows vasomotor reversal "
                    "of Dale: beta-2 action lowers mean BP and beta-1 action "
                    "raises pulse rate."
                )
            elif beta_blocked:
                map_effect = +50 * dose_factor * direct
                hr_effect = -13 * dose_factor * delayed
                explanation = (
                    "Epinephrine after propranolol shows a rapid unopposed alpha-1 "
                    "pressor response with reflex slowing of the pulse."
                )
            elif dose_value < 0.5:
                map_effect = -28 * dose_factor * direct
                hr_effect = +20 * dose_factor * direct
                explanation = (
                    "Low-dose epinephrine: beta-2 vasodilatation lowers mean BP "
                    "and beta-1 stimulation raises pulse rate."
                )
            elif dose_value < 1.0:
                map_effect = +28 * dose_factor * direct - 22 * dose_factor * delayed
                hr_effect = +14 * dose_factor * direct
                explanation = "Moderate-dose epinephrine gives a biphasic mean-BP response."
            else:
                map_effect = +50 * dose_factor * direct
                if muscarinic_blocked:
                    hr_effect = +9 * dose_factor * direct
                    explanation = (
                        "High-dose epinephrine after atropine: alpha-1 raises mean "
                        "BP; vagal reflex slowing is blocked."
                    )
                else:
                    hr_effect = -13 * dose_factor * delayed
                    explanation = (
                        "High-dose epinephrine rapidly raises mean BP through "
                        "alpha-1 vasoconstriction, followed by reflex bradycardia."
                    )
        elif drug == "Norepinephrine":
            if alpha_blocked:
                map_effect = +5 * dose_factor * direct
                hr_effect = +4 * dose_factor * direct
                explanation = (
                    "Norepinephrine after phenoxybenzamine has a markedly reduced "
                    "pressor response because most vascular alpha action is blocked."
                )
            else:
                map_effect = +45 * dose_factor * direct
                if muscarinic_blocked:
                    hr_effect = +10 * dose_factor * direct
                    explanation = (
                        "Norepinephrine after atropine raises mean BP; vagal reflex "
                        "bradycardia is blocked, revealing direct beta-1 action."
                    )
                else:
                    hr_effect = -17 * dose_factor * delayed
                    explanation = (
                        "Norepinephrine rapidly raises mean BP through alpha-1 "
                        "vasoconstriction and produces reflex bradycardia."
                    )
        elif drug == "Isoprenaline":
            if beta_blocked:
                map_effect = np.zeros_like(t)
                hr_effect = np.zeros_like(t)
                explanation = (
                    "Isoprenaline after propranolol gives no important response "
                    "because beta receptors are blocked."
                )
            else:
                map_effect = -28 * dose_factor * direct
                hr_effect = +42 * dose_factor * direct
                explanation = (
                    "Isoprenaline rapidly lowers mean BP through beta-2 "
                    "vasodilatation and raises pulse rate through beta-1 stimulation."
                )
        elif drug == "Acetylcholine":
            if muscarinic_blocked:
                if dose_value >= 1.5:
                    map_effect = +18 * dose_factor * direct
                    hr_effect = +11 * dose_factor * direct
                    explanation = (
                        "A large acetylcholine dose after atropine shows a nicotinic "
                        "pressor response from ganglionic and adrenal stimulation."
                    )
                else:
                    map_effect = np.zeros_like(t)
                    hr_effect = np.zeros_like(t)
                    explanation = (
                        "Acetylcholine after atropine gives no important muscarinic response."
                    )
            else:
                map_effect = -38 * dose_factor * sharp
                hr_effect = -24 * dose_factor * sharp
                explanation = (
                    "Acetylcholine gives a sharp, short-lived fall in mean BP "
                    "through M3/NO vasodilatation and slows the pulse through M2 receptors."
                )
        elif drug == "Histamine":
            map_effect = -42 * dose_factor * sharp
            hr_effect = +8 * dose_factor * direct
            explanation = (
                "Histamine gives a sharp, short-lived fall in mean BP through "
                "H1/H2-mediated vasodilatation. A modest reflex pulse rise is "
                "shown; the cardiac response may vary with experimental conditions."
            )
        elif drug == "Ephedrine":
            prior_doses = sum(
                event.get("drug") == "Ephedrine" for event in self.injection_history
            )
            remaining_effect = 0.5 ** prior_doses
            map_effect = +38 * dose_factor * remaining_effect * gradual
            hr_effect = +18 * dose_factor * remaining_effect * gradual
            explanation = (
                "Ephedrine gives a gradual, sustained pressor response by releasing "
                "stored norepinephrine. Repeated equal doses show tachyphylaxis."
            )
        elif drug == "Saline":
            map_effect = np.zeros_like(t)
            hr_effect = np.zeros_like(t)
            explanation = "Saline is the control and has no important pharmacological effect."
        else:
            map_effect = np.zeros_like(t)
            hr_effect = np.zeros_like(t)
            explanation = "Select a known drug before injection."

        map_curve = np.clip(previous_map + map_effect + noise_map, 35.0, 185.0)
        hr_curve = np.clip(previous_hr + hr_effect + noise_hr, 30.0, 180.0)
        return map_curve, hr_curve, explanation

    def simulate_full_response(self, drug, dose_ug_kg, t):
        """Return the full SBP/DBP/MAP/HR response used by both practicals."""
        return simulate_response(
            drug, dose_ug_kg, t, prior_drugs=self.injection_history,
        )

    def simulate_drug_effect(self, drug, dose, t, previous_map=None, previous_hr=None):
        """Compatibility wrapper for callers that previously requested MAP/HR only."""
        del previous_map, previous_hr
        result = self.simulate_full_response(drug, dose, t)
        return result["map"], result["hr"], result["explanation"]

    def _build_screen(self):
        header = tk.Frame(self.master, bg="#173b57", padx=18, pady=10)
        header.pack(fill="x")
        title_row = tk.Frame(header, bg="#173b57")
        title_row.pack(fill="x")
        tk.Label(
            title_row, text="Dog Blood Pressure Teaching Practical",
            font=("Segoe UI", 18, "bold"), bg="#173b57", fg="white",
        ).pack(side="left", anchor="w")
        tk.Label(
            title_row, text="MAMC, New Delhi", font=("Segoe UI", 8, "bold"),
            bg="#173b57", fg="#cfe2f3",
        ).pack(side="right", padx=(12, 0))
        self.subtitle_label = tk.Label(
            header,
            text="Study known autonomic drugs, receptor blockade and response patterns",
            font=("Segoe UI", 9), bg="#173b57", fg="#cfe2f3",
            justify="left", anchor="w",
        )
        self.subtitle_label.pack(fill="x", pady=(2, 0))

        toolbar = tk.Frame(
            self.master, bg="white", padx=12, pady=7,
            highlightbackground="#cbd8e2", highlightthickness=1,
        )
        toolbar.pack(fill="x")
        tk.Button(
            toolbar, text="Theory",
            command=lambda: self.show_information("Dog BP Theory", self.THEORY_TEXT),
            font=("Segoe UI", 9, "bold"), bg="#eaf3fa", fg="#173b57",
            padx=14, pady=5, cursor="hand2",
        ).pack(side="left", padx=(0, 7))
        tk.Button(
            toolbar, text="Practical Guide",
            command=lambda: self.show_information(
                "Dog BP Practical Guide", self.PRACTICAL_TEXT
            ),
            font=("Segoe UI", 9, "bold"), bg="#eaf3fa", fg="#173b57",
            padx=14, pady=5, cursor="hand2",
        ).pack(side="left")
        self.mode_label = tk.Label(
            toolbar, text="Teaching mode uses known drugs only",
            font=("Segoe UI", 9, "bold"), bg="white", fg="#607789",
        )
        self.mode_label.pack(side="right", padx=(8, 0))

        body = tk.PanedWindow(
            self.master, orient="horizontal", bg="#d5e0e8",
            bd=0, sashwidth=7, sashrelief="flat",
        )
        body.pack(fill="both", expand=True, padx=10, pady=9)

        control_card = tk.Frame(
            body, bg="white", highlightbackground="#cbd8e2", highlightthickness=1,
        )
        body.add(control_card, minsize=210, width=280)
        self._build_scrollable_controls(control_card)

        workspace = tk.Frame(body, bg="#eef4f8")
        body.add(workspace, minsize=320)

        graph_card = tk.Frame(
            workspace, bg="white", highlightbackground="#cbd8e2",
            highlightthickness=1,
        )
        graph_card.pack(fill="both", expand=True)
        graph_header = tk.Frame(graph_card, bg="white", padx=10, pady=3)
        graph_header.pack(fill="x")
        tk.Label(
            graph_header, text="Continuous Recording",
            font=("Segoe UI", 10, "bold"), bg="white", fg="#173b57",
        ).pack(side="left")
        self.peak_label = tk.Label(
            graph_header, text="SBP: —  |  DBP: —",
            font=("Segoe UI", 8, "bold"), bg="white", fg="#607789",
        )
        self.peak_label.pack(side="right")

        # A modest requested height keeps the observation log visible on a
        # 720 by 520 laptop window. The canvas still expands on larger screens.
        self.fig = Figure(figsize=(7.4, 1.3), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_card)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        explanation_card = tk.Frame(
            workspace, bg="#fff8e1", padx=10, pady=4,
            highlightbackground="#e7d99c", highlightthickness=1,
        )
        explanation_card.pack(fill="x", pady=(7, 0))
        self.explanation_label = tk.Label(
            explanation_card, text=self.current_explanation,
            font=("Segoe UI", 9), bg="#fff8e1", fg="#5d5125",
            justify="left", anchor="w",
        )
        self.explanation_label.pack(fill="x")
        explanation_card.bind("<Configure>", self._resize_explanation)

        self._build_observation_log(workspace)
        self.master.bind("<Configure>", self._resize_header, add="+")

    def _build_scrollable_controls(self, parent):
        tk.Button(
            parent, text="Reset Preparation", command=self.reset_simulation,
            font=("Segoe UI", 9, "bold"), bg="#6c757d", fg="white",
            pady=4, cursor="hand2",
        ).pack(side="bottom", fill="x", padx=9, pady=(3, 8))
        canvas = tk.Canvas(parent, bg="white", highlightthickness=0, width=280)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        content = tk.Frame(canvas, bg="white", padx=12, pady=8)
        content_window = canvas.create_window((0, 0), window=content, anchor="nw")

        def update_scroll_region(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def fit_content(event):
            canvas.itemconfigure(content_window, width=max(1, event.width))

        content.bind("<Configure>", update_scroll_region)
        canvas.bind("<Configure>", fit_content)
        self.controls_canvas = canvas
        self.setup_controls(content)

        scroll_tag = "DogTeachingControls{}".format(id(self))

        def scroll_controls(event):
            canvas.yview_scroll(int(-event.delta / 120), "units")

        canvas.bind_class(scroll_tag, "<MouseWheel>", scroll_controls)

        def attach_scroll_tag(widget):
            tags = list(widget.bindtags())
            if scroll_tag not in tags:
                tags.insert(max(len(tags) - 1, 0), scroll_tag)
                widget.bindtags(tuple(tags))
            for child in widget.winfo_children():
                attach_scroll_tag(child)

        attach_scroll_tag(canvas)

    def _build_observation_log(self, parent):
        log_card = tk.Frame(
            parent, bg="white", padx=8, pady=3,
            highlightbackground="#cbd8e2", highlightthickness=1,
        )
        log_card.pack(fill="x", pady=(7, 0))
        tk.Label(
            log_card, text="Observation Log", font=("Segoe UI", 10, "bold"),
            bg="white", fg="#173b57",
        ).pack(anchor="w", pady=(0, 2))
        table_frame = tk.Frame(log_card, bg="white")
        table_frame.pack(fill="x")
        columns = ("trial", "drug", "dose", "map_change", "hr_change", "response")
        self.log_table = ttk.Treeview(
            table_frame, columns=columns, show="headings", height=1,
        )
        headings = {
            "trial": "Trial", "drug": "Known drug", "dose": "Dose",
            "map_change": "Mean BP change: rise / fall (mmHg)",
            "hr_change": "Heart-rate change (bpm)",
            "response": "Main response",
        }
        widths = {
            "trial": 55, "drug": 150, "dose": 120,
            "map_change": 225, "hr_change": 175, "response": 210,
        }
        for column in columns:
            self.log_table.heading(column, text=headings[column])
            self.log_table.column(
                column, width=widths[column], minwidth=widths[column],
                anchor="center", stretch=column == "response",
            )
        vertical = ttk.Scrollbar(table_frame, orient="vertical", command=self.log_table.yview)
        horizontal = ttk.Scrollbar(
            table_frame, orient="horizontal", command=self.log_table.xview
        )
        self.log_table.configure(
            yscrollcommand=vertical.set, xscrollcommand=horizontal.set,
        )
        self.log_table.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        table_frame.columnconfigure(0, weight=1)

        compact_headings = {
            "trial": "Trial", "drug": "Drug", "dose": "Dose",
            "map_change": "ΔMAP + / −", "hr_change": "ΔHR + / −",
            "response": "Pattern",
        }
        compact_fractions = {
            "trial": 0.08, "drug": 0.19, "dose": 0.16,
            "map_change": 0.20, "hr_change": 0.18, "response": 0.19,
        }

        def fit_log_columns(event):
            if event.width < 650:
                usable = max(280, event.width - 22)
                for column in columns:
                    self.log_table.heading(column, text=compact_headings[column])
                    self.log_table.column(
                        column,
                        width=max(28, int(usable * compact_fractions[column])),
                        minwidth=28, stretch=False,
                    )
                horizontal.grid_remove()
            else:
                for column in columns:
                    self.log_table.heading(column, text=headings[column])
                    self.log_table.column(
                        column, width=widths[column], minwidth=widths[column],
                        anchor="center", stretch=column == "response",
                    )
                horizontal.grid()

        table_frame.bind("<Configure>", fit_log_columns)

    def _resize_header(self, event):
        if event.widget is self.master:
            self.subtitle_label.configure(wraplength=max(300, event.width - 45))
            if event.width < 720:
                self.mode_label.configure(text="Known drugs only")
            else:
                self.mode_label.configure(text="Teaching mode uses known drugs only")

    def _resize_explanation(self, event):
        self.explanation_label.configure(wraplength=max(250, event.width - 24))

    def update_continuous_graph(self):
        while len(self.fig.axes) > 1:
            self.fig.delaxes(self.fig.axes[-1])
        self.ax.clear()
        pulse_axis = self.ax.twinx()

        window_end = max(self.WINDOW_DURATION, len(self.injection_history) * 60)
        bp_min, bp_max = 40.0, 175.0
        pulse_min, pulse_max = 30.0, 170.0
        if self.injection_history:
            bp_values = np.concatenate([
                np.concatenate((event["sbp_curve"], event["dbp_curve"]))
                for event in self.injection_history
            ])
            pulse_values = np.concatenate([
                event["hr_curve"] for event in self.injection_history
            ])
            bp_min = min(bp_min, float(np.min(bp_values)) - 8)
            bp_max = max(bp_max, float(np.max(bp_values)) + 8)
            pulse_min = min(pulse_min, float(np.min(pulse_values)) - 8)
            pulse_max = max(pulse_max, float(np.max(pulse_values)) + 8)

        self.ax.plot(
            [0, window_end], [self.baseline_sbp, self.baseline_sbp],
            color="#1769aa", alpha=0.28, linestyle=":", label="SBP",
        )
        self.ax.plot(
            [0, window_end], [self.baseline_dbp, self.baseline_dbp],
            color="#6a3d8f", alpha=0.28, linestyle=":", label="DBP",
        )
        pulse_axis.plot(
            [0, window_end], [self.baseline_hr, self.baseline_hr],
            color="#d33f49", alpha=0.28, linestyle=":", label="Heart rate",
        )
        for event in self.injection_history:
            self.ax.plot(
                event["time_array"], event["sbp_curve"],
                color="#1769aa", linewidth=2,
            )
            self.ax.plot(
                event["time_array"], event["dbp_curve"],
                color="#6a3d8f", linewidth=2,
            )
            self.ax.fill_between(
                event["time_array"], event["dbp_curve"], event["sbp_curve"],
                color="#7aa8cc", alpha=0.055,
            )
            pulse_axis.plot(
                event["time_array"], event["hr_curve"],
                color="#d33f49", linewidth=1.6, linestyle="--",
            )
            start = event["start_time"]
            self.ax.axvline(start, color="#607789", alpha=0.22, linestyle=":")
            self.ax.text(
                start + 2, bp_max - 4, event["drug"], fontsize=8,
                color="#3f5668", va="top", clip_on=True,
            )

        self.ax.set_xlim(0, window_end)
        self.ax.set_ylim(bp_min, bp_max)
        pulse_axis.set_ylim(pulse_min, pulse_max)
        self.ax.set_title(
            "Systolic and diastolic arterial pressure with heart rate",
            fontsize=11, color="#173b57",
        )
        self.ax.set_xlabel("Experimental time in seconds", fontsize=9)
        self.ax.set_ylabel(
            "Blood Pressure\n(mmHg)", color="#1769aa", fontsize=8,
        )
        pulse_axis.set_ylabel(
            "Heart rate\n(beats/min)", color="#d33f49", fontsize=8,
        )
        self.ax.grid(alpha=0.14)
        handles_left, labels_left = self.ax.get_legend_handles_labels()
        handles_right, labels_right = pulse_axis.get_legend_handles_labels()
        self.ax.legend(
            handles_left + handles_right, labels_left + labels_right,
            loc="upper right", fontsize=7, ncol=3, framealpha=0.78,
        )
        self.fig.tight_layout(pad=1.45)
        self.canvas.draw()

    def update_numeric_labels(self, event):
        self.peak_label.configure(
            text=(
                f"SBP {np.min(event['sbp_curve']):.0f}–{np.max(event['sbp_curve']):.0f}  |  "
                f"DBP {np.min(event['dbp_curve']):.0f}–{np.max(event['dbp_curve']):.0f}"
            )
        )

    def update_explanation(self, text):
        self.current_explanation = text
        self.explanation_label.configure(text=text)

    def reset_simulation(self):
        if self.injection_history and not messagebox.askyesno(
            "Reset preparation",
            "Clear all recorded injections and remove all pretreatment?",
            parent=self.master,
        ):
            return
        self.injection_history = []
        self.current_offset = 0
        self.update_continuous_graph()
        self.peak_label.configure(text="SBP: —  |  DBP: —")
        self.update_explanation(
            "Preparation reset to baseline. Earlier blocker and drug effects have been removed."
        )
        for item in self.log_table.get_children():
            self.log_table.delete(item)

    def inject_drug(self, drug, dose):
        time = np.linspace(0, 60, 121)
        result = self.simulate_full_response(drug, dose, time)
        sbp_curve = result["sbp"]
        dbp_curve = result["dbp"]
        map_curve = result["map"]
        hr_curve = result["hr"]
        explanation = result["explanation"]
        event_baseline = result["baseline"]
        start_time = len(self.injection_history) * 60
        map_change = map_curve - event_baseline["map"]
        hr_change = hr_curve - event_baseline["hr"]
        map_rise = max(0.0, float(np.max(map_change)))
        map_fall = min(0.0, float(np.min(map_change)))
        hr_rise = max(0.0, float(np.max(hr_change)))
        hr_fall = min(0.0, float(np.min(hr_change)))
        response = self._response_summary(
            map_rise, map_fall, hr_rise, hr_fall
        )
        metadata = DOSE_METADATA[drug]
        displayed_dose = dose / metadata["display_factor"]
        dose_display = f"{displayed_dose:g} {metadata['display_unit']}"
        new_event = {
            "start_time": start_time,
            "time_array": time + start_time,
            "sbp_curve": sbp_curve,
            "dbp_curve": dbp_curve,
            "map_curve": map_curve,
            "hr_curve": hr_curve,
            "drug": drug,
            "dose": dose,
            "dose_ug_kg": dose,
            "dose_display": dose_display,
            "explanation": explanation,
            "baseline": event_baseline,
            "map_rise": map_rise,
            "map_fall": map_fall,
            "hr_rise": hr_rise,
            "hr_fall": hr_fall,
            "response": response,
        }
        self.injection_history.append(new_event)
        self.current_offset = start_time + 60
        self.update_continuous_graph()
        self.update_numeric_labels(new_event)
        self.update_explanation(explanation)
        self.log_table.insert(
            "", "end", values=(
                len(self.injection_history), drug, dose_display,
                f"+{map_rise:.1f} / {map_fall:.1f}",
                f"+{hr_rise:.1f} / {hr_fall:.1f}", response,
            ),
        )
        children = self.log_table.get_children()
        if children:
            self.log_table.see(children[-1])

    @staticmethod
    def _response_summary(map_rise, map_fall, hr_rise, hr_fall):
        if map_rise > 2.0 and map_fall < -2.0:
            bp_pattern = "MAP ↑ then ↓"
        elif map_rise > 2.0:
            bp_pattern = "MAP ↑"
        elif map_fall < -2.0:
            bp_pattern = "MAP ↓"
        else:
            bp_pattern = "MAP ↔"
        if hr_rise > 2.0 and hr_fall < -2.0:
            hr_pattern = "HR ↑ then ↓"
        elif hr_rise > 2.0:
            hr_pattern = "HR ↑"
        elif hr_fall < -2.0:
            hr_pattern = "HR ↓"
        else:
            hr_pattern = "HR ↔"
        return f"{bp_pattern}; {hr_pattern}"

    def _legacy_setup_controls(self, parent):
        tk.Label(
            parent, text="KNOWN DRUGS • BLOCKER FIRST",
            font=("Segoe UI", 10, "bold"),
            bg="white", fg="#607789",
        ).pack(anchor="w", pady=(0, 5))

        tk.Label(
            parent, text="Dose in microgram per kilogram",
            font=("Segoe UI", 9, "bold"), bg="white", fg="#3f5668",
        ).pack(anchor="w")
        self.dose_var = tk.DoubleVar(value=1.0)
        dose_row = tk.Frame(parent, bg="white")
        dose_row.pack(fill="x", pady=(2, 7))
        self.dose_spinbox = tk.Spinbox(
            dose_row, from_=0.01, to=5.0, increment=0.1,
            textvariable=self.dose_var, format="%.2f",
            font=("Segoe UI", 10), justify="center", width=10,
        )
        self.dose_spinbox.pack(side="left", fill="x", expand=True)
        tk.Label(
            dose_row, text="mcg/kg", font=("Segoe UI", 9),
            bg="white", fg="#607789",
        ).pack(side="left", padx=(7, 0))
        tk.Label(
            parent, text="KNOWN AGONIST", font=("Segoe UI", 10, "bold"),
            bg="white", fg="#607789",
        ).pack(anchor="w", pady=(0, 3))
        self.agonist_var = tk.StringVar(value=self.AGONISTS[0])
        ttk.Combobox(
            parent, textvariable=self.agonist_var, values=self.AGONISTS,
            state="readonly", font=("Segoe UI", 9),
        ).pack(fill="x")
        tk.Button(
            parent, text="Inject Known Agonist",
            command=lambda: self._inject_selected(self.agonist_var),
            font=("Segoe UI", 10, "bold"), bg="#1769aa", fg="white",
            pady=5, cursor="hand2",
        ).pack(fill="x", pady=(4, 8))

        tk.Label(
            parent, text="KNOWN BLOCKER OR CONTROL",
            font=("Segoe UI", 10, "bold"), bg="white", fg="#607789",
        ).pack(anchor="w", pady=(0, 3))
        self.blocker_var = tk.StringVar(value=self.BLOCKERS[0])
        ttk.Combobox(
            parent, textvariable=self.blocker_var, values=self.BLOCKERS,
            state="readonly", font=("Segoe UI", 9),
        ).pack(fill="x")
        tk.Button(
            parent, text="Inject Known Blocker or Control",
            command=lambda: self._inject_selected(self.blocker_var),
            font=("Segoe UI", 9, "bold"), bg="#d68910", fg="white",
            pady=5, cursor="hand2",
        ).pack(fill="x", pady=(4, 7))

        tk.Button(
            parent, text="Reset Preparation", command=self.reset_simulation,
            font=("Segoe UI", 10, "bold"), bg="#6c757d", fg="white",
            pady=5, cursor="hand2",
        ).pack(fill="x")

    def _legacy_valid_dose(self):
        try:
            dose = float(self.dose_var.get())
        except (tk.TclError, TypeError, ValueError):
            dose = 0
        if not 0.01 <= dose <= 5.0:
            messagebox.showwarning(
                "Dose required",
                "Enter a dose from 0.01 to 5.00 microgram per kilogram.",
                parent=self.master,
            )
            self.dose_spinbox.focus_set()
            return None
        return dose

    def _legacy_inject_selected(self, variable):
        dose = self._legacy_valid_dose()
        if dose is not None:
            self.inject_drug(variable.get(), dose)

    def setup_controls(self, parent):
        self.dose_controls = {}
        self._build_dose_section(
            parent, "agonist", "KNOWN AGONIST", self.AGONISTS,
            "Inject Known Agonist", "#1769aa",
        )
        self._build_dose_section(
            parent, "blocker", "KNOWN BLOCKER OR CONTROL", self.BLOCKERS,
            "Inject Known Blocker or Control", "#d68910",
        )
        # Compatibility names used by older launch/test helpers.
        self.dose_var = self.dose_controls["agonist"]["dose_var"]
        self.dose_spinbox = self.dose_controls["agonist"]["spinbox"]

    def _build_dose_section(self, parent, key, heading, drugs, button_text, colour):
        tk.Label(
            parent, text=heading, font=("Segoe UI", 10, "bold"),
            bg="white", fg="#607789",
        ).pack(anchor="w", pady=(0, 3))
        drug_var = tk.StringVar(value=drugs[0])
        combo = ttk.Combobox(
            parent, textvariable=drug_var, values=drugs,
            state="readonly", font=("Segoe UI", 9),
        )
        combo.pack(fill="x")
        dose_row = tk.Frame(parent, bg="white")
        dose_row.pack(fill="x", pady=(4, 0))
        dose_var = tk.StringVar()
        spinbox = tk.Spinbox(
            dose_row, textvariable=dose_var, font=("Segoe UI", 10),
            justify="center", width=9,
        )
        spinbox.pack(side="left", fill="x", expand=True)
        unit_label = tk.Label(
            dose_row, font=("Segoe UI", 9, "bold"), bg="white", fg="#3f5668",
        )
        unit_label.pack(side="left", padx=(7, 0))
        range_label = tk.Label(
            parent, font=("Segoe UI", 8), bg="white", fg="#607789",
            anchor="w",
        )
        range_label.pack(fill="x", pady=(1, 3))
        self.dose_controls[key] = {
            "drug_var": drug_var, "dose_var": dose_var, "spinbox": spinbox,
            "unit_label": unit_label, "range_label": range_label,
        }
        if key == "agonist":
            self.agonist_var = drug_var
        else:
            self.blocker_var = drug_var
        combo.bind(
            "<<ComboboxSelected>>",
            lambda _event, group=key: self._configure_dose_control(group),
        )
        self._configure_dose_control(key)
        tk.Button(
            parent, text=button_text,
            command=lambda group=key: self._inject_group(group),
            font=("Segoe UI", 9, "bold"), bg=colour, fg="white",
            pady=5, cursor="hand2",
        ).pack(fill="x", pady=(1, 8))

    def _configure_dose_control(self, key):
        control = self.dose_controls[key]
        drug = control["drug_var"].get()
        metadata = DOSE_METADATA[drug]
        factor = metadata["display_factor"]
        minimum = metadata["min_ug_kg"] / factor
        maximum = metadata["max_ug_kg"] / factor
        default = metadata["default_ug_kg"] / factor
        control["spinbox"].configure(
            from_=minimum, to=maximum, increment=metadata["step"],
        )
        control["dose_var"].set(f"{default:g}")
        control["unit_label"].configure(text=metadata["display_unit"])
        control["range_label"].configure(
            text=f"Supported range: {minimum:g}–{maximum:g} {metadata['display_unit']}"
        )

    def _valid_group_dose(self, key):
        control = self.dose_controls[key]
        drug = control["drug_var"].get()
        metadata = DOSE_METADATA[drug]
        try:
            displayed_dose = float(control["dose_var"].get())
        except (tk.TclError, TypeError, ValueError):
            displayed_dose = float("nan")
        dose_ug_kg = displayed_dose * metadata["display_factor"]
        valid, warning = validate_dose(drug, dose_ug_kg)
        if not valid:
            messagebox.showwarning(
                "Dose outside teaching range", warning, parent=self.master,
            )
            control["spinbox"].focus_set()
            return None
        return dose_ug_kg

    def _inject_group(self, key):
        dose = self._valid_group_dose(key)
        if dose is not None:
            self.inject_drug(self.dose_controls[key]["drug_var"].get(), dose)

    def _valid_dose(self):
        return self._valid_group_dose("agonist")

    def _inject_selected(self, variable):
        key = "blocker" if variable is self.blocker_var else "agonist"
        self._inject_group(key)

    def show_information(self, title, content):
        window = tk.Toplevel(self.master)
        window.title(title)
        set_window_size(window, 780, 650, 560, 420, margin_x=70, margin_y=90)
        window.configure(bg="#eef4f8")
        header = tk.Frame(window, bg="#173b57", padx=16, pady=10)
        header.pack(fill="x")
        tk.Label(
            header, text=title, font=("Segoe UI", 17, "bold"),
            bg="#173b57", fg="white",
        ).pack(anchor="w")
        bottom = tk.Frame(window, bg="#eef4f8", padx=12, pady=8)
        bottom.pack(side="bottom", fill="x")
        tk.Button(
            bottom, text="Close", command=window.destroy,
            font=("Segoe UI", 10, "bold"), bg="#6c757d", fg="white",
            padx=22, pady=6,
        ).pack(side="right")
        text_frame = tk.Frame(window, bg="white")
        text_frame.pack(fill="both", expand=True, padx=12, pady=10)
        text = tk.Text(
            text_frame, wrap="word", font=("Segoe UI", 10),
            bg="white", fg="#263b4a", padx=16, pady=14,
            relief="flat", spacing1=2, spacing3=5,
        )
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        text.insert("1.0", content.strip())
        text.configure(state="disabled")
        window.transient(self.master)
        window.focus_set()
