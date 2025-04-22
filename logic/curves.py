# logic/curves.py
import numpy as np
from logic.filters import apply_hp_filter, apply_lp_filter, FilterConfig

# Standard 1/3 octave frequency list
FREQUENCIES = np.array([
    20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160,
    200, 250, 315, 400, 500, 630, 800, 1000, 1250,
    1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000,
    10000, 12500, 16000, 20000
])

# Provided House Curve (dB)
HOUSE_CURVE = np.array([
    24.0, 22.0, 20.0, 16.0, 11.0, 8.0, 6.0, 4.0, 3.0, 1.5,
    0.5,  0.0, -1.0, -2.0, -2.3, -2.5, -2.5, -3.0, -3.3, -3.6,
    -4.0, -4.5, -5.0, -5.5, -6.0, -6.8, -7.5, -8.0, -8.8, -9.5,
    -10.0
])

def generate_target_curve(hp_cfg: FilterConfig, lp_cfg: FilterConfig) -> np.ndarray:
    """
    Generate the target curve by applying high‑pass, then low‑pass filters.
    hp_cfg or lp_cfg with filter_type 'None' will skip that stage.
    """
    curve = HOUSE_CURVE.copy()
    if hp_cfg.filter_type != 'None':
        curve = apply_hp_filter(
            curve,
            FREQUENCIES,
            hp_cfg.cutoff,
            hp_cfg.filter_type,
            hp_cfg.slope
        )
    if lp_cfg.filter_type != 'None':
        curve = apply_lp_filter(
            curve,
            FREQUENCIES,
            lp_cfg.cutoff,
            lp_cfg.filter_type,
            lp_cfg.slope
        )
    return curve
