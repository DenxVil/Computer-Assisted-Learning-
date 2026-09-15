#!/usr/bin/env python3
"""
=============================================================================
RABBIT EYE EXPERIMENT SIMULATOR  (v3 — Interactive Tools)
Computer-Assisted Learning (CAL) Software
MAMC, New Delhi

For 2nd Year MBBS Students

INTERACTIVE TOOLS:
  📏 Ruler   — Click & drag across pupil to measure diameter in mm
  🔦 Torch   — Move mouse near pupil; watch it constrict (or not)
  🧹 Cotton  — Click & drag swab to cornea; eye blinks (or stays open)
  👁  Conjunctiva — Click to inspect
  ✋  Tone    — Click to palpate

Requirements: Python 3.8+, Pillow  (pip install Pillow)
Run: python rabbit_eye_experiment_v3.py [path/to/images]
=============================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk, ImageDraw, ImageFont
from datetime import datetime
import csv
import os, sys, math, textwrap
from ui.display import configure_application_display, enable_high_dpi, set_window_size

# =============================================================================
# PHARMACOLOGY DATA
# =============================================================================
BASELINE = {
    "pupil_size": "normal", "pupil_mm": 6.0,
    "light_reflex": "present", "corneal_reflex": "present",
    "conjunctiva": "normal", "conjunctiva_desc": "Normal, pink vasculature",
    "tone": "normal", "tone_desc": "Normal IOP (~15-20 mmHg)",
    "pupil_image": "Normal_pupil",
}

DRUG_DATA = {
    "Atropine (1%)": {
        "class": "Anticholinergic (M3 antagonist)",
        "pupil_size": "mydriasis", "pupil_mm": 9.0,
        "light_reflex": "absent", "corneal_reflex": "present",
        "conjunctiva": "no_change", "conjunctiva_desc": "No significant change",
        "tone": "increased", "tone_desc": "Increased IOP (~25-30 mmHg) — angle closure",
        "mechanism": "M3 antagonist → sphincter pupillae relaxation (mydriasis)\n"
                     "+ cycloplegia. Abolishes light reflex.",
        "onset": "20-30 min", "duration": "7-10 days",
        "pupil_image": "Mydriasis", "color": "#ef4444",
    },
    "Lignocaine (4%)": {
        "class": "Local Anaesthetic",
        "pupil_size": "normal", "pupil_mm": 6.0,
        "light_reflex": "present", "corneal_reflex": "absent",
        "conjunctiva": "no_change", "conjunctiva_desc": "No significant change",
        "tone": "normal", "tone_desc": "No change in IOP",
        "mechanism": "Na⁺ channel block → abolishes corneal sensation.\n"
                     "No autonomic effect on pupil.",
        "onset": "1-5 min", "duration": "30-60 min",
        "pupil_image": "Normal_pupil", "color": "#3b82f6",
    },
    "Cocaine (4%)": {
        "class": "NA Reuptake Inhibitor + LA",
        "pupil_size": "mydriasis", "pupil_mm": 8.5,
        "light_reflex": "present", "corneal_reflex": "absent",
        "conjunctiva": "blanched", "conjunctiva_desc": "Blanched — vasoconstriction",
        "tone": "normal", "tone_desc": "No significant change",
        "mechanism": "Blocks NA reuptake → mydriasis with preserved light reflex.\n"
                     "Also LA → abolishes corneal reflex.\nVasoconstriction → blanching.",
        "onset": "5-10 min", "duration": "1-2 hours",
        "pupil_image": "Mydriasis", "color": "#8b5cf6",
    },
    "Ephedrine (1%)": {
        "class": "Mixed Sympathomimetic",
        "pupil_size": "mydriasis", "pupil_mm": 8.0,
        "light_reflex": "present", "corneal_reflex": "present",
        "conjunctiva": "blanched", "conjunctiva_desc": "Mild blanching — vasoconstriction",
        "tone": "normal", "tone_desc": "No significant change",
        "mechanism": "Releases NA + direct α₁ action → mydriasis.\n"
                     "Light reflex and corneal reflex remain intact.",
        "onset": "10-20 min", "duration": "3-6 hours",
        "pupil_image": "Mydriasis", "color": "#f59e0b",
    },
    "Pilocarpine (1%)": {
        "class": "Cholinomimetic (M3 agonist)",
        "pupil_size": "miosis", "pupil_mm": 3.0,
        "light_reflex": "present", "corneal_reflex": "present",
        "conjunctiva": "congested", "conjunctiva_desc": "Congested — vasodilation",
        "tone": "decreased", "tone_desc": "Decreased IOP (~10-15 mmHg)",
        "mechanism": "M3 agonist → sphincter pupillae contracts (miosis).\n"
                     "Opens trabecular meshwork → ↓ IOP.",
        "onset": "10-20 min", "duration": "4-8 hours",
        "pupil_image": "Miosis", "color": "#10b981",
    },
}

# =============================================================================
C = {
    "bg": "#F4F8FC", "bg2": "#E5EFF8", "bg3": "#FFFFFF",
    "gold": "#145C96", "gold_dim": "#4D6F8A",
    "text": "#172536", "text2": "#43586D", "text3": "#66798C",
    "green": "#18794E", "red": "#B42318", "blue": "#1769AA",
    "amber": "#9A5A00", "card": "#FFFFFF", "border": "#B9C9D8",
    "soft_blue": "#EAF4FC", "soft_green": "#EAF7F0",
}

RABBIT_GUIDE = """AIM

To study the local actions of selected drugs on the rabbit eye and to compare the treated eye with the saline control eye.

THEORY

The circular sphincter pupillae muscle constricts the pupil through muscarinic receptors. The radial dilator pupillae muscle widens the pupil through alpha receptors. Atropine blocks muscarinic receptors and produces mydriasis, cycloplegia and loss of the light reflex in the treated eye. Pilocarpine stimulates muscarinic receptors and produces miosis with a fall in intraocular pressure.

Sympathomimetic drugs produce mydriasis while the light reflex remains present because the sphincter pathway is not blocked. Cocaine also causes local anaesthesia and vasoconstriction. Ephedrine does not abolish the corneal reflex. Lignocaine blocks sodium channels in sensory nerves. It abolishes the corneal reflex but does not change pupil size or the light reflex.

EXPERIMENTAL SETUP

One eye receives the selected drug. The other eye receives normal saline and acts as control. The ruler is used for pupil diameter. The torch is used for the light reflex. A soft cotton swab is used carefully for the corneal reflex. Conjunctival colour and ocular tone are compared in both eyes.

PRACTICAL PROCEDURE

1. Select the drug and the eye which will receive it.
2. Allow the other eye to remain as the saline control.
3. Measure pupil diameter in both eyes with the ruler.
4. Bring the torch near each eye and observe the light reflex.
5. Touch the edge of each cornea gently with the cotton swab and observe blinking.
6. Inspect both conjunctivae for congestion, normal colour or blanching.
7. Compare ocular tone gently and record all findings.
8. After the first observation, open the comparison notebook and type the finding manually.
9. Save the current test and start another experiment when required; earlier entries remain selectable.
10. Export all entered tests together as PNG or CSV after completing the session.
11. Identify the drug action only after considering the full pattern.

EXPECTED FINDINGS

Atropine gives mydriasis with absent light reflex. Pilocarpine gives miosis with present reflexes. Lignocaine gives an absent corneal reflex without pupil change. Cocaine gives mydriasis, an absent corneal reflex and conjunctival blanching. Ephedrine gives mydriasis with both reflexes present.

PRECAUTIONS

