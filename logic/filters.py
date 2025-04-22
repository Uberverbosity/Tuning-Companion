# logic/filters.py
import numpy as np
from scipy import signal

class FilterConfig:
    """
    Simple container for filter configuration.
    Attributes:
      filter_type: str, one of 'None', 'Butterworth', 'Linkwitz-Riley', 'Bessel', 'Chebyshev'
      slope: int, filter slope in dB/oct.
      cutoff: float, cutoff frequency in Hz.
    """
    def __init__(self, filter_type: str, slope: int, cutoff: float):
        self.filter_type = filter_type
        self.slope = slope
        self.cutoff = cutoff

# Central filter list used by UI dropdowns and filter application logic
FILTER_TYPES = ['None', 'Butterworth', 'Linkwitz-Riley', 'Bessel', 'Chebyshev']


def butterworth_lp_mag(f: np.ndarray, f_c: float, slope: int) -> np.ndarray:
    """
    Butterworth low-pass magnitude. Order n = slope/6 (6 dB/oct per order).
    |H(jw)| = 1 / sqrt(1 + (f/f_c)^(2n))
    """
    n = max(1, slope // 6)
    H = 1.0 / np.sqrt(1 + (f / f_c)**(2 * n))
    return H


def butterworth_hp_mag(f: np.ndarray, f_c: float, slope: int) -> np.ndarray:
    """
    Butterworth high-pass magnitude. Order n = slope/6.
    |H(jw)| = 1 / sqrt(1 + (f_c/f)^(2n))
    """
    n = max(1, slope // 6)
    H = 1.0 / np.sqrt(1 + (f_c / f)**(2 * n))
    return H


def linkwitz_riley_lp_mag(f: np.ndarray, f_c: float, slope: int) -> np.ndarray:
    """
    Linkwitz-Riley low-pass: two cascaded Butterworth filters of order n = slope/12.
    Magnitude = (H_bw)^2
    """
    n = max(1, slope // 12)
    H_bw = butterworth_lp_mag(f, f_c, n * 6)  # slope per stage = 6*n dB/oct
    LR = H_bw**2
    return LR


def linkwitz_riley_hp_mag(f: np.ndarray, f_c: float, slope: int) -> np.ndarray:
    """
    Linkwitz-Riley high-pass: two cascaded Butterworth filters of order n = slope/12.
    Magnitude = (H_bw)^2
    """
    n = max(1, slope // 12)
    H_bw = butterworth_hp_mag(f, f_c, n * 6)
    LR = H_bw**2
    return LR


def bessel_mag(f: np.ndarray, f_c: float, slope: int, btype: str) -> np.ndarray:
    """
    Bessel filter magnitude, order = slope/6.
    """
    n = max(1, slope // 6)
    w, h = signal.freqs(*signal.bessel(n, 2 * np.pi * f_c, btype=btype, analog=True), worN=2 * np.pi * f)
    mag = np.abs(h)
    return mag


def chebyshev1_mag(f: np.ndarray, f_c: float, slope: int, btype: str, rp: float = 1.0) -> np.ndarray:
    """
    Chebyshev Type I filter magnitude, order = slope/6, ripple rp dB.
    """
    n = max(1, slope // 6)
    w, h = signal.freqs(*signal.cheby1(n, rp, 2 * np.pi * f_c, btype=btype, analog=True), worN=2 * np.pi * f)
    mag = np.abs(h)
    return mag


def apply_hp_filter(curve_db: np.ndarray, freq: np.ndarray,
                    cutoff: float, filter_type: str, slope: int) -> np.ndarray:
    if filter_type == 'None' or cutoff <= 0:
        return curve_db

    if filter_type == 'Linkwitz-Riley':
        H = linkwitz_riley_hp_mag(freq, cutoff, slope)
    elif filter_type == 'Butterworth':
        H = butterworth_hp_mag(freq, cutoff, slope)
    elif filter_type == 'Bessel':
        H = bessel_mag(freq, cutoff, slope, 'high')
    elif filter_type == 'Chebyshev':
        H = chebyshev1_mag(freq, cutoff, slope, 'high')
    else:
        raise ValueError(f"Unknown filter type: {filter_type}")

    H_db = 20 * np.log10(H)
    result = curve_db + H_db
    return result


def apply_lp_filter(curve_db: np.ndarray, freq: np.ndarray,
                    cutoff: float, filter_type: str, slope: int) -> np.ndarray:
    if filter_type == 'None' or cutoff <= 0:
        return curve_db

    if filter_type == 'Linkwitz-Riley':
        H = linkwitz_riley_lp_mag(freq, cutoff, slope)
    elif filter_type == 'Butterworth':
        H = butterworth_lp_mag(freq, cutoff, slope)
    elif filter_type == 'Bessel':
        H = bessel_mag(freq, cutoff, slope, 'low')
    elif filter_type == 'Chebyshev':
        H = chebyshev1_mag(freq, cutoff, slope, 'low')
    else:
        raise ValueError(f"Unknown filter type: {filter_type}")

    H_db = 20 * np.log10(H)
    result = curve_db + H_db
    return result
