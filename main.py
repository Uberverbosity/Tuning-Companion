import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import signal
import matplotlib.ticker as ticker

# Define the standard 1/3‑octave frequency list
frequencies = np.array([
    20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160,
    200, 250, 315, 400, 500, 630, 800, 1000, 1250,
    1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000,
    10000, 12500, 16000, 20000
])

# Provided House Curve amplitude values (in dB)
house_curve = np.array([
    24.0, 22.0, 20.0, 16.0, 11.0, 8.0, 6.0, 4.0, 3.0, 1.5,
    0.5,  0.0,  -1.0, -2.0, -2.3, -2.5, -2.5, -3.0, -3.3, -3.6,
    -4.0, -4.5, -5.0, -5.5, -6.0, -6.8, -7.5, -8.0, -8.8, -9.5,
    -10.0
])

# Define Filter Functions
def butterworth_lp_mag(f, f_c, n):
    """
    Compute the linear magnitude response of a low-pass Butterworth filter.
    |H(jω)| = 1 / √(1 + (f/f_c)^(2n))
    """
    return 1.0 / np.sqrt(1 + (f / f_c)**(2 * n))

def butterworth_hp_mag(f, f_c, n):
    """
    Compute the linear magnitude response of a high-pass Butterworth filter.
    |H(jω)| = 1 / √(1 + (f_c/f)^(2n))
    """
    return 1.0 / np.sqrt(1 + (f_c / f)**(2 * n))

def linkwitz_riley_lp_mag(f, f_c, n=2):
    """
    Compute the Linkwitz-Riley low-pass magnitude response by cascading two Butterworth filters.
    (Squared magnitude response)
    """
    H = butterworth_lp_mag(f, f_c, n)
    return H**2

def linkwitz_riley_hp_mag(f, f_c, n=2):
    """
    Compute the Linkwitz-Riley high-pass magnitude response by cascading two Butterworth filters.
    (Squared magnitude response)
    """
    H = butterworth_hp_mag(f, f_c, n)
    return H**2

def apply_filter(curve_db, freq, cutoff, filter_type='low', order=4):
    """
    Apply a filter to the House Curve (in dB) using the computed magnitude response.
    
    Parameters:
      curve_db: 1D numpy array representing the House Curve in dB.
      freq: Frequency array (Hz).
      cutoff: Cutoff frequency (Hz).
      filter_type: 'low' for low pass or 'high' for high pass.
      order: Filter order (default 4 corresponds to a Linkwitz-Riley 24 dB/octave response).
    
    Returns:
      The filtered curve (in dB).
    """
    # Use half the order (n) for the Butterworth stage (since cascading doubles the order)
    n = order // 2
    if filter_type == 'low':
        H = linkwitz_riley_lp_mag(freq, cutoff, n=n)
    elif filter_type == 'high':
        H = linkwitz_riley_hp_mag(freq, cutoff, n=n)
    else:
        raise ValueError("filter_type must be 'low' or 'high'")
    
    # Convert the linear magnitude response to dB
    H_db = 20 * np.log10(H)
    
    # For a flat curve, applying the filter is equivalent to adding H_db
    return curve_db + H_db

def apply_channel_filter(curve_db, freq, hp_cutoff=None, lp_cutoff=None, order=4):
    """
    Apply channel-specific filtering to the House Curve.
    Optionally apply a high-pass filter (if hp_cutoff is provided) and/or a low-pass filter (if lp_cutoff is provided).
    """
    filtered = curve_db.copy()
    if hp_cutoff is not None:
        filtered = apply_filter(filtered, freq, hp_cutoff, filter_type='high', order=order)
    if lp_cutoff is not None:
        filtered = apply_filter(filtered, freq, lp_cutoff, filter_type='low', order=order)
    return filtered

# Create Channel Targets
# -----------------------------------------------------------------------------
# Define channel-XO's
channels = {
    "Sub2":    {"hp": None,    "lp": 60},
    "Sub1":    {"hp": 60,      "lp": 150},
    "Midbass": {"hp": 150,     "lp": 500},
    "Midrange":{"hp": 500,     "lp": 3000},
    "Tweeter": {"hp": 3000,    "lp": None}
}

# Calculate target curves
channel_curves = {}
for ch_name, params in channels.items():
    ch_curve = apply_channel_filter(
        house_curve, 
        frequencies, 
        hp_cutoff=params.get("hp"), 
        lp_cutoff=params.get("lp"),
        order=4
    )
    channel_curves[ch_name] = ch_curve

# -----------------------------------------------------------------------------
# Step 4: Plotting
# -----------------------------------------------------------------------------
plt.figure(figsize=(12, 8))

# Plot the original House Curve (provided amplitudes)
plt.semilogx(frequencies, house_curve, label='House Curve', color='black', linewidth=2)

# Define distinct colors for each channel
channel_colors = {
    "Sub2": "blue",
    "Sub1": "cyan",
    "Midbass": "red",
    "Midrange": "green",
    "Tweeter": "magenta"
}

# Plot each channel's target curve
for ch_name, ch_curve in channel_curves.items():
    plt.semilogx(frequencies, ch_curve, label=f'{ch_name} Target', color=channel_colors.get(ch_name), linestyle='--')

plt.xlabel("Frequency (Hz)")
plt.ylabel("Amplitude (dB)")
plt.title("House Curve and Channel Target Curves")
plt.xlim([20, 20000])
plt.ylim([-12, 26])

# Set fixed major ticks and custom labels (to mimic Excel)
ax = plt.gca()
major_ticks = [20, 100, 1000, 10000, 20000]
ax.set_xticks(major_ticks)
ax.set_xticklabels(["20 Hz", "100 Hz", "1 kHz", "10 kHz", "20 kHz"])
ax.xaxis.set_minor_locator(ticker.LogLocator(subs='all', numticks=20))
ax.xaxis.set_minor_formatter(ticker.NullFormatter())
plt.grid(True, which='both', linestyle='--', linewidth=0.5)
plt.legend()
plt.show()

# -----------------------------------------------------------------------------
# Step 5: Export Functionality
# -----------------------------------------------------------------------------
def export_to_rew(frequencies, curve, filename):
    """
    Export the given curve data to a CSV file in REW format (two columns: frequency and amplitude)
    with no header or index.
    """
    export_data = pd.DataFrame({
        'Frequency': frequencies,
        'Amplitude': curve
    })
    export_data.to_csv(filename, header=False, index=False)
    print(f"Exported {filename}")

# Export the House Curve in REW format
export_to_rew(frequencies, house_curve, 'house_curve_rew.csv')

# Export each channel's target curve in REW format
for ch_name, ch_curve in channel_curves.items():
    filename = f'{ch_name.lower()}_target_rew.csv'
    export_to_rew(frequencies, ch_curve, filename)
