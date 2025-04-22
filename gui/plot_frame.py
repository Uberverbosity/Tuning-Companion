# gui/plot_frame.py
import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.interpolate import interp1d

class PlotFrame(tk.Frame):
    """
    PlotFrame displays the house curve and channel target curves.
    """
    def __init__(self, parent, frequencies, house_curve, channel_colors):
        super().__init__(parent)
        self.frequencies = frequencies
        self.house_curve = house_curve
        self.channel_colors = channel_colors
        self.channel_curves = {}  # idx -> (name, curve array)

        # Set up matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Initial plot
        self._draw_plot()

    def update_channel_curve(self, idx, name, curve):
        """Store and redraw the target curve for one channel."""
        if curve is not None:
            arr = np.asarray(curve).flatten()
            if arr.shape != self.frequencies.shape:
                arr = np.resize(arr, self.frequencies.shape)
            self.channel_curves[idx] = (name, arr)
        else:
            self.channel_curves.pop(idx, None)
        self._draw_plot()

    def update_channel_name(self, idx, name):
        """Update the name of an existing channel curve and redraw."""
        if idx in self.channel_curves:
            _, curve = self.channel_curves[idx]
            self.channel_curves[idx] = (name, curve)
            self._draw_plot()

    def clear_channel(self, idx):
        """Remove a channel curve and redraw."""
        self.channel_curves.pop(idx, None)
        self._draw_plot()

    def _draw_plot(self):
        """
        Draw the house curve and each channel curve as smooth dashed lines.
        """
        self.ax.cla()

        # Configure axes
        self.ax.set_ylim(-20, 30)
        self.ax.set_xscale('log')
        self.ax.set_xlim(self.frequencies[0], self.frequencies[-1])
        self.ax.set_xticks([20, 100, 1000, 10000, 20000])
        self.ax.set_xticklabels(["20 Hz", "100 Hz", "1 kHz", "10 kHz", "20 kHz"])
        self.ax.grid(True, which='both', linestyle='--', linewidth=0.5)

        # Plot house curve
        self.ax.plot(
            self.frequencies,
            self.house_curve,
            label="House Curve",
            color='black',
            linewidth=2
        )

        # Plot each channel
        for idx, (name, curve) in sorted(self.channel_curves.items()):
            try:
                interp_fn = interp1d(
                    self.frequencies,
                    curve,
                    kind='cubic',
                    bounds_error=False,
                    fill_value='extrapolate'
                )
                freq_smooth = np.logspace(
                    np.log10(self.frequencies[0]),
                    np.log10(self.frequencies[-1]),
                    num=200
                )
                y_smooth = interp_fn(freq_smooth)
            except Exception:
                freq_smooth = self.frequencies
                y_smooth = curve

            color = self.channel_colors[idx % len(self.channel_colors)]
            self.ax.plot(
                freq_smooth,
                y_smooth,
                label=name,
                color=color,
                linestyle='--'
            )

        # Legend top-right
        self.ax.legend(loc='upper right')
        self.canvas.draw()