Always compare the same parameter in both eyes. Use the cotton swab gently. Do not identify a drug from pupil size alone. Observe pupil size, both reflexes, conjunctiva and ocular tone together.
"""


def get_image_path(image_dir, key):
    for ext in ['.png', '.jpg', '.jpeg', '.PNG']:
        p = os.path.join(image_dir, key + ext)
        if os.path.exists(p):
            return p
    return os.path.join(image_dir, key + ".png")


# =============================================================================
# EYE CANVAS — handles all interactive drawing on one eye
# =============================================================================
class EyeCanvas(tk.Canvas):
    """Canvas for a single eye with interactive tool overlays."""

    # Image centre coordinates (after placing image)
    IMG_CX = 160
    IMG_CY = 200
    # Approx radius (in px) of the iris in the photographs
    IRIS_PX = 95
    # Iris real diameter in mm (rabbit)
    IRIS_MM = 10.0

    def __init__(self, parent, eye_data, image_dir, side, experiment_frame):
        super().__init__(parent, width=340, height=440, bg=C["bg"], highlightthickness=0)
        self.eye_data = eye_data
        self.image_dir = image_dir
        self.side = side
        self.exp = experiment_frame

        # State
        self.photo = None           # normal / drug eye image
        self.close_photo = None     # closed-eye (blink) image
        self.miosis_photo = None    # constricted pupil image (for light reflex)
        self.is_blinking = False
        self.is_constricted = False # currently showing miosis image (torch)

        # Ruler state
        self.ruler_start = None
        self.ruler_line_id = None
        self.ruler_cap1 = None
        self.ruler_cap2 = None
        self.ruler_bg = None
        self.ruler_label = None

        # Torch state
        self.torch_glow = None
        self.torch_icon = []
        self.torch_label = None
        self.torch_near = False

        # Cotton swab state
        self.swab_items = []
        self.swab_touched = False
        self.swab_target = None

        self._load_eye_image()
        self._preload_close_image()
        self._preload_miosis_image()

    # ---- image loading ----
    def _load_eye_image(self):
        img_key = self.eye_data.get("pupil_image", "Normal_pupil")
        img_path = get_image_path(self.image_dir, img_key)
        if os.path.exists(img_path):
            try:
                img = Image.open(img_path)
                scale = min(320 / img.width, 420 / img.height)
                img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
                self.photo = ImageTk.PhotoImage(img)
                self.create_image(self.IMG_CX, self.IMG_CY, image=self.photo, tags="eyeimg")
            except Exception:
                self.create_text(self.IMG_CX, self.IMG_CY, text=img_key, fill=C["text3"])
        else:
            self.create_text(self.IMG_CX, self.IMG_CY, text=f"Not found:\n{img_key}",
                             fill=C["text3"], font=("Segoe UI", 10))

    def _preload_close_image(self):
        close_path = get_image_path(self.image_dir, "Close")
        if os.path.exists(close_path):
            try:
                img = Image.open(close_path)
                scale = min(320 / img.width, 420 / img.height)
                img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
                self.close_photo = ImageTk.PhotoImage(img)
            except Exception:
                self.close_photo = None

    def _preload_miosis_image(self):
        """Preload constricted-pupil image for light reflex demonstration."""
        miosis_path = get_image_path(self.image_dir, "Miosis")
        if os.path.exists(miosis_path):
            try:
                img = Image.open(miosis_path)
                scale = min(320 / img.width, 420 / img.height)
                img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
                self.miosis_photo = ImageTk.PhotoImage(img)
            except Exception:
                self.miosis_photo = None

    def _show_constricted(self):
        """Swap to miosis (constricted pupil) image when torch is near."""
        if self.miosis_photo and not self.is_constricted and not self.is_blinking:
            self.is_constricted = True
            self.delete("eyeimg")
            self.create_image(self.IMG_CX, self.IMG_CY, image=self.miosis_photo, tags="eyeimg")

    def _show_normal(self):
        """Restore normal eye image when torch moves away."""
        if self.is_constricted:
            self.is_constricted = False
            self.delete("eyeimg")
            if self.photo:
                self.create_image(self.IMG_CX, self.IMG_CY, image=self.photo, tags="eyeimg")

    def _show_blink(self):
        """Show closed eye image for blink, then restore after 600ms."""
        if self.close_photo and not self.is_blinking:
            self.is_blinking = True
            self.delete("eyeimg")
            self.delete("swab")
            self.delete("swab_target")
            self.create_image(self.IMG_CX, self.IMG_CY, image=self.close_photo, tags="eyeimg")
            # Add text to make it obvious
            self.create_text(self.IMG_CX, 30, text="👁 Eye BLINKED ✓",
                             fill=C["green"], font=("Segoe UI", 12, "bold"), tags="blinktext")
            self.after(800, self._restore_eye)

    def _restore_eye(self):
        self.delete("eyeimg")
        self.delete("blinktext")
        if self.photo:
            self.create_image(self.IMG_CX, self.IMG_CY, image=self.photo, tags="eyeimg")
        self.is_blinking = False
        self.is_constricted = False

    # ---- pixel ↔ mm conversion ----
    def px_to_mm(self, px_distance):
        return (px_distance / (self.IRIS_PX * 2)) * self.IRIS_MM

    # ---- clear all overlays ----
    def clear_overlays(self):
        for tag in ("ruler", "torch", "swab", "swab_target", "blinktext"):
            self.delete(tag)
        self.ruler_start = None
        self.torch_near = False
        self.swab_touched = False
        # Restore normal image if we were showing constricted or blink
        if self.is_constricted or self.is_blinking:
            self._restore_eye()

    # ================================================================
    # RULER — click & drag
    # ================================================================
    def ruler_press(self, event):
        self.clear_overlays()
        self.ruler_start = (event.x, event.y)

    def ruler_drag(self, event):
        if not self.ruler_start:
            return
        sx, sy = self.ruler_start
        ex, ey = event.x, event.y
        self.delete("ruler")

        # Main dashed line
        self.create_line(sx, sy, ex, ey, fill="#ffd700", width=2, dash=(6, 3), tags="ruler")

        # End caps (perpendicular ticks)
        dx, dy = ex - sx, ey - sy
        length = math.sqrt(dx * dx + dy * dy) or 1
        nx, ny = -dy / length * 10, dx / length * 10
        self.create_line(sx - nx, sy - ny, sx + nx, sy + ny, fill="#ffd700", width=2, tags="ruler")
        self.create_line(ex - nx, ey - ny, ex + nx, ey + ny, fill="#ffd700", width=2, tags="ruler")

        # Measurement label
        px_dist = math.sqrt((ex - sx) ** 2 + (ey - sy) ** 2)
        mm = self.px_to_mm(px_dist)
        mx, my = (sx + ex) / 2, (sy + ey) / 2 - 16
        self.create_rectangle(mx - 36, my - 11, mx + 36, my + 11,
                              fill="#FFF8D6", outline=C["amber"], width=1, tags="ruler")
        self.create_text(mx, my, text=f"{mm:.1f} mm", fill=C["text"],
                         font=("Consolas", 12, "bold"), tags="ruler")

    def ruler_release(self, event):
        if not self.ruler_start:
            return
        sx, sy = self.ruler_start
        px_dist = math.sqrt((event.x - sx) ** 2 + (event.y - sy) ** 2)
        mm = self.px_to_mm(px_dist)
        self.ruler_start = None

        data = self.eye_data
        self.exp.show_result(
            f"📏 PUPIL SIZE — {self.side.upper()} EYE",
            f"Measured: {mm:.1f} mm\n"
            f"Expected: ~{data['pupil_mm']} mm\n\n"
            f"State: {data['pupil_size'].upper()}\n\n"
            + ("Dilator pupillae dominant (sympathetic)."
               if data["pupil_size"] == "mydriasis"
               else "Sphincter pupillae dominant (parasympathetic)."
               if data["pupil_size"] == "miosis"
               else "Normal balanced autonomic tone."),
            data["pupil_size"] == "normal"
        )

    # ================================================================
    # TORCH — mouse-move proximity
    # ================================================================
    def torch_move(self, event):
        self.delete("torch")
        tx, ty = event.x, event.y

        # Distance from pupil centre
        dist = math.sqrt((tx - self.IMG_CX) ** 2 + (ty - self.IMG_CY) ** 2)
        near = dist < 120
        was_near = self.torch_near
        self.torch_near = near

        # Glow circle (larger when near)
        glow_r = 65 if near else 35
        self.create_oval(tx - glow_r, ty - glow_r, tx + glow_r, ty + glow_r,
                         fill="#fff9c4", outline="", stipple="gray25", tags="torch")

        # Torch body
        self.create_rectangle(tx - 10, ty - 6, tx + 10, ty + 6,
                              fill="#555555", outline="#888888", tags="torch")
        self.create_rectangle(tx - 5, ty + 6, tx + 5, ty + 20,
                              fill="#444444", outline="#666666", tags="torch")
        # Bulb
        self.create_oval(tx - 5, ty - 11, tx + 5, ty - 1,
                         fill="#fff9c4" if near else "#fff176", outline="", tags="torch")

        # ---- IMAGE SWAP based on proximity and reflex ----
        reflex = self.eye_data["light_reflex"]
        if near and not was_near:
            # Torch just got close — swap image if reflex present
            if reflex == "present":
                self._show_constricted()  # swap to Miosis image
            # sluggish: could show slight change, but miosis image is good enough
            elif reflex == "sluggish":
                self._show_constricted()
            # absent: do nothing, keep original image
        elif not near and was_near:
            # Torch moved away — restore original image
            self._show_normal()

        # Status text
        if near:
            if reflex == "present":
                txt, clr = "Pupil CONSTRICTS ✓  (see miosis)", C["green"]
            elif reflex == "sluggish":
                txt, clr = "Pupil constricts SLOWLY ⚠", C["amber"]
            else:
                txt, clr = "NO constriction ✗  (pupil unchanged)", C["red"]
            self.create_text(self.IMG_CX, 425, text=txt, fill=clr,
                             font=("Segoe UI", 11, "bold"), tags="torch")

            self.exp.show_result(
                f"🔦 LIGHT REFLEX — {self.side.upper()} EYE",
                f"Response: {reflex.upper()}\n\n"
                + ("✓ Pupil constricts on light exposure.\n"
                   "Image changed to MIOSIS (constricted pupil).\n"
                   "Sphincter pupillae functional."
                   if reflex == "present"
                   else "⚠ Delayed/incomplete constriction.\n"
                   "Sympathetic dominance partially overrides."
                   if reflex == "sluggish"
                   else "✗ NO constriction on light.\n"
                   "Pupil image remains UNCHANGED.\n"
                   "Sphincter pupillae paralysed."),
                reflex == "present"
            )
        else:
            self.create_text(self.IMG_CX, 425, text="🔦 Move torch closer to the pupil",
                             fill=C["text3"], font=("Segoe UI", 10), tags="torch")

    def torch_leave(self, event):
        self.delete("torch")
        if self.torch_near:
            self._show_normal()  # restore original image
        self.torch_near = False

    # ================================================================
    # COTTON SWAB — click & drag, blink on cornea contact
    # ================================================================
    def swab_press(self, event):
        self.clear_overlays()
        self.swab_touched = False
        # Show pulsing target zone on the cornea
        self.create_oval(self.IMG_CX - 45, self.IMG_CY - 45,
                         self.IMG_CX + 45, self.IMG_CY + 45,
                         outline="#ffd700", width=2, dash=(6, 4), tags="swab_target")
        self.create_text(self.IMG_CX, self.IMG_CY + 65,
                         text="↑ Drag cotton swab to this zone",
                         fill="#ffd700", font=("Segoe UI", 10, "bold"), tags="swab_target")

    def swab_drag(self, event):
        if self.swab_touched or self.is_blinking:
            return
        self.delete("swab")
        sx, sy = event.x, event.y

        # ---- Draw a large visible cotton swab ----
        # Cotton tip (big white circle)
        self.create_oval(sx - 10, sy - 10, sx + 10, sy + 10,
                         fill="white", outline="#bbbbbb", width=2, tags="swab")
        # Wooden stick
        self.create_line(sx + 8, sy - 8, sx + 55, sy - 55,
                         fill="#d4b896", width=5, tags="swab")
        self.create_line(sx + 8, sy - 8, sx + 55, sy - 55,
                         fill="#e8d5b8", width=3, tags="swab")
        # Label near swab
        self.create_text(sx + 60, sy - 60, text="Cotton\nSwab",
                         fill="white", font=("Segoe UI", 8), tags="swab", anchor="sw")

        # Check if cotton tip is touching cornea (centre of eye image)
        dist = math.sqrt((sx - self.IMG_CX) ** 2 + (sy - self.IMG_CY) ** 2)
        if dist < 55:
            self.swab_touched = True
            self.delete("swab_target")
            self.delete("swab")

            reflex = self.eye_data["corneal_reflex"]
            if reflex == "present":
                # Eye BLINKS — show Close.png image
                self._show_blink()
                self.exp.show_result(
                    f"🧹 CORNEAL REFLEX — {self.side.upper()} EYE",
                    "Response: PRESENT\n\n"
                    "✓ Eye BLINKS on corneal touch!\n"
                    "(Image changed to closed eye)\n\n"
                    "Sensory nerves (CN V₁) intact.\n"
                    "Afferent limb of blink reflex functional.",
                    True
                )
            else:
                # Eye stays OPEN — no image change
                self.create_text(self.IMG_CX, 30,
                                 text="✗ Eye stays OPEN — No blink!",
                                 fill=C["red"], font=("Segoe UI", 13, "bold"), tags="swab")
                self.create_text(self.IMG_CX, 425,
                                 text="Corneal sensation abolished",
                                 fill=C["red"], font=("Segoe UI", 10), tags="swab")
                self.exp.show_result(
                    f"🧹 CORNEAL REFLEX — {self.side.upper()} EYE",
                    "Response: ABSENT\n\n"
                    "✗ NO blink on corneal touch!\n"
                    "(Eye remains open — no image change)\n\n"
                    "Corneal sensation ABOLISHED.\n"
                    "Local anaesthetic blocked Na⁺ channels\n"
                    "in sensory nerve fibres.",
                    False
                )

    def swab_release(self, event):
        if not self.swab_touched:
            self.delete("swab")
            self.delete("swab_target")

    # ================================================================
    # Bind / unbind helpers
    # ================================================================
    def bind_ruler(self):
        self.clear_overlays()
        self.config(cursor="crosshair")
        self.bind("<ButtonPress-1>", self.ruler_press)
        self.bind("<B1-Motion>", self.ruler_drag)
        self.bind("<ButtonRelease-1>", self.ruler_release)
        self.unbind("<Motion>")
        self.unbind("<Leave>")

    def bind_torch(self):
        self.clear_overlays()
        self.config(cursor="none")
        self.unbind("<ButtonPress-1>")
        self.unbind("<B1-Motion>")
        self.unbind("<ButtonRelease-1>")
        self.bind("<Motion>", self.torch_move)
        self.bind("<Leave>", self.torch_leave)

    def bind_cotton(self):
        self.clear_overlays()
        self.config(cursor="crosshair")
        self.bind("<ButtonPress-1>", self.swab_press)
        self.bind("<B1-Motion>", self.swab_drag)
        self.bind("<ButtonRelease-1>", self.swab_release)
        self.unbind("<Motion>")
        self.unbind("<Leave>")

    def bind_click(self, callback):
        self.clear_overlays()
        self.config(cursor="hand2")
        self.bind("<ButtonPress-1>", callback)
        self.unbind("<B1-Motion>")
        self.unbind("<ButtonRelease-1>")
        self.unbind("<Motion>")
        self.unbind("<Leave>")

    def unbind_all_tools(self):
        self.clear_overlays()
        self.config(cursor="")
        for evt in ("<ButtonPress-1>", "<B1-Motion>", "<ButtonRelease-1>",
                    "<Motion>", "<Leave>"):
            self.unbind(evt)


# =============================================================================
# SCREENS
# =============================================================================
class SplashFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg3"])
        self.app = app

        self.canvas = tk.Canvas(
            self,
            width=700,
            height=500,
            bg=C["bg3"],
            highlightthickness=0
        )
        self.canvas.pack(expand=True)

        c = self.canvas

        # ---------- Logo ----------
        logo_path = get_image_path(app.image_dir, "mamc_logo")
        self.logo_alpha = 0

        if os.path.exists(logo_path):
            self.original_logo = Image.open(logo_path).resize((100, 100), Image.LANCZOS)
            self.logo = ImageTk.PhotoImage(self.original_logo)
            self.logo_id = c.create_image(350, 80, image=self.logo)

        # ---------- Titles ----------
        c.create_text(
            350, 165,
            text="RABBIT EYE EXPERIMENT",
            font=("Georgia", 28, "bold"),
            fill=C["gold"]
        )

        c.create_text(
            350, 198,
            text="SIMULATION SOFTWARE",
            font=("Georgia", 14),
            fill=C["gold_dim"]
        )

        c.create_line(210, 220, 490, 220, fill=C["border"], width=2)

        c.create_text(
            350, 255,
            text="Computer-Assisted Learning for 2nd Year MBBS",
            font=("Segoe UI", 15, "bold"),
            fill=C["text"]
        )

        # ENTER blinking prompt
        self.enter_id = c.create_text(
            350, 410,
            text="[ Press ENTER to Begin ]",
            font=("Segoe UI", 14, "bold"),
            fill=C["gold"]
        )

        c.create_text(
            350, 470, text="MAMC, New Delhi", font=("Segoe UI", 9, "bold"),
            fill=C["text3"],
        )

        self.blink_state = True
        self._blink_job = None
        self._fade_job = None
        self._return_binding = None
        self.animate_enter()
        self.fade_logo()

        self.begin_button = tk.Button(
            self, text="Begin Experiment", command=app.show_setup,
            font=("Segoe UI", 12, "bold"), bg=C["gold"], fg="white",
            activebackground="#0F4D80", activeforeground="white",
            relief="raised", bd=1, padx=22, pady=8,
            cursor="hand2",
        )
        self.begin_button.place(relx=0.5, rely=0.82, anchor="center")

        self._return_binding = app.root.bind(
            "<Return>", lambda _event: app.show_setup(), add="+"
        )

    # ---------- Blinking ENTER ----------
    def animate_enter(self):
        if self.blink_state:
            self.canvas.itemconfigure(self.enter_id, state="hidden")
        else:
            self.canvas.itemconfigure(self.enter_id, state="normal")

        self.blink_state = not self.blink_state
        self._blink_job = self.after(600, self.animate_enter)

    # ---------- Fade Logo ----------
    def fade_logo(self):
        try:
            self.logo_alpha += 20
            if self.logo_alpha > 255:
                return

            img = self.original_logo.copy()
            img.putalpha(self.logo_alpha)

            self.logo = ImageTk.PhotoImage(img)
            self.canvas.itemconfig(self.logo_id, image=self.logo)

            self._fade_job = self.after(80, self.fade_logo)

        except Exception:
            pass

    def destroy(self):
        for job in (self._blink_job, self._fade_job):
            if job is not None:
                try:
                    self.after_cancel(job)
                except tk.TclError:
                    pass
        if self._return_binding is not None:
            try:
                self.app.root.unbind("<Return>", self._return_binding)
            except tk.TclError:
                pass
        tk.Frame.destroy(self)


class SetupFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.app = app
        self.selected_drug = tk.StringVar(value="")
        self.drug_eye = tk.StringVar(value="right")

        canvas = tk.Canvas(self, bg=C["bg"], highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        content = tk.Frame(canvas, bg=C["bg"])
        content_id = canvas.create_window((0, 0), window=content, anchor="nw")
        content.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(content_id, width=max(1, event.width)),
        )

        brand = tk.Frame(content, bg=C["bg"])
        brand.pack(fill="x", padx=24, pady=(14, 0))
        tk.Label(
            brand, text="MAMC, New Delhi", font=("Segoe UI", 9, "bold"),
            bg=C["bg"], fg=C["text3"],
        ).pack(side="right")
        tk.Label(content, text="EXPERIMENT SETUP", font=("Segoe UI", 18, "bold"),
                 bg=C["bg"], fg=C["gold"]).pack(pady=(4, 5))
        tk.Label(content, text="Select drug and choose which eye receives it. "
                               "The other eye gets Normal Saline as control.",
                 font=("Segoe UI", 11), bg=C["bg"], fg=C["text2"],
                 wraplength=760, justify="center").pack(pady=(0, 16), padx=15)

        main = tk.Frame(content, bg=C["bg"])
        main.pack(expand=True, fill="x", padx=24)

        # Drug selection
        left = tk.Frame(
            main, bg=C["card"], padx=20, pady=15,
            highlightbackground=C["border"], highlightthickness=1,
        )
        left.grid(row=0, column=0, sticky="nsew", padx=8, pady=6)
        tk.Label(left, text="SELECT DRUG", font=("Segoe UI", 11, "bold"),
                 bg=C["card"], fg=C["text2"]).pack(anchor="w", pady=(0, 10))
        for name, d in DRUG_DATA.items():
            tk.Radiobutton(left, text=f"{name}  ({d['class']})",
                           variable=self.selected_drug, value=name,
                           font=("Segoe UI", 12), bg=C["card"], fg=C["text"],
                           selectcolor=C["soft_blue"], activebackground=C["card"],
                           activeforeground=C["gold"], anchor="w", padx=10, pady=6
                           ).pack(fill="x", pady=2)

        # Eye assignment
        right = tk.Frame(
            main, bg=C["card"], padx=20, pady=15,
            highlightbackground=C["border"], highlightthickness=1,
        )
        right.grid(row=0, column=1, sticky="nsew", padx=8, pady=6)
        tk.Label(right, text="DRUG EYE ASSIGNMENT", font=("Segoe UI", 11, "bold"),
                 bg=C["card"], fg=C["text2"]).pack(anchor="w", pady=(0, 10))
        for val, txt in [("right", "Right Eye → Drug  |  Left Eye → Saline"),
                         ("left",  "Left Eye → Drug  |  Right Eye → Saline")]:
            tk.Radiobutton(right, text=txt, variable=self.drug_eye, value=val,
                           font=("Segoe UI", 12), bg=C["card"], fg=C["text"],
                           selectcolor=C["soft_blue"], activebackground=C["card"],
                           activeforeground=C["gold"], anchor="w", padx=10, pady=8
                           ).pack(fill="x", pady=2)
        tk.Label(right, text="\nThe control eye (Normal Saline) shows\n"
                              "baseline parameters for comparison.",
                 font=("Segoe UI", 10, "italic"), bg=C["card"], fg=C["text3"],
                 justify="left").pack(anchor="w", pady=(10, 0))

        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=1)

        def arrange_panels(event):
            narrow = event.width < 820
            left.grid_configure(row=0, column=0, columnspan=2 if narrow else 1)
            right.grid_configure(row=1 if narrow else 0,
                                 column=0 if narrow else 1,
                                 columnspan=2 if narrow else 1)

        main.bind("<Configure>", arrange_panels)

        actions = tk.Frame(content, bg=C["bg"])
        actions.pack(fill="x", padx=24, pady=(12, 22))
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=1)
        tk.Button(
            actions, text="Theory and Practical", command=app.show_guide,
            font=("Segoe UI", 11, "bold"), bg=C["soft_blue"], fg=C["gold"],
            activebackground="#D7EAF8", activeforeground=C["text"],
            relief="raised", bd=1, padx=18, pady=10, cursor="hand2",
        ).grid(row=0, column=0, sticky="ew", padx=6, pady=3)
        tk.Button(
            actions, text="Administer Drug and Begin",
            font=("Segoe UI", 12, "bold"), bg=C["gold"], fg="white",
            activebackground="#0F4D80", activeforeground="white",
            relief="raised", bd=1, padx=22, pady=10,
            cursor="hand2", command=self._go,
        ).grid(row=0, column=1, sticky="ew", padx=6, pady=3)

    def _go(self):
        drug = self.selected_drug.get()
        if not drug:
            messagebox.showwarning("Select Drug", "Please select a drug.")
            return
        self.app.start_experiment(drug, self.drug_eye.get())


# =============================================================================
# EXPERIMENT FRAME
# =============================================================================
class ExperimentFrame(tk.Frame):
    PARAMETERS = ("Pupil", "Light Reflex", "Corneal Reflex", "Conjunctiva", "Tone")

    def __init__(self, parent, app, drug_name, drug_eye_side):
        super().__init__(parent, bg=C["bg"])
        self.app = app
        self.drug_name = drug_name
        self.drug_eye = drug_eye_side
        self.control_eye = "left" if drug_eye_side == "right" else "right"
        self.drug_data = DRUG_DATA[drug_name]
        self.active_tool = None
        self.observed = set()
        self.comparison_vars = {}
        self.comparison_window = None
        self.comparison_record = app.current_comparison_record

        self._build_ui()

    def _eye_data(self, side):
        return self.drug_data if side == self.drug_eye else BASELINE

    # ---- UI ----
    def _build_ui(self):
        # Top bar
        top = tk.Frame(self, bg=C["bg2"], padx=9, pady=5)
        top.pack(fill="x")

        actions = tk.Frame(top, bg=C["bg2"])
        actions.pack(side="right", padx=(8, 0))
        tk.Label(
            actions, text="MAMC, New Delhi", font=("Segoe UI", 8, "bold"),
            bg=C["bg2"], fg=C["text3"], anchor="e",
        ).pack(fill="x", padx=3, pady=(0, 2))
        action_buttons = tk.Frame(actions, bg=C["bg2"])
        action_buttons.pack(fill="x")
        tk.Button(action_buttons, text="Theory and Practical", font=("Segoe UI", 9),
                  bg=C["soft_blue"], fg=C["gold"], relief="raised", bd=1,
                  activebackground="#D7EAF8", activeforeground=C["text"], cursor="hand2",
                  command=self.app.show_guide).pack(side="left", padx=3)
        tk.Button(action_buttons, text="New Experiment", font=("Segoe UI", 9),
                  bg="#FFFFFF", fg=C["text2"], relief="raised", bd=1,
                  activebackground=C["soft_blue"], activeforeground=C["text"], cursor="hand2",
                  command=self.app.show_setup).pack(side="left", padx=3)

        identity = tk.Frame(top, bg=C["bg2"])
        identity.pack(side="left", fill="both", expand=True)

        logo_path = get_image_path(self.app.image_dir, "mamc_logo")
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path).resize((30, 30), Image.LANCZOS)
                self._logo = ImageTk.PhotoImage(img)
                tk.Label(identity, image=self._logo, bg=C["bg2"]).pack(
                    side="left", padx=(0, 7)
                )
            except Exception:
                pass

        identity_text = tk.Frame(identity, bg=C["bg2"])
        identity_text.pack(side="left", fill="both", expand=True)
        tk.Label(
            identity_text, text="Rabbit Eye Experiment",
            font=("Segoe UI", 13, "bold"), bg=C["bg2"], fg=C["gold"],
            anchor="w",
        ).pack(fill="x")
        drug_label = tk.Label(
            identity_text, text=f"Drug: {self.drug_name}",
            font=("Segoe UI", 9), bg=C["bg2"], fg=C["text2"],
            anchor="w", justify="left",
        )
        drug_label.pack(fill="x")

        def wrap_drug_name(event):
            drug_label.configure(wraplength=max(150, event.width - 48))

        identity.bind("<Configure>", wrap_drug_name)

        viewport = tk.Frame(self, bg=C["bg"])
        viewport.pack(fill="both", expand=True)
        viewport.grid_rowconfigure(0, weight=1)
        viewport.grid_columnconfigure(0, weight=1)
        body_canvas = tk.Canvas(viewport, bg=C["bg"], highlightthickness=0, bd=0)
        xbar = ttk.Scrollbar(viewport, orient="horizontal", command=body_canvas.xview)
        ybar = ttk.Scrollbar(viewport, orient="vertical", command=body_canvas.yview)
        body_canvas.configure(xscrollcommand=xbar.set, yscrollcommand=ybar.set)
        body_canvas.grid(row=0, column=0, sticky="nsew")
        ybar.grid(row=0, column=1, sticky="ns")
        xbar.grid(row=1, column=0, sticky="ew")

        body = tk.Frame(body_canvas, bg=C["bg"])
        body_id = body_canvas.create_window((0, 0), window=body, anchor="nw")

        def update_body_scroll(_event=None):
            body_canvas.configure(scrollregion=body_canvas.bbox("all"))

        def fit_body(event):
            body_canvas.itemconfigure(body_id, width=max(1, event.width))
            arrange = getattr(self, "_responsive_body_layout", None)
            if arrange is not None:
                arrange(event.width)
            update_body_scroll()

        body.bind("<Configure>", update_body_scroll)
        body_canvas.bind("<Configure>", fit_body)

        def scroll_body(event):
            body_canvas.yview_scroll(int(-event.delta / 120), "units")

        def scroll_body_sideways(event):
            body_canvas.xview_scroll(int(-event.delta / 120), "units")

        # ---- Left: Tools ----
        tools_frame = tk.Frame(body, bg=C["card"], width=195)
        tools_frame.pack(side="left", fill="y", padx=(8, 4), pady=8)
        tools_frame.pack_propagate(False)

        tk.Label(tools_frame, text="TOOLS", font=("Segoe UI", 10, "bold"),
                 bg=C["card"], fg=C["gold"]).pack(pady=(10, 5))

        tools = [
            ("📏 Ruler",        "ruler",       "Click & drag across pupil"),
            ("🔦 Torch",        "torch",       "Move near pupil to test"),
            ("🧹 Cotton Swab",  "cotton",      "Drag swab to cornea"),
            ("👁 Conjunctiva",  "conjunctiva", "Click to inspect"),
            ("✋ Tone/IOP",     "tone",        "Click to palpate"),
        ]
        self.tool_btns = {}
        for text, tid, tip in tools:
            btn = tk.Button(tools_frame, text=text, font=("Segoe UI", 11),
                            bg=C["bg"], fg=C["text"], relief="flat", anchor="w",
                            padx=10, pady=6, cursor="hand2",
                            command=lambda t=tid: self._select_tool(t))
            btn.pack(fill="x", padx=8, pady=2)
            self.tool_btns[tid] = btn
            tk.Label(tools_frame, text=f"  {tip}", font=("Segoe UI", 8),
                     bg=C["card"], fg=C["text3"]).pack(fill="x", padx=15)

        self.instruction = tk.Label(tools_frame, text="Select a tool,\nthen use it on an eye",
                                    font=("Segoe UI", 9, "italic"),
                                    bg=C["card"], fg=C["gold"], justify="left", wraplength=170)
        self.instruction.pack(pady=(12, 5), padx=10, anchor="w")

        # Mechanism box
        mf = tk.Frame(tools_frame, bg=C["bg"], padx=8, pady=8)
        mf.pack(fill="x", padx=8, pady=(8, 8))
        tk.Label(mf, text="MECHANISM", font=("Segoe UI", 9, "bold"),
                 bg=C["bg"], fg=C["amber"]).pack(anchor="w")
        tk.Label(mf, text=self.drug_data["mechanism"], font=("Segoe UI", 8),
                 bg=C["bg"], fg=C["text2"], wraplength=160, justify="left").pack(anchor="w", pady=(4, 0))
        tk.Label(mf, text=f"Onset: {self.drug_data['onset']}  •  Duration: {self.drug_data['duration']}",
                 font=("Segoe UI", 8), bg=C["bg"], fg=C["text3"]).pack(anchor="w", pady=(4, 0))

        # ---- Centre: Eyes ----
        centre = tk.Frame(body, bg=C["bg"])
        centre.pack(side="left", fill="both", expand=True, padx=4, pady=8)
        eyes = tk.Frame(centre, bg=C["bg"])
        eyes.pack(expand=True)

        eye_frames = []
        for side in ["left", "right"]:
            fr = tk.Frame(eyes, bg=C["bg"])
            fr.pack(side="left", padx=12)
            eye_frames.append(fr)
            is_drug = (side == self.drug_eye)
            lbl = f"💉 {self.drug_name}" if is_drug else "💧 Normal Saline"
            clr = self.drug_data["color"] if is_drug else C["green"]
            tk.Label(fr, text=lbl, font=("Segoe UI", 10, "bold"),
                     bg=C["bg"], fg=clr).pack(pady=(0, 4))

            ec = EyeCanvas(fr, self._eye_data(side), self.app.image_dir, side, self)
            ec.pack()
            tk.Label(fr, text=f"{side.upper()} EYE", font=("Segoe UI", 9, "bold"),
                     bg=C["bg"], fg=C["text3"]).pack(pady=(2, 0))

            if side == "left":
                self.left_eye = ec
            else:
                self.right_eye = ec

        # ---- Right: Results + Comparison ----
        rpanel = tk.Frame(body, bg=C["card"], width=280)
        rpanel.pack(side="right", fill="y", padx=(4, 8), pady=8)
        rpanel.pack_propagate(False)

        tk.Label(rpanel, text="FINDINGS", font=("Segoe UI", 10, "bold"),
                 bg=C["card"], fg=C["gold"]).pack(pady=(10, 5))

        self.result_text = tk.Text(rpanel, font=("Consolas", 10), bg=C["bg"],
                                   fg=C["text"], relief="flat", wrap="word",
                                   padx=10, pady=8, height=12)
        self.result_text.pack(fill="x", padx=8)
        self.result_text.tag_configure("title", font=("Segoe UI", 11, "bold"), foreground=C["gold"])
        self.result_text.tag_configure("good", foreground=C["green"])
        self.result_text.tag_configure("bad", foreground=C["red"])
        self.result_text.tag_configure("warn", foreground=C["amber"])
        self.result_text.tag_configure("info", foreground=C["text2"], font=("Consolas", 9))
        self.result_text.configure(state="disabled")

        # Entry opens after the first genuine observation. Values are typed by
        # the student and live in the application-level session notebook.
        self.findings_progress_var = tk.StringVar(
            value="No observation recorded yet.\nUse a tool on either eye to begin."
        )
        tk.Label(
            rpanel, textvariable=self.findings_progress_var,
            font=("Segoe UI", 9), bg=C["card"], fg=C["text2"],
            justify="left", wraplength=245,
        ).pack(fill="x", padx=12, pady=(10, 6))
        self.comparison_button = tk.Button(
            rpanel, text="Enter Comparison Table",
            font=("Segoe UI", 10, "bold"), bg=C["bg2"], fg=C["text3"],
            activebackground="#D7EAF8", activeforeground=C["text"],
            disabledforeground="#7D8B98", relief="raised", bd=1,
            padx=12, pady=8, cursor="hand2", state="disabled",
            command=self._open_comparison_table,
        )
        self.comparison_button.pack(fill="x", padx=10, pady=(0, 12))

        scroll_tag = "RabbitEyeScroll{}".format(id(self))
        body_canvas.bind_class(scroll_tag, "<MouseWheel>", scroll_body)
        body_canvas.bind_class(scroll_tag, "<Shift-MouseWheel>", scroll_body_sideways)

        def attach_scroll_tag(widget):
            tags = list(widget.bindtags())
            if scroll_tag not in tags:
                tags.insert(max(len(tags) - 1, 0), scroll_tag)
                widget.bindtags(tuple(tags))
            for child in widget.winfo_children():
                attach_scroll_tag(child)

        attach_scroll_tag(viewport)

        layout_state = {"narrow": None, "stack_eyes": None}

        def arrange_work_area(width):
            narrow = width < 1190
            stack_eyes = width < 760
            if (layout_state["narrow"] == narrow and
                    layout_state["stack_eyes"] == stack_eyes):
                return
            layout_state["narrow"] = narrow
            layout_state["stack_eyes"] = stack_eyes
            for eye_frame in eye_frames:
                eye_frame.pack_forget()
            for eye_frame in eye_frames:
                eye_frame.pack(
                    side="top" if stack_eyes else "left",
                    padx=12, pady=(0, 8) if stack_eyes else 0,
                )
            tools_frame.pack_forget()
            centre.pack_forget()
            rpanel.pack_forget()
            if narrow:
                tools_frame.pack_propagate(True)
                rpanel.pack_propagate(True)
                centre.pack(side="top", fill="x", padx=4, pady=8)
                tools_frame.pack(side="left", fill="y", padx=(8, 4), pady=8)
                rpanel.pack(side="left", fill="y", padx=(4, 8), pady=8)
            else:
                tools_frame.pack_propagate(False)
                rpanel.pack_propagate(False)
                tools_frame.pack(side="left", fill="y", padx=(8, 4), pady=8)
                centre.pack(side="left", fill="both", expand=True, padx=4, pady=8)
                rpanel.pack(side="right", fill="y", padx=(4, 8), pady=8)
            self.after_idle(update_body_scroll)

        self._responsive_body_layout = arrange_work_area
        self.after_idle(lambda: arrange_work_area(body_canvas.winfo_width()))

    # ---- tool selection ----
    def _select_tool(self, tool_id):
        self.active_tool = tool_id
        for tid, btn in self.tool_btns.items():
            btn.configure(bg=(C["gold"] if tid == tool_id else C["bg"]),
                          fg=(C["bg3"] if tid == tool_id else C["text"]))

        instructions = {
            "ruler":       "📏 Click & drag across the pupil\n    on either eye to measure.",
            "torch":       "🔦 Move your mouse over an eye.\n    Watch the pupil react!",
            "cotton":      "🧹 Click & drag the cotton swab\n    to the centre of the eye.",
            "conjunctiva": "👁 Click on an eye to inspect\n    conjunctival vasculature.",
            "tone":        "✋ Click on an eye to palpate\n    for intraocular pressure.",
        }
        self.instruction.configure(text=instructions.get(tool_id, ""))

        # Bind appropriate events on both eye canvases
        for eye in (self.left_eye, self.right_eye):
            if tool_id == "ruler":
                eye.bind_ruler()
            elif tool_id == "torch":
                eye.bind_torch()
            elif tool_id == "cotton":
                eye.bind_cotton()
            elif tool_id == "conjunctiva":
                eye.bind_click(lambda e, s=eye.side: self._click_conjunctiva(s))
            elif tool_id == "tone":
                eye.bind_click(lambda e, s=eye.side: self._click_tone(s))

    def _click_conjunctiva(self, side):
        data = self._eye_data(side)
        status = data["conjunctiva"]
        desc = data["conjunctiva_desc"]
        ok = status in ("normal", "no_change")
        self.show_result(
            f"👁 CONJUNCTIVA — {side.upper()} EYE",
            f"Status: {status.upper()}\n{desc}\n\n"
            + ("Normal pink vasculature."
               if ok else
               "Congested — parasympathomimetic vasodilation."
               if status == "congested" else
               "Blanched — sympathomimetic vasoconstriction."),
            ok
        )

    def _click_tone(self, side):
        data = self._eye_data(side)
        tone = data["tone"]
        desc = data["tone_desc"]
        ok = tone == "normal"
        self.show_result(
            f"✋ TONE (IOP) — {side.upper()} EYE",
            f"Tone: {tone.upper()}\n{desc}\n\n"
            + ("Normal firmness on palpation."
               if ok else
               "Globe feels HARD — elevated IOP."
               if tone == "increased" else
               "Globe feels SOFT — reduced IOP."),
            ok
        )

    # ---- result display ----
    def show_result(self, title, body, is_good=True):
        self._record_finding(title)
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("end", title + "\n\n", "title")
        self.result_text.insert("end", body, "good" if is_good else "bad")
        self.result_text.configure(state="disabled")

    def _record_finding(self, title):
        """Track genuine tool observations without revealing expected values."""
        title_upper = title.upper()
        parameter = None
        for marker, name in (
            ("PUPIL SIZE", "Pupil"),
            ("LIGHT REFLEX", "Light Reflex"),
            ("CORNEAL REFLEX", "Corneal Reflex"),
            ("CONJUNCTIVA", "Conjunctiva"),
            ("TONE", "Tone"),
        ):
            if marker in title_upper:
                parameter = name
                break

        side = None
        if "LEFT EYE" in title_upper:
            side = "left"
        elif "RIGHT EYE" in title_upper:
            side = "right"

        if parameter and side:
            self.observed.add((parameter, side))

        total = len(self.PARAMETERS) * 2
        completed = len(self.observed)
        if completed:
            self.findings_progress_var.set(
                f"Observations viewed: {completed} of {total}\n"
                "You can enter and save findings now."
            )
            self.comparison_button.configure(
                state="normal", bg=C["gold"], fg="white",
                activebackground="#0F4D80", activeforeground="white",
            )
        else:
            self.findings_progress_var.set(
                "No observation recorded yet.\nUse a tool on either eye to begin."
            )

    def _legacy_open_comparison_table(self):
        if not self.observed:
            messagebox.showinfo(
                "Observe First",
                "View at least one genuine eye observation before entering findings.",
                parent=self.winfo_toplevel(),
            )
            return

        if self.comparison_window is not None:
            try:
                if self.comparison_window.winfo_exists():
                    self.comparison_window.deiconify()
                    self.comparison_window.lift()
                    self.comparison_window.focus_force()
                    return
            except tk.TclError:
                pass

        window = tk.Toplevel(self)
        self.comparison_window = window
        window.title("Rabbit Eye Comparison — Student Findings")
        window.configure(bg=C["bg"])
        set_window_size(window, 780, 590, 560, 430, margin_x=40, margin_y=60)
        window.transient(self.winfo_toplevel())

        def close_window():
            self.comparison_window = None
            window.destroy()

        window.protocol("WM_DELETE_WINDOW", close_window)

        header = tk.Frame(window, bg=C["bg2"], padx=18, pady=12)
        header.pack(fill="x")
        tk.Label(
            header, text="COMPARISON TABLE", font=("Segoe UI", 16, "bold"),
            bg=C["bg2"], fg=C["gold"],
        ).pack(side="left")
        tk.Label(
            header, text="MAMC, New Delhi", font=("Segoe UI", 8, "bold"),
            bg=C["bg2"], fg=C["text3"],
        ).pack(side="right")

        tk.Label(
            window,
            text=("Enter your own observed findings. The expected answers are "
                  "intentionally not filled in."),
            font=("Segoe UI", 10), bg=C["bg"], fg=C["text2"],
            wraplength=700, justify="left",
        ).pack(fill="x", padx=22, pady=(14, 8))

        table = tk.Frame(
            window, bg=C["card"], padx=12, pady=10,
            highlightbackground=C["border"], highlightthickness=1,
        )
        table.pack(fill="both", expand=True, padx=22, pady=6)
        table.grid_columnconfigure(0, weight=1)
        table.grid_columnconfigure(1, weight=2)
        table.grid_columnconfigure(2, weight=2)

        for column, (heading, colour) in enumerate((
            ("Parameter", C["text2"]),
            (f"Drug eye — {self.drug_name}", self.drug_data["color"]),
            ("Saline control eye", C["green"]),
        )):
            tk.Label(
                table, text=heading, font=("Segoe UI", 9, "bold"),
                bg=C["card"], fg=colour, wraplength=210, justify="left",
            ).grid(row=0, column=column, sticky="ew", padx=6, pady=(2, 8))

        saved_entries = self._comparison_values()
        self.comparison_vars.clear()
        for row, parameter in enumerate(self.PARAMETERS, 1):
            tk.Label(
                table, text=parameter, font=("Segoe UI", 10, "bold"),
                bg=C["card"], fg=C["text2"], anchor="w",
            ).grid(row=row, column=0, sticky="ew", padx=6, pady=5)
            for column, eye_kind in ((1, "drug"), (2, "saline")):
                variable = tk.StringVar(
                    value=saved_entries.get((parameter, eye_kind), "")
                )
                self.comparison_vars[(parameter, eye_kind)] = variable
                tk.Entry(
                    table, textvariable=variable, font=("Segoe UI", 10),
                    bg="#FFFFFF", fg=C["text"], insertbackground=C["text"],
                    relief="solid", bd=1,
                ).grid(row=row, column=column, sticky="ew", padx=6, pady=5, ipady=6)

        actions = tk.Frame(window, bg=C["bg"])
        actions.pack(fill="x", padx=22, pady=(8, 16))
        tk.Button(
            actions, text="Close", command=close_window,
            font=("Segoe UI", 10), bg="#FFFFFF", fg=C["text2"],
            activebackground=C["soft_blue"], activeforeground=C["text"],
            relief="raised", bd=1, padx=18, pady=8,
        ).pack(side="left")
        tk.Button(
            actions, text="Clear Entries",
            command=lambda: [var.set("") for var in self.comparison_vars.values()],
            font=("Segoe UI", 10), bg=C["soft_blue"], fg=C["gold"],
            activebackground="#D7EAF8", activeforeground=C["text"],
            relief="raised", bd=1, padx=18, pady=8,
        ).pack(side="left", padx=8)
        tk.Button(
            actions, text="Save Comparison as PNG",
            command=self._save_comparison_image,
            font=("Segoe UI", 10, "bold"), bg=C["gold"], fg="white",
            activebackground="#0F4D80", activeforeground="white",
            relief="raised", bd=1, padx=18, pady=8,
        ).pack(side="right")

    @staticmethod
    def _export_font(size, bold=False):
        candidates = [
            os.path.join(
                os.environ.get("WINDIR", r"C:\Windows"), "Fonts",
                "seguisb.ttf" if bold else "segoeui.ttf",
            ),
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold
            else "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for candidate in candidates:
            try:
                if os.path.exists(candidate):
                    return ImageFont.truetype(candidate, size)
            except OSError:
                continue
        return ImageFont.load_default()

    def _legacy_comparison_values(self):
        return {
            key: variable.get().strip()
            for key, variable in self.comparison_vars.items()
        }

    def _legacy_save_comparison_image(self, path=None):
        interactive = path is None
        values = self._comparison_values()
        missing = [key for key, value in values.items() if not value]
        if missing:
            messagebox.showwarning(
                "Incomplete Comparison",
                "Please enter a finding in every Drug eye and Saline eye cell.",
                parent=self.comparison_window,
            )
            return None

        if path is None:
            stamp = datetime.now().strftime("%Y%m%d_%H%M")
            path = filedialog.asksaveasfilename(
                parent=self.comparison_window,
                title="Save Rabbit Eye Comparison",
                initialfile=f"Rabbit_Eye_Comparison_{stamp}.png",
                defaultextension=".png",
                filetypes=[("PNG image", "*.png")],
            )
            if not path:
                return None

        try:
            self._render_comparison_image(path, values)
        except (OSError, ValueError) as exc:
            messagebox.showerror(
                "Could Not Save Image", str(exc), parent=self.comparison_window,
            )
            return None

        if interactive and self.comparison_window is not None:
            messagebox.showinfo(
                "Image Saved",
                f"The comparison image was saved to:\n{path}",
                parent=self.comparison_window,
            )
        return path

    def _legacy_render_comparison_image(self, path, values):
        """Create a portable, data-rendered PNG rather than a screen capture."""
        width, height = 1400, 900
        image = Image.new("RGB", (width, height), C["bg"])
        draw = ImageDraw.Draw(image)
        title_font = self._export_font(44, bold=True)
        subtitle_font = self._export_font(24)
        heading_font = self._export_font(24, bold=True)
        cell_font = self._export_font(23)
        parameter_font = self._export_font(23, bold=True)
        small_font = self._export_font(19)

        draw.rounded_rectangle((45, 40, width - 45, 155), radius=20, fill=C["bg2"])
        draw.text((75, 62), "Rabbit Eye Comparison", font=title_font, fill=C["gold"])
        brand = "MAMC, New Delhi"
        brand_box = draw.textbbox((0, 0), brand, font=small_font)
        draw.text(
            (width - 75 - (brand_box[2] - brand_box[0]), 84), brand,
            font=small_font, fill=C["text3"],
        )
        draw.text(
            (75, 174), f"Drug tested: {self.drug_name}",
            font=subtitle_font, fill=C["text2"],
        )

        x_positions = (65, 390, 875, 1335)
        table_top = 225
        header_height = 80
        row_height = 102
        table_bottom = table_top + header_height + row_height * len(self.PARAMETERS)
        draw.rounded_rectangle(
            (x_positions[0], table_top, x_positions[-1], table_bottom),
            radius=14, fill=C["card"], outline=C["border"], width=2,
        )

        headers = (
            "Parameter",
            f"Drug eye — {self.drug_name}",
            "Saline control eye",
        )
        header_colours = (C["text2"], self.drug_data["color"], C["green"])
        for column, heading in enumerate(headers):
            left, right = x_positions[column], x_positions[column + 1]
            if column:
                draw.line(
                    (left, table_top, left, table_bottom),
                    fill=C["border"], width=2,
                )
            wrapped = "\n".join(textwrap.wrap(heading, width=26))
            bounds = draw.multiline_textbbox(
                (0, 0), wrapped, font=heading_font, spacing=5, align="center",
            )
            text_width = bounds[2] - bounds[0]
            text_height = bounds[3] - bounds[1]
            draw.multiline_text(
                ((left + right - text_width) / 2,
                 table_top + (header_height - text_height) / 2 - 2),
                wrapped, font=heading_font, fill=header_colours[column],
                spacing=5, align="center",
            )

        draw.line(
            (x_positions[0], table_top + header_height,
             x_positions[-1], table_top + header_height),
            fill=C["border"], width=2,
        )

        def draw_cell_text(value, box, font, colour, wrap_width=31, bold=False):
            del bold  # Font weight is already represented by ``font``.
            lines = textwrap.wrap(str(value), width=wrap_width) or [""]
            if len(lines) > 3:
                lines = lines[:3]
                lines[-1] = lines[-1].rstrip(" .") + "…"
            wrapped = "\n".join(lines)
            bounds = draw.multiline_textbbox(
                (0, 0), wrapped, font=font, spacing=5, align="left",
            )
            text_height = bounds[3] - bounds[1]
            left, top, _right, bottom = box
            draw.multiline_text(
                (left + 18, top + (bottom - top - text_height) / 2 - 2),
                wrapped, font=font, fill=colour, spacing=5, align="left",
            )

        for row, parameter in enumerate(self.PARAMETERS):
            top = table_top + header_height + row * row_height
            bottom = top + row_height
            if row % 2:
                draw.rectangle(
                    (x_positions[0] + 2, top, x_positions[-1] - 2, bottom),
                    fill=C["soft_blue"],
                )
            if row:
                draw.line(
                    (x_positions[0], top, x_positions[-1], top),
                    fill=C["border"], width=1,
                )
            draw_cell_text(
                parameter, (x_positions[0], top, x_positions[1], bottom),
                parameter_font, C["text2"], wrap_width=22,
            )
            draw_cell_text(
                values[(parameter, "drug")],
                (x_positions[1], top, x_positions[2], bottom),
                cell_font, C["text"], wrap_width=32,
            )
            draw_cell_text(
                values[(parameter, "saline")],
                (x_positions[2], top, x_positions[3], bottom),
                cell_font, C["text"], wrap_width=30,
            )

        # Redraw the column rules after alternating row fills.
        for boundary in x_positions[1:-1]:
            draw.line(
                (boundary, table_top, boundary, table_bottom),
                fill=C["border"], width=2,
            )

        footer = "Student-entered findings • Saved " + datetime.now().strftime(
            "%d %b %Y, %I:%M %p"
        )
        draw.text((75, 846), footer, font=small_font, fill=C["text3"])
        image.save(path, format="PNG")

    @staticmethod
    def _record_label(record):
        side = str(record["drug_eye"]).title()
        return f"Test {record['id']} — {record['drug_name']} — drug in {side} eye"

    def _open_comparison_table(self):
        """Open the persistent, cumulative student observation notebook."""
        if not self.observed:
            messagebox.showinfo(
                "Observe First",
                "View at least one genuine eye observation before entering findings.",
                parent=self.winfo_toplevel(),
            )
            return
        if self.comparison_window is not None:
            try:
                if self.comparison_window.winfo_exists():
                    self.comparison_window.deiconify()
                    self.comparison_window.lift()
                    self.comparison_window.focus_force()
                    return
            except tk.TclError:
                pass

        window = tk.Toplevel(self)
        self.comparison_window = window
        window.title("Rabbit Eye — Session Comparison Notebook")
        window.configure(bg=C["bg"])
        set_window_size(window, 860, 690, 600, 470, margin_x=40, margin_y=55)
        window.transient(self.winfo_toplevel())

        header = tk.Frame(window, bg=C["bg2"], padx=18, pady=11)
        header.pack(fill="x")
        tk.Label(
            header, text="SESSION COMPARISON NOTEBOOK",
            font=("Segoe UI", 16, "bold"), bg=C["bg2"], fg=C["gold"],
        ).pack(side="left")
        tk.Label(
            header, text="MAMC, New Delhi", font=("Segoe UI", 8, "bold"),
            bg=C["bg2"], fg=C["text3"],
        ).pack(side="right")

        tk.Label(
            window,
            text=("Type only what you observed. Entries are retained immediately "
                  "when you close this window or begin another test."),
            font=("Segoe UI", 9), bg=C["bg"], fg=C["text2"],
            wraplength=800, justify="left",
        ).pack(fill="x", padx=20, pady=(10, 5))

        selection = tk.Frame(window, bg=C["bg"])
        selection.pack(fill="x", padx=20, pady=(0, 6))
        tk.Label(
            selection, text="Test to view or edit", font=("Segoe UI", 9, "bold"),
            bg=C["bg"], fg=C["text2"],
        ).pack(side="left", padx=(0, 9))
        labels = [self._record_label(record) for record in self.app.comparison_records]
        records_by_label = dict(zip(labels, self.app.comparison_records))
        selected_label = tk.StringVar(value=self._record_label(self.comparison_record))
        selector = ttk.Combobox(
            selection, textvariable=selected_label, values=labels,
            state="readonly", font=("Segoe UI", 9),
        )
        selector.pack(side="left", fill="x", expand=True)

        editor = tk.Frame(
            window, bg=C["card"], padx=10, pady=8,
            highlightbackground=C["border"], highlightthickness=1,
        )
        editor.pack(fill="both", expand=True, padx=20, pady=5)
        status_var = tk.StringVar()
        self._comparison_selected_record = self.comparison_record

        def store_value(record, key, variable):
            record["values"][key] = variable.get().strip()
            record["saved_at"] = None
            status_var.set("Draft retained in this session")

        def render_editor(_event=None):
            record = records_by_label[selected_label.get()]
            self._comparison_selected_record = record
            for child in editor.winfo_children():
                child.destroy()
            self.comparison_vars.clear()
            for column in range(3):
                editor.grid_columnconfigure(column, weight=1 if column == 0 else 2)
            headings = (
                ("Parameter", C["text2"]),
                (f"Drug eye — {record['drug_name']}", DRUG_DATA[record["drug_name"]]["color"]),
                ("Saline control eye", C["green"]),
            )
            for column, (heading, colour) in enumerate(headings):
                tk.Label(
                    editor, text=heading, font=("Segoe UI", 9, "bold"),
                    bg=C["card"], fg=colour, wraplength=230, justify="left",
                ).grid(row=0, column=column, sticky="ew", padx=5, pady=(2, 7))
            for row, parameter in enumerate(self.PARAMETERS, 1):
                tk.Label(
                    editor, text=parameter, font=("Segoe UI", 10, "bold"),
                    bg=C["card"], fg=C["text2"], anchor="w",
                ).grid(row=row, column=0, sticky="ew", padx=5, pady=4)
                for column, eye_kind in ((1, "drug"), (2, "saline")):
                    key = (parameter, eye_kind)
                    variable = tk.StringVar(value=record["values"].get(key, ""))
                    self.comparison_vars[key] = variable
                    variable.trace_add(
                        "write",
                        lambda *_args, rec=record, item=key, var=variable:
                            store_value(rec, item, var),
                    )
                    tk.Entry(
                        editor, textvariable=variable, font=("Segoe UI", 10),
                        bg="#FFFFFF", fg=C["text"], insertbackground=C["text"],
                        relief="solid", bd=1,
                    ).grid(row=row, column=column, sticky="ew", padx=5, pady=4, ipady=5)
            saved_at = record.get("saved_at")
            status_var.set(
                "Saved " + saved_at.strftime("%d %b %Y, %I:%M %p")
                if saved_at else "Draft retained in this session"
            )

        selector.bind("<<ComboboxSelected>>", render_editor)
        render_editor()
        tk.Label(
            window, textvariable=status_var, font=("Segoe UI", 8, "italic"),
            bg=C["bg"], fg=C["text3"], anchor="w",
        ).pack(fill="x", padx=22, pady=(1, 4))

        def save_current():
            record = self._comparison_selected_record
            if not any(value.strip() for value in record["values"].values()):
                messagebox.showwarning(
                    "No Manual Entry", "Type at least one observed finding before saving.",
                    parent=window,
                )
                return
            record["saved_at"] = datetime.now()
            status_var.set(
                "Saved " + record["saved_at"].strftime("%d %b %Y, %I:%M %p")
            )

        def clear_current():
            if not messagebox.askyesno(
                    "Clear Current Test", "Clear every manual entry for this test?",
                    parent=window):
                return
            for variable in self.comparison_vars.values():
                variable.set("")

        actions = tk.Frame(window, bg=C["bg"])
        actions.pack(fill="x", padx=20, pady=(4, 13))
        for column in range(5):
            actions.grid_columnconfigure(column, weight=1)
        buttons = (
            ("Close", lambda: (setattr(self, "comparison_window", None), window.destroy()),
             "#FFFFFF", C["text2"]),
            ("Clear Current", clear_current, C["soft_blue"], C["gold"]),
            ("Save Current Test", save_current, C["soft_green"], C["green"]),
            ("Export All CSV", self._save_comparison_csv, "#6A3D8F", "white"),
            ("Export All PNG", self._save_comparison_image, C["gold"], "white"),
        )
        for column, (label, command, bg, fg) in enumerate(buttons):
            tk.Button(
                actions, text=label, command=command,
                font=("Segoe UI", 9, "bold"), bg=bg, fg=fg,
                activebackground="#D7EAF8", activeforeground=C["text"],
                relief="raised", bd=1, padx=7, pady=7,
            ).grid(row=0, column=column, sticky="ew", padx=3)

        def close_window():
            self.comparison_window = None
            window.destroy()

        window.protocol("WM_DELETE_WINDOW", close_window)

    def _comparison_values(self, record=None):
        record = record or getattr(self, "_comparison_selected_record", self.comparison_record)
        return dict(record["values"])

    def _records_with_entries(self):
        return [
            record for record in self.app.comparison_records
            if any(value.strip() for value in record["values"].values())
        ]

    def _save_comparison_csv(self, path=None):
        records = self._records_with_entries()
        if not records:
            messagebox.showwarning(
                "No Manual Entries", "Enter at least one finding before exporting.",
                parent=self.comparison_window,
            )
            return None
        interactive = path is None
        if path is None:
            stamp = datetime.now().strftime("%Y%m%d_%H%M")
            path = filedialog.asksaveasfilename(
                parent=self.comparison_window, title="Export All Rabbit Eye Tests",
                initialfile=f"Rabbit_Eye_Session_{stamp}.csv",
                defaultextension=".csv", filetypes=[("CSV table", "*.csv")],
            )
            if not path:
                return None
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as stream:
                writer = csv.writer(stream)
                writer.writerow((
                    "Test", "Drug", "Drug eye", "Parameter",
                    "Drug-eye observation", "Saline-eye observation",
                ))
                for record in records:
                    for parameter in self.PARAMETERS:
                        writer.writerow((
                            record["id"], record["drug_name"], record["drug_eye"].title(),
                            parameter, record["values"].get((parameter, "drug"), ""),
                            record["values"].get((parameter, "saline"), ""),
                        ))
        except OSError as exc:
            messagebox.showerror("Could Not Export CSV", str(exc), parent=self.comparison_window)
            return None
        if interactive:
            messagebox.showinfo("CSV Exported", f"All entered tests were saved to:\n{path}", parent=self.comparison_window)
        return path

    def _save_comparison_image(self, path=None):
        records = self._records_with_entries()
        if not records:
            messagebox.showwarning(
                "No Manual Entries", "Enter at least one finding before exporting.",
                parent=self.comparison_window,
            )
            return None
        interactive = path is None
        if path is None:
            stamp = datetime.now().strftime("%Y%m%d_%H%M")
            path = filedialog.asksaveasfilename(
                parent=self.comparison_window, title="Export All Rabbit Eye Tests",
                initialfile=f"Rabbit_Eye_Session_{stamp}.png",
                defaultextension=".png", filetypes=[("PNG image", "*.png")],
            )
            if not path:
                return None
        try:
            self._render_comparison_image(path, records)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Could Not Save Image", str(exc), parent=self.comparison_window)
            return None
        if interactive:
            messagebox.showinfo("Image Saved", f"All entered tests were saved to:\n{path}", parent=self.comparison_window)
        return path

    def _render_comparison_image(self, path, records=None):
        """Render all manually entered session tests as one readable table."""
        records = records or self._records_with_entries()
        width = 1800
        top = 230
        header_height = 80
        title_font = self._export_font(42, bold=True)
        subtitle_font = self._export_font(22)
        heading_font = self._export_font(22, bold=True)
        cell_font = self._export_font(21)
        small_font = self._export_font(18)
        xs = (45, 145, 445, 610, 835, 1310, 1755)
        cell_spacing = 6
        measure_draw = ImageDraw.Draw(Image.new("RGB", (4, 4), C["bg"]))

        def wrapped_lines(value, pixel_width):
            width_hint = max(7, int(pixel_width / 15))
            return textwrap.wrap(
                str(value or "—"), width=width_hint,
                break_long_words=True, break_on_hyphens=True,
            ) or ["—"]

        def rendered_height(lines):
            bounds = measure_draw.multiline_textbbox(
                (0, 0), "\n".join(lines), font=cell_font,
                spacing=cell_spacing,
            )
            return bounds[3] - bounds[1]

        rows = []
        for record in records:
            for parameter_index, parameter in enumerate(self.PARAMETERS):
                values = (
                    record["id"] if parameter_index == 0 else "",
                    record["drug_name"] if parameter_index == 0 else "",
                    record["drug_eye"].title() if parameter_index == 0 else "",
                    parameter,
                    record["values"].get((parameter, "drug"), ""),
                    record["values"].get((parameter, "saline"), ""),
                )
                line_sets = [
                    wrapped_lines(value, xs[index + 1] - xs[index] - 24)
                    for index, value in enumerate(values)
                ]
                row_height = max(
                    82,
                    max(rendered_height(lines) for lines in line_sets) + 28,
                )
                rows.append((record, parameter_index, parameter, values, line_sets, row_height))

        table_bottom = top + header_height + sum(row[-1] for row in rows)
        height = table_bottom + 105
        image = Image.new("RGB", (width, height), C["bg"])
        draw = ImageDraw.Draw(image)

        draw.rounded_rectangle((45, 35, width - 45, 150), radius=18, fill=C["bg2"])
        draw.text((72, 58), "Rabbit Eye — Session Comparison Table", font=title_font, fill=C["gold"])
        brand = "MAMC, New Delhi"
        bounds = draw.textbbox((0, 0), brand, font=small_font)
        draw.text((width - 72 - (bounds[2] - bounds[0]), 88), brand, font=small_font, fill=C["text3"])
        draw.text(
            (72, 172), f"{len(records)} test(s) • student-entered observations",
            font=subtitle_font, fill=C["text2"],
        )

        draw.rounded_rectangle((xs[0], top, xs[-1], table_bottom), radius=12,
                               fill=C["card"], outline=C["border"], width=2)
        headers = ("Test", "Drug", "Drug eye", "Parameter", "Drug-eye observation", "Saline-eye observation")
        for column, heading in enumerate(headers):
            left, right = xs[column], xs[column + 1]
            if column:
                draw.line((left, top, left, table_bottom), fill=C["border"], width=2)
            wrapped = "\n".join(textwrap.wrap(heading, width=22))
            box = draw.multiline_textbbox((0, 0), wrapped, font=heading_font, spacing=4, align="center")
            tw, th = box[2] - box[0], box[3] - box[1]
            draw.multiline_text(((left + right - tw) / 2, top + (header_height - th) / 2 - 2),
                                wrapped, font=heading_font, fill=C["text2"], spacing=4, align="center")
        draw.line((xs[0], top + header_height, xs[-1], top + header_height), fill=C["border"], width=2)

        def cell_text(value, lines, left, row_top, right, row_bottom, colour=C["text"]):
            wrapped = "\n".join(lines)
            box = draw.multiline_textbbox(
                (0, 0), wrapped, font=cell_font, spacing=cell_spacing,
            )
            th = box[3] - box[1]
            origin_y = row_top + (row_bottom - row_top - th) / 2 - box[1]
            draw.multiline_text(
                (left + 12, origin_y), wrapped, font=cell_font,
                fill=colour, spacing=cell_spacing,
            )

        row_top = top + header_height
        for row_index, (record, parameter_index, parameter, values, line_sets, row_height) in enumerate(rows):
            row_bottom = row_top + row_height
            if row_index % 2:
                draw.rectangle((xs[0] + 2, row_top, xs[-1] - 2, row_bottom), fill=C["soft_blue"])
            if row_index:
                draw.line((xs[0], row_top, xs[-1], row_top), fill=C["border"], width=1)
            if parameter_index == 0:
                cell_text(values[0], line_sets[0], xs[0], row_top, xs[1], row_bottom, C["gold"])
                cell_text(values[1], line_sets[1], xs[1], row_top, xs[2], row_bottom)
                cell_text(values[2], line_sets[2], xs[2], row_top, xs[3], row_bottom)
            cell_text(parameter, line_sets[3], xs[3], row_top, xs[4], row_bottom, C["text2"])
            cell_text(values[4], line_sets[4], xs[4], row_top, xs[5], row_bottom)
            cell_text(values[5], line_sets[5], xs[5], row_top, xs[6], row_bottom)
            row_top = row_bottom
        for boundary in xs[1:-1]:
            draw.line((boundary, top, boundary, table_bottom), fill=C["border"], width=2)
        footer = "Student-entered findings • Exported " + datetime.now().strftime("%d %b %Y, %I:%M %p")
        draw.text((72, table_bottom + 38), footer, font=small_font, fill=C["text3"])
        image.save(path, format="PNG")

    def destroy(self):
        if self.comparison_window is not None:
            try:
                if self.comparison_window.winfo_exists():
                    self.comparison_window.destroy()
            except tk.TclError:
                pass
            self.comparison_window = None
        super().destroy()


# =============================================================================
class RabbitEyeApp:
    def __init__(self, root, image_dir=None):
        self.root = root
        self.root.title("Rabbit Eye Experiment — MAMC, New Delhi")
        self.root.configure(bg=C["bg3"])
        if image_dir and os.path.isdir(image_dir):
            self.image_dir = image_dir
        else:
            # Support PyInstaller --onefile (images bundled inside .exe)
            if getattr(sys, 'frozen', False):
                # Running as compiled .exe
                base_dir = sys._MEIPASS
            else:
                # Running as normal .py script
                base_dir = os.path.dirname(os.path.abspath(__file__))

            self.image_dir = os.path.join(base_dir, "images")
            if not os.path.isdir(self.image_dir):
                self.image_dir = base_dir
        try:
            self.root.state('zoomed')
        except Exception:
            try:
                self.root.attributes('-zoomed', True)
            except Exception:
                set_window_size(self.root, 1280, 780, 720, 520)
        self.current_frame = None
        self.comparison_records = []
        self.current_comparison_record = None
        self.experiment_counter = 0
        self.show_splash()

    def _switch(self, frame):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = frame
        frame.pack(fill="both", expand=True)

    def show_splash(self):
        self._switch(SplashFrame(self.root, self))

    def show_setup(self):
        self._switch(SetupFrame(self.root, self))

    def show_guide(self):
        guide = tk.Toplevel(self.root)
        guide.title("Rabbit Eye Theory and Practical")
        guide.configure(bg=C["bg"])
        set_window_size(guide, 760, 640, 520, 420, margin_x=60, margin_y=80)
        tk.Label(
            guide, text="Rabbit Eye Theory and Practical",
            font=("Segoe UI", 17, "bold"), bg=C["bg2"], fg=C["gold"],
            padx=16, pady=12,
        ).pack(fill="x")
        frame = tk.Frame(guide, bg=C["bg"])
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        text = tk.Text(
            frame, wrap="word", font=("Segoe UI", 10), bg=C["card"],
            fg=C["text"], relief="flat", padx=14, pady=12, spacing3=4,
        )
        bar = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=bar.set)
        bar.pack(side="right", fill="y")
        text.pack(side="left", fill="both", expand=True)
        text.insert("1.0", RABBIT_GUIDE.strip())
        text.configure(state="disabled")
        tk.Button(
            guide, text="Close", command=guide.destroy, font=("Segoe UI", 10, "bold"),
            bg=C["gold"], fg=C["bg3"], relief="flat", padx=20, pady=7,
        ).pack(pady=(0, 12))

    def start_experiment(self, drug, eye):
        self.experiment_counter += 1
        values = {
            (parameter, eye_kind): ""
            for parameter in ExperimentFrame.PARAMETERS
            for eye_kind in ("drug", "saline")
        }
        self.current_comparison_record = {
            "id": self.experiment_counter,
            "drug_name": drug,
            "drug_eye": eye,
            "control_eye": "left" if eye == "right" else "right",
            "values": values,
            "saved_at": None,
        }
        self.comparison_records.append(self.current_comparison_record)
        self._switch(ExperimentFrame(self.root, self, drug, eye))


def main():
    enable_high_dpi()
    root = tk.Tk()
    configure_application_display(root)
    image_dir = sys.argv[1] if len(sys.argv) > 1 else None
    RabbitEyeApp(root, image_dir=image_dir)
    root.mainloop()


if __name__ == "__main__":
    main()
