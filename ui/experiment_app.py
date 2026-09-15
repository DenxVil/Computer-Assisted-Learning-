import tkinter as tk
from tkinter import messagebox, ttk
import importlib.util
from pathlib import Path
import subprocess
import sys
from PIL import Image, ImageTk

from experiments.dog_bp import DogBPSimulation
from experiments.dog_bp_exam import DogBPExamMode
from experiments.bioassay import BioassaySimulation
from experiments.frog_rectus import FrogRectusSimulation
from experiments.rabbit_eye_practical import RabbitEyeApp
from experiments.combined_exams import (
    RabbitEyeExam,
    CombinedExaminerDashboard,
)
from experiments.quantitative_practicals import (
    BioassayUnknownPractical,
    FrogRectusUnknownPractical,
)
from ui.display import (
    configure_application_display,
    enable_high_dpi,
    set_window_size,
)


THEORY_AND_PRACTICAL_GUIDES = {
    "Dog Blood Pressure": """AIM

To study the effect of autonomic drugs on arterial blood pressure and heart rate in a virtual anaesthetised dog.

THEORY

Arterial blood pressure depends mainly on cardiac output and peripheral vascular resistance. This anaesthetised-dog teaching preparation starts at 120/80 mmHg (calculated MAP about 93 mmHg) with a heart rate of 80 beats/min. Sympathetic and parasympathetic drugs alter systolic pressure, diastolic pressure and heart rate by acting on specific receptors.

Epinephrine, also called adrenaline, stimulates alpha and beta receptors. Its intravenous teaching trace is biphasic: an early alpha 1/beta 1 pressor phase is followed by a beta 2 depressor phase. Dose changes their relative size, and after alpha blockade the depressor component becomes dominant. Norepinephrine produces a rapid alpha-mediated pressor response. Acetylcholine and histamine produce sharp, brief dose-dependent depressor responses. Ephedrine gives a slower, broader pressor response and repeated doses show tachyphylaxis. Atropine blocks muscarinic effects. Propranolol blocks beta receptors and produces a clear gradual fall in heart rate together with a smaller gradual fall in pressure through reduced cardiac output. Phenoxybenzamine blocks alpha receptors.

EXPERIMENTAL SETUP

The virtual dog is anaesthetised. A cannula in the carotid artery is connected to a pressure transducer. A venous cannula is used for giving drugs. The graph shows separate systolic and diastolic pressure traces in mmHg and heart rate with time. Calculated mean-pressure changes are reported in the observation log.

PRACTICAL PROCEDURE

1. Note the 120/80 mmHg baseline arterial pressure and heart rate.
2. Select a known drug and enter a dose within its displayed teaching range and unit.
3. Add the drug and observe the direction, size and duration of the response.
4. Allow the tracing to return near baseline before the next dose.
5. When studying blockade, give the blocker first and then repeat the agonist.
6. Compare the tracing before and after blockade and write the receptor mechanism.

OBSERVATION

Record the drug, dose, maximum rise and fall in calculated mean arterial pressure, change in heart rate, whether the response is sharp or gradual, and the likely receptor involved. The numeric curves are schematic teaching values; direction, timing and antagonist interactions are the learning objectives.

PRECAUTIONS

Use one drug at a time. Read the dose unit carefully. Wait for recovery before the next observation. Interpret both blood pressure and heart rate together.
""",
    "Rabbit Eye": """AIM

To study the local effect of drugs on the rabbit eye and compare the treated eye with the control eye.

THEORY

Pupil size is controlled by the circular sphincter pupillae and radial dilator pupillae muscles. Muscarinic stimulation produces miosis. Muscarinic blockade produces mydriasis and loss of the light reflex. Sympathetic stimulation produces mydriasis. A local anaesthetic can abolish the corneal reflex without changing pupil size.

EXPERIMENTAL SETUP

One eye receives the selected drug. The other eye receives normal saline and acts as control. The ruler, torch, cotton swab, conjunctival inspection and gentle tone examination are used to compare both eyes.

PRACTICAL PROCEDURE

1. Select the drug and select the eye which will receive it.
2. Measure pupil diameter in both eyes with the ruler.
3. Move the torch near each pupil and observe the light reflex.
4. Touch the cornea gently with the cotton swab and observe the corneal reflex.
5. Inspect the conjunctiva for congestion or blanching.
6. Compare ocular tone in both eyes.
7. After the first genuine observation, open the comparison notebook and type your own finding.
8. Save the current test, begin further tests as required, and use the selector to revisit earlier entries. Export the cumulative session table as PNG or CSV when finished.

OBSERVATION

Compare pupil size, light reflex, corneal reflex, conjunctiva and ocular tone. The saline eye provides the normal response for the same animal. The notebook unlocks after an observation and never fills answers automatically. Typed entries remain available across new tests during the current application session.

PRECAUTIONS

Always compare the same parameter in both eyes. Use the cotton swab gently. Do not identify a drug from pupil size alone. Use the complete pattern of findings.
""",
    "Frog Rectus Abdominis": """AIM

To record graded contractions of frog rectus abdominis muscle produced by acetylcholine and to study a concentration response curve.

THEORY

Frog rectus abdominis is a skeletal muscle preparation. Acetylcholine activates nicotinic muscle receptors and produces contraction. Within the useful range, increasing concentration produces an increasing response. At higher concentrations the response approaches a maximum because the available response capacity becomes saturated.

The simulator uses a standard sigmoid concentration response relation. The displayed response is based on the final molar concentration in the organ bath. Physostigmine can enhance the effect of acetylcholine by reducing its breakdown. A competitive nicotinic blocker shifts the concentration response curve to the right.

EXPERIMENTAL SETUP

The muscle is mounted in frog Ringer solution in an organ bath. The lower end is fixed and the upper end is attached to a lever or transducer. The recording panel works like a kymograph and shows contraction height against time.

PRACTICAL PROCEDURE

1. Keep the tissue under a steady resting tension and allow equilibration.
2. Enter the acetylcholine concentration and select its unit.
3. Add the drug and allow the response to reach its peak.
4. Measure the contraction height in millimetres.
5. Wash the tissue and keep the same contact time and cycle time.
6. Repeat increasing concentrations until a near maximal response is obtained.
7. Plot log concentration on the horizontal axis and percentage response on the vertical axis.
8. Save the labelled tracing when the required observations are complete.

UNKNOWN CONCENTRATION

Record responses to suitable standard concentrations on either side of the unknown response. The unknown may be estimated by interpolation. For a three point or four point assay, use alternating standard and unknown doses in the same part of the concentration response curve and follow the calculation shown in the simulator.

PRECAUTIONS

Use the same bath volume, contact time, cycle time and resting tension. Wash completely between doses. Avoid using only maximal responses for estimation because they do not discriminate concentrations well.
""",
    "Acetylcholine Bioassay": """AIM

To estimate the concentration of an unknown acetylcholine solution by comparing its response with standard acetylcholine on frog rectus abdominis.

THEORY

A bioassay estimates the strength of a substance from a biological response. The standard and unknown must be tested on the same tissue under the same conditions. Responses should lie in the useful, nearly linear part of the log concentration response curve.

In interpolation, the unknown response is placed between two standard responses and its concentration is read from the standard curve. In the three point method used here, two standard concentrations and one unknown test dilution are compared. In a four point assay, two standard doses and two unknown doses with the same dose ratio are compared. Repeated alternating cycles reduce error due to change in tissue sensitivity.

EXPERIMENTAL SETUP

The frog rectus muscle is mounted in an organ bath containing frog Ringer solution. A lever or transducer records contraction height. Standard acetylcholine has a known concentration. Before dosing can begin, the teacher enters the hidden unknown-stock concentration. Teaching mode does not require a password; examination mode keeps examiner setup password-protected. The unknown solution is then labelled without showing its concentration to the student.

PRACTICAL PROCEDURE

1. Ask the teacher to set the hidden unknown-stock concentration and unit.
2. Enter a standard concentration and select its unit.
3. Record the response after a fixed contact time.
4. Wash the tissue and maintain the same cycle time.
5. Record further standards until they bracket the expected unknown response.
6. Select interpolation, three point assay or four point assay.
7. Add standard and unknown doses in the order suggested on the screen.
8. Repeat the cycle when required and measure each height from the same baseline.
9. Calculate the estimated unknown concentration and compare the observed responses.
10. Save the final labelled tracing and result as an image.

OBSERVATION

For every addition record the solution, entered concentration, final bath concentration, response height and percentage of maximal response. A valid result should be supported by responses which are neither very small nor maximal.

PRECAUTIONS

Keep all experimental conditions constant. Use the same unit during one calculation. Wash completely between additions. Alternate standard and unknown solutions. Repeat observations when two nominally equal doses give markedly different responses.
""",
}


