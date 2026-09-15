"""Entry point for the combined MAMC Pharmacology CAL application."""

import importlib
from pathlib import Path
import sys

from ui.display import enable_high_dpi

enable_high_dpi()

import tkinter as tk
from ui.display import configure_application_display
from ui.experiment_app import ExperimentApp


def application_resource_root():
    """Return the source or PyInstaller resource directory."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def run_smoke_test():
    """Verify packaged modules and data without creating a visible window."""
    module_names = (
        "experiments.dog_bp",
        "experiments.dog_bp_exam",
        "experiments.dog_bp_model",
        "experiments.bioassay",
        "experiments.frog_rectus",
        "experiments.quantitative_practicals",
        "experiments.rabbit_eye_practical",
        "experiments.combined_exams",
        "integrated_modules.frog_rectus.main",
    )
    for module_name in module_names:
        importlib.import_module(module_name)

    required_assets = (
        ("assets", "mamc_logo.png"),
        ("assets", "rabbit_eye", "Normal_pupil.png"),
        ("assets", "rabbit_eye", "Miosis.png"),
        ("assets", "rabbit_eye", "Mydriasis.png"),
    )
    resource_root = application_resource_root()
    missing = [
        str(resource_root.joinpath(*parts))
        for parts in required_assets
        if not resource_root.joinpath(*parts).is_file()
    ]
    if missing:
        raise FileNotFoundError("Missing packaged assets: " + ", ".join(missing))

    # Exercise the scientific model once so NumPy and the dose-response code
    # are checked inside the frozen application as well as merely imported.
    import numpy as np
    from experiments.dog_bp_model import simulate_response

    response = simulate_response(
        "Epinephrine", 2.0, np.linspace(0.0, 45.0, 181)
    )
    trace_names = ("sbp", "dbp", "map", "hr")
    if any(
        trace_name not in response or len(response[trace_name]) != 181
        for trace_name in trace_names
    ):
        raise RuntimeError("Dog BP packaged-model smoke test returned invalid data.")
    return 0


def run_frog_rectus():
    """Start the advanced Qt simulator from this executable."""
    from integrated_modules.frog_rectus.main import main as frog_main

    return frog_main([sys.argv[0]])


def run_portal():
    root = tk.Tk()
    configure_application_display(root)
    ExperimentApp(root)
    root.mainloop()
    return 0


def main():
    if "--smoke-test" in sys.argv[1:]:
        return run_smoke_test()
    if "--frog-rectus" in sys.argv[1:]:
        return run_frog_rectus()
    return run_portal()


if __name__ == "__main__":
    raise SystemExit(main())
