"""High-DPI display helpers for the MAMC CAL desktop application."""

import ctypes
import sys
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk


TEXT_MAGNIFICATION = 1.08
_dpi_awareness_requested = False


def _install_macos_colour_button():
    """Use a colour-capable Tk button on macOS when the optional helper exists.

    Apple's native Tk button ignores custom face colours on several Tk/macOS
    combinations.  The suite deliberately uses colour to distinguish actions,
    so a future macOS bundle installs ``tkmacosx`` and transparently receives a
    drop-in button that honours the existing background/foreground options.
    Source runs still fall back safely to the native button if it is absent.
    """
    if sys.platform != "darwin":
        return False
    try:
        from tkmacosx import Button as MacColourButton
    except ImportError:
        return False
    tk.Button = MacColourButton
    return True


MACOS_COLOUR_BUTTON_AVAILABLE = _install_macos_colour_button()


def _relative_luminance(widget, colour):
    red, green, blue = (component / 65535.0 for component in widget.winfo_rgb(colour))

    def linear(component):
        if component <= 0.03928:
            return component / 12.92
        return ((component + 0.055) / 1.055) ** 2.4

    return 0.2126 * linear(red) + 0.7152 * linear(green) + 0.0722 * linear(blue)


def _contrast_ratio(widget, foreground, background):
    lighter = max(
        _relative_luminance(widget, foreground),
        _relative_luminance(widget, background),
    )
    darker = min(
        _relative_luminance(widget, foreground),
        _relative_luminance(widget, background),
    )
    return (lighter + 0.05) / (darker + 0.05)


def _make_button_legible(button):
    """Repair low-contrast action labels without changing their action colour."""
    if not isinstance(button, tk.Button):
        return
    try:
        background = button.cget("background")
        foreground = button.cget("foreground")
        # A native Aqua button can ignore its configured face colour.  When the
        # optional colour widget is missing, dark text remains readable against
        # the native light face instead of disappearing as white-on-white.
        if sys.platform == "darwin" and not MACOS_COLOUR_BUTTON_AVAILABLE:
            replacement = "#000000"
        elif _contrast_ratio(button, foreground, background) < 4.5:
            candidates = ("#ffffff", "#000000")
            replacement = max(
                candidates,
                key=lambda colour: _contrast_ratio(button, colour, background),
            )
        else:
            replacement = foreground
        if replacement != foreground:
            button.configure(foreground=replacement)

        active_background = button.cget("activebackground")
        active_foreground = button.cget("activeforeground")
        if sys.platform == "darwin" and not MACOS_COLOUR_BUTTON_AVAILABLE:
            active_replacement = "#000000"
        elif _contrast_ratio(button, active_foreground, active_background) < 4.5:
            active_replacement = max(
                ("#ffffff", "#000000"),
                key=lambda colour: _contrast_ratio(
                    button, colour, active_background
                ),
            )
        else:
            active_replacement = active_foreground
        if active_replacement != active_foreground:
            button.configure(activeforeground=active_replacement)
    except (KeyError, tk.TclError, ValueError):
        return


def _install_button_contrast_guard(root):
    if getattr(root, "_mamc_button_contrast_guard", False):
        return
    root._mamc_button_contrast_guard = True

    def on_widget_mapped(event):
        _make_button_legible(event.widget)

    root.bind_all("<Map>", on_widget_mapped, add="+")


def enable_high_dpi():
    """Ask Windows for native per-monitor rendering before a Tk window exists."""
    global _dpi_awareness_requested
    if _dpi_awareness_requested or sys.platform != "win32":
        return
    _dpi_awareness_requested = True

    try:
        user32 = ctypes.windll.user32
        user32.SetProcessDpiAwarenessContext.argtypes = [ctypes.c_void_p]
        user32.SetProcessDpiAwarenessContext.restype = ctypes.c_bool
        if user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
            return
    except (AttributeError, OSError, ValueError):
        pass

    try:
        # PROCESS_PER_MONITOR_DPI_AWARE
        if ctypes.windll.shcore.SetProcessDpiAwareness(2) in (0, -2147024891):
            return
    except (AttributeError, OSError):
        pass

    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        pass