def resource_path(*parts):
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent.parent
    return base.joinpath(*parts)

class ExperimentApp:
    def __init__(self, root):
        self.root = root
        configure_application_display(self.root)
        self.root.title("MAMC Pharmacology CAL Suite")
        set_window_size(
            self.root, 980, 740, 620, 480,
            margin_x=60, margin_y=80, expand_large=True,
        )
        self.root.config(bg="#e6f3ff")
        self.show_landing_page()

    def create_scrollable_body(self, background, padx=0, pady=0):
        """Create a page body whose controls remain reachable on a short screen."""
        shell = tk.Frame(self.root, bg=background)
        shell.pack(fill="both", expand=True)
        canvas = tk.Canvas(shell, bg=background, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(shell, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        content = tk.Frame(canvas, bg=background, padx=padx, pady=pady)
        window_id = canvas.create_window((0, 0), window=content, anchor="nw")

        def update_scroll_region(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def fit_content(event):
            canvas.itemconfigure(window_id, width=max(1, event.width))
            update_scroll_region()

        def wheel(event):
            if canvas.winfo_exists():
                canvas.yview_scroll(int(-event.delta / 120), "units")

        content.bind("<Configure>", update_scroll_region)
        canvas.bind("<Configure>", fit_content)
        shell.bind("<Enter>", lambda _event: canvas.bind_all("<MouseWheel>", wheel))
        shell.bind("<Leave>", lambda _event: canvas.unbind_all("<MouseWheel>"))
        return content

    def responsive_module_grid(self, parent, modules, breakpoint=780):
        """Lay cards in one or two columns according to the available width."""
        grid = tk.Frame(parent, bg=parent.cget("bg"))
        grid.pack(fill="both", expand=True)
        cards = []
        for title, subtitle, color, command in modules:
            cards.append(self.module_card(grid, 0, 0, title, subtitle, color, command))

        layout_state = {"columns": 0}

        def arrange(event=None):
            width = event.width if event is not None else grid.winfo_width()
            columns = 1 if width < breakpoint else 2
            if columns == layout_state["columns"]:
                return
            layout_state["columns"] = columns
            for card in cards:
                card.grid_forget()
            for column in range(2):
                grid.grid_columnconfigure(column, weight=1 if column < columns else 0)
            for row in range(len(cards)):
                grid.grid_rowconfigure(row, weight=0)
            row_count = (len(cards) + columns - 1) // columns
            for row in range(max(1, row_count)):
                grid.grid_rowconfigure(row, weight=1)
            for index, card in enumerate(cards):
                card.grid(row=index // columns, column=index % columns,
                          sticky="nsew", padx=8, pady=8)

        grid.bind("<Configure>", arrange)
        grid.after_idle(arrange)
        return grid

    def _legacy_show_landing_page(self):
        # Color palette and fonts
        primary_color = "#3498db"
        secondary_color = "#2ecc71"
        accent_color = "#9b59b6"
        text_dark = "#2c3e50"
        text_light = "#ecf0f1"
        bg_color = "#f5f9fc"

        self.clear_root()
        self.root.configure(bg=bg_color)
        footer_frame = tk.Frame(self.root, bg=text_dark)
        footer_frame.pack(side="bottom", fill="x")
        version_label = tk.Label(
            footer_frame,
            text="© 2025 Maulana Azad Medical College. Version 1.0",
            font=("Segoe UI", 8), fg=text_light, bg=text_dark, pady=5,
        )
        version_label.pack()

        main_frame = self.create_scrollable_body(bg_color, padx=20, pady=10)

        top_frame = tk.Frame(main_frame, bg=bg_color,
                             highlightbackground=primary_color,
                             highlightthickness=2)
        top_frame.pack(pady=15)
        try:
            logo_path = resource_path("assets", "mamc_logo.png")
            original_image = Image.open(logo_path)
            resized_image = original_image.resize((160, 160), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(resized_image)
            logo_label = tk.Label(top_frame, image=self.logo_photo, bg=bg_color, padx=15, pady=15)
            logo_label.image = self.logo_photo
            logo_label.pack()
        except Exception as e:
            logo_frame = tk.Frame(top_frame, bg=primary_color, width=160, height=160)
            logo_frame.pack_propagate(False)
            logo_frame.pack(padx=15, pady=15)
            logo_text = tk.Label(logo_frame, text="MAMC\nLOGO", font=("Segoe UI", 18, "bold"),
                                 fg=text_light, bg=primary_color)
            logo_text.pack(expand=True)
            print(f"Error loading image: {e}")

        title_frame = tk.Frame(main_frame, bg=bg_color)
        title_frame.pack(pady=10)
        college_label = tk.Label(title_frame, text="Maulana Azad Medical College",
                                  font=("Segoe UI", 24, "bold"), fg=primary_color,
                                  bg=bg_color, wraplength=720, justify="center")
        college_label.pack()
        separator = tk.Frame(title_frame, height=2, width=400, bg=secondary_color)
        separator.pack(pady=10)
        dept_label = tk.Label(title_frame, text="Department of Pharmacology",
                              font=("Segoe UI", 18, "bold"), fg=accent_color, bg=bg_color)
        dept_label.pack(pady=(5, 0))
        cal_frame = tk.Frame(title_frame, bg=secondary_color, padx=15, pady=8)
        cal_frame.pack(pady=15)
        cal_label = tk.Label(cal_frame, text="Computer Assisted Learning",
                             font=("Segoe UI", 16, "bold"), fg=text_light, bg=secondary_color)
        cal_label.pack()

        designed_frame = tk.Frame(main_frame, bg=bg_color)
        designed_frame.pack(pady=10)
        designed_label = tk.Label(designed_frame, text="Designed and developed by",
                                  font=("Georgia", 14, "italic"), fg=text_dark, bg=bg_color)
        designed_label.pack(pady=5)

        dev_frame = tk.Frame(main_frame, bg=bg_color)
        dev_frame.pack(pady=10)
        def create_developer_info(parent, name, title, column=0):
            dev_container = tk.Frame(parent, bg=bg_color)
            dev_container.grid(row=0, column=column, padx=20, pady=5)
            name_color = accent_color if column == 1 else primary_color
            name_label = tk.Label(dev_container, text=name, font=("Segoe UI", 12, "bold"),
                                  fg=name_color, bg=bg_color)
            name_label.pack()
            title_label = tk.Label(dev_container, text=title, font=("Segoe UI", 11),
                                   fg=text_dark, bg=bg_color)
            title_label.pack()
            dept_label = tk.Label(dev_container, text="Department of Pharmacology", font=("Segoe UI", 12),
                                  fg=text_dark, bg=bg_color)
            dept_label.pack()
            college_label = tk.Label(dev_container, text="Maulana Azad Medical College, New Delhi", font=("Segoe UI", 12),
                                     fg=text_dark, bg=bg_color)
            college_label.pack()
        #create_developer_info(dev_frame, "Dr. Shalini Chawla", "Director Professor", column=0)
        create_developer_info(dev_frame, "Faculties and Residents", "Academic Year 2025-26", column=1)
        #create_developer_info(dev_frame, "Dr. Bhupinder Singh Kalra", "Professor", column=2)

        # Keep the primary action on screen even when a short laptop display
        # needs to scroll the institutional/developer details above it.
        button_frame = tk.Frame(
            self.root, bg=bg_color,
            highlightbackground="#d6e3ec", highlightthickness=1,
        )
        button_frame.pack(side="bottom", fill="x")
        enter_button = tk.Button(button_frame, text="ENTER PORTAL", font=("Segoe UI", 16, "bold"),
                                 bg=secondary_color, fg=text_light,
                                 activebackground=primary_color, activeforeground=text_light,
                                 relief="raised", bd=2, padx=20, pady=10, cursor="hand2",
                                 command=self.show_main_menu)
        enter_button.pack(pady=9)
        enter_button.bind("<Enter>", lambda e: enter_button.config(bg=primary_color))
        enter_button.bind("<Leave>", lambda e: enter_button.config(bg=secondary_color))

    def show_landing_page(self):
        """Reference-style CAL landing page with a screen-safe primary action."""
        background = "#F3F8FC"
        blue = "#3498DB"
        navy = "#153F62"
        green = "#2ECC71"
        button_green = "#16844B"
        button_green_active = "#116A3D"
        purple = "#9B59B6"
        text = "#193651"

        self.clear_root()
        self.root.configure(bg=background)

        # Keep the action visible even on a short laptop display. The complete
        # credit block above remains reachable with the vertical scrollbar.
        action = tk.Frame(
            self.root, bg=background,
            highlightbackground="#D6E4EE", highlightthickness=1,
        )
        action.pack(side="bottom", fill="x")
        explore = tk.Button(
            action, text="EXPLORE LEARNING MODULES",
            command=self.show_main_menu,
            font=("Segoe UI", 13, "bold"),
            bg=button_green, fg="white",
            activebackground=button_green_active, activeforeground="white",
            relief="raised", bd=2, padx=28, pady=10, cursor="hand2",
        )
        explore.pack(pady=8)

        main = self.create_scrollable_body(background, padx=20, pady=12)
        content = tk.Frame(main, bg=background)
        content.pack(fill="both", expand=True)

        badge_scale = min(
            2.5, max(1.0, float(getattr(self.root, "_mamc_monitor_scale", 1.0)))
        )
        badge_size = int(round(100 * badge_scale))
        badge = tk.Canvas(
            content, width=badge_size, height=badge_size, bg=background,
            highlightthickness=0, bd=0,
        )
        badge.pack(pady=(0, 5))
        badge.create_oval(
            5 * badge_scale, 5 * badge_scale,
            95 * badge_scale, 95 * badge_scale,
            fill=navy, outline=blue, width=max(4, int(round(4 * badge_scale))),
        )
        badge.create_text(
            50 * badge_scale, 45 * badge_scale,
            text="CAL", fill="white", font=("Segoe UI", 22, "bold"),
        )
        badge.create_text(
            50 * badge_scale, 68 * badge_scale,
            text="PHARMACOLOGY", fill="white",
            font=("Segoe UI", 6, "bold"),
        )

        title = tk.Label(
            content, text="COMPUTER-ASSISTED LEARNING",
            font=("Segoe UI", 25, "bold"), fg=blue, bg=background,
            justify="center",
        )
        title.pack(fill="x", padx=10, pady=(3, 0))
        rule = tk.Frame(content, bg=green, height=2, width=400)
        rule.pack(pady=(7, 14))
        subtitle = tk.Label(
            content, text="Virtual Pharmacology Laboratory",
            font=("Segoe UI", 17, "bold"), fg=purple, bg=background,
            justify="center",
        )
        subtitle.pack(fill="x", padx=10)

        banner = tk.Label(
            content,
            text="Interactive simulations, practical exercises and assessments for medical education",
            font=("Segoe UI", 10, "bold"), fg="white", bg=green,
            padx=18, pady=8, justify="center",
        )
        banner.pack(fill="x", padx=38, pady=(12, 16))

        credits = tk.Label(
            content,
            text=(
                "Designed and developed by\n"
                "Dr. Manu Kumar Shetty\n"
                "Professor of Pharmacology\n"
                "Maulana Azad Medical College, New Delhi\n"
                "with assistance from generative AI tools"
            ),
            font=("Georgia", 11, "italic"), fg=text, bg=background,
            justify="center",
        )
        credits.pack(fill="x", padx=12, pady=(0, 13))

        contribution = tk.Label(
            content,
            text=(
                "Contributed by the Faculties of the Department of Pharmacology\n"
                "Maulana Azad Medical College, New Delhi  -  Academic Year 2025-26\n"
                "Funded by MRU, MAMC  -  Nodal Officer: Dr. Bhupinder Kalra"
            ),
            font=("Segoe UI", 9), fg=text, bg=background,
            justify="center",
        )
        contribution.pack(fill="x", padx=12, pady=(0, 10))

        def fit_landing(event):
            width = max(320, event.width)
            compact = width < 760
            title.configure(
                font=("Segoe UI", 20 if compact else 25, "bold"),
                wraplength=max(280, width - 44),
            )
            subtitle.configure(
                font=("Segoe UI", 14 if compact else 17, "bold"),
                wraplength=max(270, width - 50),
            )
            banner.configure(
                font=("Segoe UI", 9 if compact else 10, "bold"),
                wraplength=max(260, width - 110),
            )
            credits.configure(wraplength=max(270, width - 55))
            contribution.configure(wraplength=max(270, width - 55))

        content.bind("<Configure>", fit_landing)
        content.after_idle(lambda: fit_landing(
            type("Size", (), {"width": content.winfo_width()})()
        ))

    def clear_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def page_header(self, title, subtitle, back_command=None):
        header = tk.Frame(self.root, bg="#173b57", padx=20, pady=13)
        header.pack(fill="x")
        if back_command:
            tk.Button(header, text="‹ Back", command=back_command,
                      font=("Segoe UI", 10, "bold"), bg="#173b57", fg="white",
                      activebackground="#245779", activeforeground="white",
                      relief="flat", cursor="hand2").pack(side="left", padx=(0, 18))
        text = tk.Frame(header, bg="#173b57")
        text.pack(side="left", fill="x", expand=True)
        tk.Label(
            text, text="MAMC, New Delhi", font=("Segoe UI", 8, "bold"),
            bg="#173b57", fg="#9fc4dd", justify="left", anchor="w",
        ).pack(fill="x")
        title_label = tk.Label(text, text=title, font=("Segoe UI", 19, "bold"),
                               bg="#173b57", fg="white", justify="left", anchor="w")
        title_label.pack(fill="x")
        subtitle_label = tk.Label(text, text=subtitle, font=("Segoe UI", 9),
                                  bg="#173b57", fg="#cfe2f3", justify="left", anchor="w")
        subtitle_label.pack(fill="x", pady=(2, 0))

        def wrap_header(event):
            wrap = max(220, event.width - (150 if back_command else 50))
            title_label.configure(wraplength=wrap)
            subtitle_label.configure(wraplength=wrap)

        header.bind("<Configure>", wrap_header)

    def module_card(self, parent, row, column, title, subtitle, color, command):
        card = tk.Frame(parent, bg="white", padx=18, pady=15,
                        highlightbackground="#cbd8e2", highlightthickness=1)
        card.grid(row=row, column=column, sticky="nsew", padx=8, pady=8)
        accent = tk.Frame(card, bg=color, width=6)
        accent.pack(side="left", fill="y", padx=(0, 13))
        content = tk.Frame(card, bg="white")
        content.pack(side="left", fill="both", expand=True)
        tk.Label(content, text=title, font=("Segoe UI", 13, "bold"),
                 bg="white", fg="#173b57").pack(anchor="w")
        subtitle_label = tk.Label(content, text=subtitle, font=("Segoe UI", 9),
                                  bg="white", fg="#607789", wraplength=270,
                                  justify="left")
        subtitle_label.pack(anchor="w", fill="x", pady=(4, 9))
        tk.Button(content, text="Open module", command=command,
                  font=("Segoe UI", 9, "bold"), bg=color, fg="white",
                  activebackground=color, activeforeground="white",
                  relief="flat", padx=12, pady=5, cursor="hand2").pack(anchor="w")
        card.bind(
            "<Configure>",
            lambda event: subtitle_label.configure(wraplength=max(180, event.width - 75)),
        )
        return card

    def show_main_menu(self):
        self.clear_root()
        self.root.configure(bg="#eef4f8")
        self.page_header(
            "MAMC Pharmacology CAL Suite",
            "Computer-assisted learning workspace",
        )
        tk.Label(self.root,
                 text="MAMC, New Delhi  •  Academic CAL workspace",
                 font=("Segoe UI", 8), bg="#20394d", fg="#dce6ed",
                 pady=6).pack(fill="x", side="bottom")
        body = self.create_scrollable_body("#eef4f8", padx=28, pady=24)
        tk.Label(body, text="LEARNING PORTAL", font=("Segoe UI", 10, "bold"),
                 bg="#eef4f8", fg="#607789").pack(anchor="w", pady=(0, 10))
        modules = (
            ("Theory and Practical Guide",
             "Read the theory, setup, procedure, observation and precautions for all four experiments.",
             "#607d8b", self.show_theory),
            ("Teaching Practicals",
             "Run guided simulations with observations, tracings and interpretation.",
             "#1769aa", self.show_practical_options),
            ("Student Examinations",
             "Attempt timed MBBS and PG practical assessments with secure submission.",
             "#8e44ad", self.show_exam_options),
            ("Examiner Results",
             "Open password protected marks and answer reviews across experiments.",
             "#237032", self.launch_examiner_results),
        )
        self.responsive_module_grid(body, modules)

    def show_message(self, msg):
        messagebox.showinfo("Information", msg)

    def show_exam_options(self):
        self.clear_root()
        self.root.configure(bg="#eef4f8")
        self.page_header(
            "Student Examinations",
            "Practical and knowledge assessments • Marks available only to examiners",
            self.show_main_menu,
        )
        body = self.create_scrollable_body("#eef4f8", padx=24, pady=18)
        modules = (
            ("Dog BP – MBBS", "Identify two examiner-selected unknown drugs using the experimental setup.",
             "#1769aa", lambda: self.launch_dog_bp_exam("MBBS")),
            ("Dog BP – PG", "Advanced unknown-drug identification using agonists, blockers and dose response.",
             "#8e44ad", lambda: self.launch_dog_bp_exam("PG")),
            ("Rabbit Eye – MBBS", "Compare paired eyes, reflexes, pupil size and ocular tone.",
             "#d68910", self.launch_rabbit_eye_exam),
            ("Frog Rectus – PG", "Perform a timed experiment to identify an examiner configured unknown agonist and its concentration.",
             "#148f77", self.launch_frog_rectus_exam),
            ("ACh Bioassay – PG", "Estimate an examiner configured unknown ACh stock by interpolation, three point or four point assay.",
             "#a04070", self.launch_bioassay_exam),
            ("Examiner Results", "Password-protected marks and answer review for every module.",
             "#237032", self.launch_examiner_results),
        )
        self.responsive_module_grid(body, modules)

    def exit_program(self):
        self.root.quit()

    def show_theory(self):
        self.clear_root()
        self.root.configure(bg="#eef4f8")
        self.page_header(
            "Theory and Practical Guide",
            "Simple instructions for the four CAL experiments",
            self.show_main_menu,
        )
        body = tk.Frame(self.root, bg="#eef4f8", padx=18, pady=14)
        body.pack(fill="both", expand=True)
        tk.Label(
            body,
            text=("Select an experiment. Read the theory first and then follow the practical "
                  "procedure in the teaching simulator."),
            font=("Segoe UI", 10), bg="#eef4f8", fg="#405b70",
            justify="left", anchor="w", wraplength=900,
        ).pack(fill="x", pady=(0, 10))

        notebook = ttk.Notebook(body)
        notebook.pack(fill="both", expand=True)
        short_tab_names = {
            "Dog Blood Pressure": "Dog BP",
            "Rabbit Eye": "Rabbit Eye",
            "Frog Rectus Abdominis": "Frog Rectus",
            "Acetylcholine Bioassay": "ACh Bioassay",
        }
        for experiment, guide in THEORY_AND_PRACTICAL_GUIDES.items():
            tab = tk.Frame(notebook, bg="white")
            notebook.add(tab, text=short_tab_names[experiment])
            text = tk.Text(
                tab, wrap="word", font=("Segoe UI", 10), bg="white", fg="#20394d",
                relief="flat", padx=18, pady=14, spacing1=2, spacing3=5,
            )
            bar = ttk.Scrollbar(tab, orient="vertical", command=text.yview)
            text.configure(yscrollcommand=bar.set)
            bar.pack(side="right", fill="y")
            text.pack(side="left", fill="both", expand=True)
            text.tag_configure("heading", font=("Segoe UI", 11, "bold"),
                               foreground="#1769aa", spacing1=8, spacing3=4)
            text.insert("end", experiment.upper() + "\n\n", "heading")
            for line in guide.strip().splitlines():
                if line and line == line.upper() and len(line) < 40:
                    text.insert("end", line + "\n", "heading")
                else:
                    text.insert("end", line + "\n")
            text.configure(state="disabled")

    def show_rabbit_eye_experiment(self):
        exp_win = tk.Toplevel(self.root)
        RabbitEyeApp(exp_win, image_dir=str(resource_path("assets", "rabbit_eye")))

    def show_practical_options(self):
        self.clear_root()
        self.root.configure(bg="#eef4f8")
        self.page_header(
            "Teaching Practicals",
            "Guided pharmacology simulations with observation and interpretation",
            self.show_main_menu,
        )
        tk.Label(
            self.root,
            text="Select a preparation to begin the guided practical",
            font=("Segoe UI", 8), bg="#20394d", fg="#dce6ed", pady=6,
        ).pack(fill="x", side="bottom")
        body = self.create_scrollable_body("#eef4f8", padx=28, pady=24)
        modules = (
            ("Dog Blood Pressure",
             "Study agonists, antagonists, cardiovascular responses and receptor blockade.",
             "#1769aa", self.launch_dog_bp_experiment),
            ("Rabbit Eye",
             "Compare drug-treated and saline-control eyes using interactive examination tools.",
             "#d68910", self.show_rabbit_eye_experiment),
            ("Frog Rectus Abdominis",
             "Open the advanced organ-bath simulator for DRC and antagonism experiments.",
             "#148f77", self.launch_frog_rectus_experiment),
            ("Acetylcholine Bioassay",
             "Estimate an unknown by interpolation using standards, wash cycles and tracings.",
             "#a04070", self.launch_bioassay_experiment),
        )
        self.responsive_module_grid(body, modules)

    # Helper methods for button hover effects
    def on_practical_button_hover(self, event, button):
        """Change button appearance on hover"""
        text = button['text']
        if "Dog BP" in text:
            button.config(bg="#273c75")
        elif "Bioassay" in text:
            button.config(bg="#a3219f")
        elif "Rabbit Eye" in text:
            button.config(bg="#fa983a")
        elif "Drug Dose" in text:
            button.config(bg="#38ada9")
        elif "Return" in text:
            button.config(bg="#6d1122")

    def on_practical_button_leave(self, event, button):
        """Restore button appearance when mouse leaves"""
        text = button['text']
        if "Dog BP" in text:
            button.config(bg="#4a69bd")
        elif "Bioassay" in text:
            button.config(bg="#e84393")
        elif "Rabbit Eye" in text:
            button.config(bg="#f6b93b")
        elif "Drug Dose" in text:
            button.config(bg="#78e08f")
        elif "Return" in text:
            button.config(bg="#b71540")

    def launch_dog_bp_experiment(self):
        exp_win = tk.Toplevel(self.root)
        DogBPSimulation(exp_win)

    def launch_dog_bp_exam(self, level="MBBS"):
        exam_win = tk.Toplevel(self.root)
        DogBPExamMode(exam_win, level=level)

    def launch_examiner_results(self):
        result_win = tk.Toplevel(self.root)
        CombinedExaminerDashboard(result_win)

    def launch_rabbit_eye_exam(self):
        exam_win = tk.Toplevel(self.root)
        RabbitEyeExam(exam_win)

    def launch_frog_rectus_exam(self):
        exam_win = tk.Toplevel(self.root)
        FrogRectusUnknownPractical(exam_win, level="PG")

    def launch_bioassay_exam(self):
        exam_win = tk.Toplevel(self.root)
        BioassayUnknownPractical(exam_win, level="PG")

    def launch_bioassay_experiment(self):
        exp_win = tk.Toplevel(self.root)
        BioassaySimulation(exp_win)

    def launch_frog_rectus_experiment(self):
        qt_available = any(
            importlib.util.find_spec(binding) is not None
            for binding in ("PySide6", "PySide2")
        )
        if qt_available:
            if getattr(sys, "frozen", False):
                command = [sys.executable, "--frog-rectus"]
                working_directory = str(Path(sys.executable).resolve().parent)
            else:
                command = [
                    sys.executable, "-m", "integrated_modules.frog_rectus.main"
                ]
                working_directory = str(Path(__file__).resolve().parent.parent)
            try:
                startup = subprocess.STARTUPINFO() if sys.platform == "win32" else None
                creationflags = 0
                if startup is not None:
                    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                subprocess.Popen(
                    command,
                    cwd=working_directory,
                    startupinfo=startup,
                    creationflags=creationflags,
                )
                return
            except OSError as error:
                messagebox.showwarning(
                    "Frog Rectus",
                    f"The advanced simulator could not start ({error}).\n"
                    "Opening the built-in simulator instead.",
                )
        else:
            messagebox.showwarning(
                "Frog Rectus",
                "The advanced Qt simulator is not available in this installation. "
                "Opening the built-in simulator instead.",
            )
        exp_win = tk.Toplevel(self.root)
        FrogRectusSimulation(exp_win)


if __name__ == "__main__":
    enable_high_dpi()
    root = tk.Tk()
    configure_application_display(root)
    app = ExperimentApp(root)
    root.mainloop()
