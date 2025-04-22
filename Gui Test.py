import tkinter as tk
from tkinter import filedialog, ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import pandas as pd
import matplotlib.ticker as ticker

# Define standard 1/3‑octave frequency list
frequencies = np.array([
    20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160,
    200, 250, 315, 400, 500, 630, 800, 1000, 1250,
    1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000,
    10000, 12500, 16000, 20000
])

# Provided House Curve (dB)
house_curve = np.array([
    24.0, 22.0, 20.0, 16.0, 11.0, 8.0, 6.0, 4.0, 3.0, 1.5,
    0.5,  0.0, -1.0, -2.0, -2.3, -2.5, -2.5, -3.0, -3.3, -3.6,
    -4.0, -4.5, -5.0, -5.5, -6.0, -6.8, -7.5, -8.0, -8.8, -9.5,
    -10.0
])

# Channel names and filter options
channel_names = ["Sub2", "Sub1", "Midbass", "Midrange", "Tweeter"]
filter_types   = ["Butterworth", "Bessel", "Chebyshev", "Linkwitz-Riley"]
filter_slopes  = [6, 12, 18, 24, 30, 36, 42]  # LR will be restricted later

class TuningCompanionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tuning Companion")
        self.output_folder = None

        # store references to each channel's widgets
        self.settings = { ch: {"HP":{}, "LP":{}} for ch in channel_names }

        self.create_widgets()
        self.draw_chart()

    def create_widgets(self):
        # Top: chart
        self.chart_frame = tk.Frame(self.root)
        self.chart_frame.pack(fill=tk.BOTH, expand=True)

        # Middle: controls
        self.control_frame = tk.Frame(self.root)
        self.control_frame.pack(fill=tk.X)

        for ch in channel_names:
            row = tk.LabelFrame(self.control_frame, text=ch)
            row.pack(fill=tk.X, padx=5, pady=2)

            for stage in ("HP","LP"):
                tk.Label(row, text=stage).pack(side=tk.LEFT, padx=(10,0))

                #--- use ttk.Combobox, not tk.Combobox
                type_box = ttk.Combobox(row, values=filter_types, width=15, state="readonly")
                type_box.set(filter_types[0])
                type_box.pack(side=tk.LEFT, padx=5)

                slope_box = ttk.Combobox(row, values=filter_slopes, width=5, state="readonly")
                slope_box.set(24)
                slope_box.pack(side=tk.LEFT, padx=5)

                #--- use ttk.Entry, not tk.Entry
                freq_entry = ttk.Entry(row, width=7)
                freq_entry.insert(0, "1000")
                freq_entry.pack(side=tk.LEFT, padx=5)

                self.settings[ch][stage] = {
                    "type":  type_box,
                    "slope": slope_box,
                    "freq":  freq_entry
                }

        # Bottom: output controls
        self.bottom_frame = tk.Frame(self.root)
        self.bottom_frame.pack(fill=tk.X, pady=10)

        self.folder_label = tk.Label(self.bottom_frame, text="Output Folder: Not set")
        self.folder_label.pack(side=tk.LEFT, padx=10)

        ttk.Button(self.bottom_frame, text="Set Output Folder", command=self.set_output_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.bottom_frame, text="Output All", command=self.output_all).pack(side=tk.RIGHT, padx=5)

    def set_output_folder(self):
        path = filedialog.askdirectory(title="Select Output Folder")
        if path:
            self.output_folder = path
            self.folder_label.config(text=f"Output Folder: {path}")

    def output_all(self):
        # Placeholder for export logic
        print("Export All clicked. Output directory:", self.output_folder)

    def draw_chart(self):
        # Clear previous chart (if re-drawing)
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        fig, ax = plt.subplots(figsize=(8,4))
        ax.semilogx(frequencies, house_curve, label="House Curve", color="black", linewidth=2)
        ax.set_xlim(20,20000);  ax.set_ylim(-12,26)
        ax.set_xticks([20,100,1000,10000,20000])
        ax.set_xticklabels(["20 Hz","100 Hz","1 kHz","10 kHz","20 kHz"])
        ax.xaxis.set_minor_locator(ticker.LogLocator(subs='all'))
        ax.xaxis.set_minor_formatter(ticker.NullFormatter())
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)
        ax.set_title("Target Curves");  ax.set_xlabel("Frequency (Hz)");  ax.set_ylabel("Amplitude (dB)")
        ax.legend()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = TuningCompanionApp(root)
    root.mainloop()
