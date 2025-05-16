# logic/curves.py
import numpy as np
from logic.filters import apply_hp_filter, apply_lp_filter, FilterConfig

# Standard 1/3‑octave frequency list (Hz)
FREQUENCIES = np.array([
    20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160,
    200, 250, 315, 400, 500, 630, 800, 1000, 1250,
    1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000,
    10000, 12500, 16000, 20000
])

# Default (predefined) house curve in dB
_DEFAULT_HOUSE_CURVE = np.array([
    24.0, 22.0, 20.0, 16.0, 11.0, 8.0, 6.0, 4.0, 3.0, 1.5,
    0.5,  0.0, -1.0, -2.0, -2.3, -2.5, -2.5, -3.0, -3.3, -3.6,
    -4.0, -4.5, -5.0, -5.5, -6.0, -6.8, -7.5, -8.0, -8.8, -9.5,
    -10.0
])

# Collection of available house curves
HOUSE_CURVES = {
    "House Curve": _DEFAULT_HOUSE_CURVE.copy()
}

# User‑editable custom curves
CUSTOM_CURVES = {
    "Custom1": np.zeros_like(FREQUENCIES, dtype=float),
    "Custom2": np.zeros_like(FREQUENCIES, dtype=float),
    "Custom3": np.zeros_like(FREQUENCIES, dtype=float)
}

# Currently selected house curve name
_selected_curve_name = "House Curve"


def get_selected_house_curve_name() -> str:
    """
    Return the name of the currently active house curve.
    """
    return _selected_curve_name


def set_selected_house_curve(name: str):
    """
    Set the active house curve by name. Must exist in HOUSE_CURVES or CUSTOM_CURVES.
    """
    global _selected_curve_name
    if name in HOUSE_CURVES or name in CUSTOM_CURVES:
        _selected_curve_name = name
    else:
        raise ValueError(f"House curve '{name}' not found")


def get_selected_house_curve() -> np.ndarray:
    """
    Return the dB array of the currently selected house curve.
    """
    if _selected_curve_name in HOUSE_CURVES:
        return HOUSE_CURVES[_selected_curve_name]
    return CUSTOM_CURVES[_selected_curve_name]


def reset_custom_curves():
    """
    Reset all custom curves back to 0 dB at every frequency.
    """
    for key, arr in CUSTOM_CURVES.items():
        arr.fill(0.0)


def update_custom_curve(idx: int, name: str, value: float):
    """
    Update one frequency bin of a custom curve.

    idx: index into FREQUENCIES
    name: one of the keys in CUSTOM_CURVES
    value: new dB magnitude
    """
    if name not in CUSTOM_CURVES:
        raise ValueError(f"Custom curve '{name}' not found")
    CUSTOM_CURVES[name][idx] = value


def load_custom_curve(name: str):
    """
    Copy the currently active house curve into the custom curve named 'name'.
    """
    if name not in CUSTOM_CURVES:
        raise ValueError(f"Custom curve '{name}' not found")
    CUSTOM_CURVES[name] = get_selected_house_curve().copy()


def generate_target_curve(hp_cfg: FilterConfig, lp_cfg: FilterConfig) -> np.ndarray:
    """
    Generate the target curve by applying high‑pass then low‑pass to the
    active house curve.

    hp_cfg or lp_cfg with filter_type 'None' will skip that stage.
    """
    # start from currently selected house curve
    curve = get_selected_house_curve().copy()
    # high‑pass
    if hp_cfg.filter_type != 'None':
        curve = apply_hp_filter(
            curve,
            FREQUENCIES,
            hp_cfg.cutoff,
            hp_cfg.filter_type,
            hp_cfg.slope
        )
    # low‑pass
    if lp_cfg.filter_type != 'None':
        curve = apply_lp_filter(
            curve,
            FREQUENCIES,
            lp_cfg.cutoff,
            lp_cfg.filter_type,
            lp_cfg.slope
        )
    return curve