def configure_application_display(root):
    """Configure sharp fonts, slightly larger text, and readable ttk controls."""
    if getattr(root, "_mamc_display_configured", False):
        return
    root._mamc_display_configured = True
    root.update_idletasks()
    try:
        dpi = float(root.winfo_fpixels("1i"))
    except Exception:
        dpi = 96.0
    dpi = min(max(dpi, 96.0), 288.0)
    monitor_scale = dpi / 96.0
    root._mamc_monitor_scale = monitor_scale

    try:
        logical_width = root.winfo_screenwidth() / monitor_scale
        logical_height = root.winfo_screenheight() / monitor_scale
    except Exception:
        logical_width, logical_height = 1366.0, 768.0
    # Low-DPI projectors and large desktop displays otherwise make 10-point
    # controls look disproportionately small.  High-DPI laptops already receive
    # physical scaling from the operating system and do not need this boost.
    presentation_scale = (
        1.12
        if monitor_scale <= 1.25 and logical_width >= 1800 and logical_height >= 900
        else 1.0
    )
    root._mamc_presentation_scale = presentation_scale

    # Tk font sizes use points. This preserves the physical font size at the
    # monitor DPI and adds a small readability increase requested for teaching.
    root.tk.call(
        "tk", "scaling",
        (dpi / 72.0) * TEXT_MAGNIFICATION * presentation_scale,
    )

    if sys.platform == "win32":
        ui_family, fixed_family = "Segoe UI", "Consolas"
    elif sys.platform == "darwin":
        ui_family, fixed_family = "Helvetica Neue", "Menlo"
    else:
        ui_family, fixed_family = "DejaVu Sans", "DejaVu Sans Mono"

    font_settings = {
        "TkDefaultFont": (ui_family, 10, "normal"),
        "TkTextFont": (ui_family, 10, "normal"),
        "TkMenuFont": (ui_family, 10, "normal"),
        "TkHeadingFont": (ui_family, 10, "bold"),
        "TkCaptionFont": (ui_family, 10, "bold"),
        "TkSmallCaptionFont": (ui_family, 9, "normal"),
        "TkIconFont": (ui_family, 10, "normal"),
        "TkFixedFont": (fixed_family, 10, "normal"),
    }
    for name, (family, size, weight) in font_settings.items():
        try:
            named_font = tkfont.nametofont(name, root=root)
            named_font.configure(family=family, size=size, weight=weight)
        except Exception:
            continue

    root.option_add("*Font", "TkDefaultFont")
    root.option_add("*Menu.Font", "TkMenuFont")
    root.option_add("*Button.padX", 8)
    root.option_add("*Button.padY", 5)
    root.option_add("*Button.takeFocus", 1)
    _install_button_contrast_guard(root)

    style = ttk.Style(root)
    # The portable themes honour explicit foreground/background colours; Aqua
    # does not.  This also gives a readable fallback if tkmacosx is unavailable
    # in a source-only macOS environment.
    if sys.platform == "darwin" and not MACOS_COLOUR_BUTTON_AVAILABLE:
        themes = style.theme_names()
        if "clam" in themes:
            style.theme_use("clam")

    style.configure(".", font=(ui_family, 10))
    style.configure(
        "Treeview", font=(ui_family, 10),
        rowheight=max(
            27, int(round(27 * monitor_scale * presentation_scale))
        ),
    )
    style.configure("Treeview.Heading", font=(ui_family, 10, "bold"))
    style.configure("TCombobox", font=(ui_family, 10), padding=(5, 4))
    style.configure("TButton", font=(ui_family, 10), padding=(9, 6))
    semantic_buttons = {
        "Primary.TButton": ("#1769aa", "#ffffff"),
        "Success.TButton": ("#237032", "#ffffff"),
        "Warning.TButton": ("#d68910", "#172b3a"),
        "Danger.TButton": ("#a13d2d", "#ffffff"),
        "Secondary.TButton": ("#607789", "#ffffff"),
    }
    for style_name, (background, foreground) in semantic_buttons.items():
        style.configure(
            style_name, background=background, foreground=foreground,
            font=(ui_family, 10, "bold"), padding=(10, 7),
        )
        style.map(
            style_name,
            background=[("active", background), ("pressed", background)],
            foreground=[("disabled", "#d7e1e8"), ("active", foreground)],
        )

    try:
        from matplotlib import rcParams
        rcParams.update({
            "font.family": ui_family,
            "font.size": 10.5,
            "axes.titlesize": 11.5,
            "axes.labelsize": 10.5,
            "xtick.labelsize": 9.5,
            "ytick.labelsize": 9.5,
            "legend.fontsize": 9.5,
        })
    except Exception:
        pass


def display_scale(widget):
    root = widget._root()
    return float(getattr(root, "_mamc_monitor_scale", 1.0))


def set_window_size(window, width, height, min_width=None, min_height=None,
                    margin_x=60, margin_y=80, center=True, expand_large=False):
    """Set a DPI-scaled window size while keeping it inside the current screen."""
    scale = display_scale(window)
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    width_floor = min(500, screen_width)
    height_floor = min(420, screen_height)
    available_width = min(
        screen_width,
        max(width_floor, screen_width - int(round(margin_x * scale))),
    )
    available_height = min(
        screen_height,
        max(height_floor, screen_height - int(round(margin_y * scale))),
    )
    target_width = min(int(round(width * scale)), available_width)
    target_height = min(int(round(height * scale)), available_height)
    if expand_large and screen_width >= 1500 and screen_height >= 850:
        target_width = min(
            available_width, max(target_width, int(available_width * 0.90))
        )
        target_height = min(
            available_height, max(target_height, int(available_height * 0.90))
        )

    if center:
        left = max(0, (screen_width - target_width) // 2)
        top = max(0, (screen_height - target_height) // 3)
        window.geometry(f"{target_width}x{target_height}+{left}+{top}")
    else:
        window.geometry(f"{target_width}x{target_height}")

    if min_width is not None and min_height is not None:
        scaled_min_width = min(int(round(min_width * scale)), target_width)
        scaled_min_height = min(int(round(min_height * scale)), target_height)
        window.minsize(scaled_min_width, scaled_min_height)
    return target_width, target_height
