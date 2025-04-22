# gui/main_window.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from gui.plot_frame import PlotFrame
from logic.curves import FREQUENCIES, HOUSE_CURVE, generate_target_curve
from logic.filters import FilterConfig, FILTER_TYPES

class TuningCompanionApp(tk.Tk):
    """Main application window for tuning companion GUI."""
    def __init__(self):
        super().__init__()
        self.title("Tuning Companion")
        # Make the window taller
        self.geometry("1000x700")
        self.resizable(True, True)

        # Colors for channel curves matching list order
        self.channel_colors = ['red', 'orange', 'green', 'blue', 'purple']
        # Storage for channel control variables and startup defaults
        self.channel_controls = []
        self._startup_defaults = [
            ("None", 0),
            ("Linkwitz-Riley", 45),
            ("Linkwitz-Riley", 90),
            ("Linkwitz-Riley", 350),
            ("Linkwitz-Riley", 3500)
        ]

        # Alert banner variable
        self.alert_var = tk.StringVar()

        self._build_ui()

    def _build_ui(self):
        # Plot frame with extra bottom padding
        self.plot_frame = PlotFrame(self, FREQUENCIES, HOUSE_CURVE, self.channel_colors)
        self.plot_frame.pack(fill="both", expand=True, pady=(0, 20))

        # Controls frame below plot
        self.controls_frame = tk.Frame(self)
        self.controls_frame.pack(side="bottom", anchor="w", padx=5, pady=5)

        # Alert row (row 0)
        self.alert_label = tk.Label(
            self.controls_frame,
            textvariable=self.alert_var,
            fg="red",
            bg=self.controls_frame.cget('bg'),
            anchor="w"
        )
        self.alert_label.grid(row=0, column=0, columnspan=9, sticky="we", pady=(0,5))

        # Header row (row 1)
        headers = ["Enable", "Name", "HP Filter", "dB/oct", "HP Freq",
                   "LP Filter", "dB/oct", "LP Freq", "Output"]
        for col, txt in enumerate(headers):
            ttk.Label(self.controls_frame, text=txt).grid(row=1, column=col, padx=2, pady=2)

        # Channel rows start at row 2
        for idx in range(5):
            self._add_channel_row(idx, start_row=2)

        # Bottom controls at row 7
        self.folder_label = ttk.Label(self.controls_frame, text="Output Folder: Not set")
        self.folder_label.grid(row=7, column=0, columnspan=3, sticky="w")
        ttk.Button(self.controls_frame, text="Set Output Folder",
                   command=self._set_output_folder).grid(row=7, column=3, sticky="w")
        ttk.Button(self.controls_frame, text="Reset", 
                   command=self._reset_defaults, width=12).grid(row=7, column=6, sticky="w")
        ttk.Button(self.controls_frame, text="Exit", 
                   command=self.quit, width=12).grid(row=7, column=7, sticky="w")
        ttk.Button(self.controls_frame, text="Output All", 
                   command=self._output_all, width=12).grid(row=7, column=8, sticky="w")

        # Initial draw and alert check
        for i in range(5):
            self._update_curve(i)
        self._check_all_alerts()

    def _set_output_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.output_folder = path
            self.folder_label.config(text=f"Output Folder: {path}")

    def _output_all(self):
        for i in range(len(self.channel_controls)):
            self._output_single(i)

    def _output_single(self, idx):
        name = self.channel_controls[idx]['name'].get()
        print(f"Exporting target curve for {name}")

    def _add_channel_row(self, idx, start_row):
        row = start_row + idx
        ctrl = {}
        hp_def, hp_freq_def = self._startup_defaults[idx]
        lp_def, lp_freq_def = (
            self._startup_defaults[idx+1] if idx < 4 else ("None", 20000)
        )

        # Control variables
        ctrl['enabled']  = tk.BooleanVar(value=True)
        ctrl['name']     = tk.StringVar(value=f"Channel {idx+1}")
        ctrl['hp_type']  = tk.StringVar(value=hp_def)
        ctrl['hp_slope'] = tk.StringVar(value="24")
        ctrl['hp_freq']  = tk.StringVar(value=str(hp_freq_def))
        ctrl['lp_type']  = tk.StringVar(value=lp_def)
        ctrl['lp_slope'] = tk.StringVar(value="24")
        ctrl['lp_freq']  = tk.StringVar(value=str(lp_freq_def))

        # Widgets
        ttk.Checkbutton(
            self.controls_frame,
            variable=ctrl['enabled'],
            command=lambda i=idx: self._update_curve(i)
        ).grid(row=row, column=0)

        ent = ttk.Entry(self.controls_frame, textvariable=ctrl['name'], width=10)
        ent.grid(row=row, column=1)
        ent.bind("<Return>", lambda e,i=idx: (self._on_name_change(i), self.focus_set()))

        # HP controls
        opt_hp = ttk.OptionMenu(
            self.controls_frame,
            ctrl['hp_type'],
            ctrl['hp_type'].get(),
            *FILTER_TYPES,
            command=lambda _: self._on_filter_change(idx)
        )
        opt_hp.config(width=18)
        opt_hp.grid(row=row, column=2)

        opt_hs = ttk.OptionMenu(
            self.controls_frame,
            ctrl['hp_slope'],
            ctrl['hp_slope'].get(),
            "12","24","36",
            command=lambda _: self._on_filter_change(idx)
        )
        opt_hs.config(width=5)
        opt_hs.grid(row=row, column=3)

        ent_hf = ttk.Entry(self.controls_frame, textvariable=ctrl['hp_freq'], width=6)
        ent_hf.grid(row=row, column=4)
        ent_hf.bind("<Return>", lambda e,i=idx: (self._on_filter_change(i), self.focus_set()))

        # LP controls
        opt_lp = ttk.OptionMenu(
            self.controls_frame,
            ctrl['lp_type'],
            ctrl['lp_type'].get(),
            *FILTER_TYPES,
            command=lambda _: self._on_filter_change(idx)
        )
        opt_lp.config(width=18)
        opt_lp.grid(row=row, column=5)

        opt_ls = ttk.OptionMenu(
            self.controls_frame,
            ctrl['lp_slope'],
            ctrl['lp_slope'].get(),
            "12","24","36",
            command=lambda _: self._on_filter_change(idx)
        )
        opt_ls.config(width=5)
        opt_ls.grid(row=row, column=6)

        ent_lf = ttk.Entry(self.controls_frame, textvariable=ctrl['lp_freq'], width=6)
        ent_lf.grid(row=row, column=7)
        ent_lf.bind("<Return>", lambda e,i=idx: (self._on_filter_change(i), self.focus_set()))

        ttk.Button(
            self.controls_frame,
            text="Output Target",
            command=lambda i=idx: self._output_single(i)
        ).grid(row=row, column=8)

        # Store for enabling/disabling
        ctrl['hp_slope_w'] = opt_hs
        ctrl['hp_freq_w']  = ent_hf
        ctrl['lp_slope_w'] = opt_ls
        ctrl['lp_freq_w']  = ent_lf

        self.channel_controls.append(ctrl)
        # Initial disable based on filter type
        self._on_filter_change(idx)

    def _on_name_change(self, idx):
        name = self.channel_controls[idx]['name'].get()
        self.plot_frame.update_channel_name(idx, name)
        self._check_all_alerts()

    def _on_filter_change(self, idx):
        ctrl = self.channel_controls[idx]
        # enforce LR slope
        if ctrl['hp_type'].get() == 'Linkwitz-Riley' and ctrl['hp_slope'].get() not in ['12','24','36']:
            ctrl['hp_slope'].set('24')
        if ctrl['lp_type'].get() == 'Linkwitz-Riley' and ctrl['lp_slope'].get() not in ['12','24','36']:
            ctrl['lp_slope'].set('24')
        # disable/enable widgets
        state_hp = 'disabled' if ctrl['hp_type'].get()=='None' else 'normal'
        ctrl['hp_slope_w'].config(state=state_hp)
        ctrl['hp_freq_w'].config(state=state_hp)
        state_lp = 'disabled' if ctrl['lp_type'].get()=='None' else 'normal'
        ctrl['lp_slope_w'].config(state=state_lp)
        ctrl['lp_freq_w'].config(state=state_lp)
        self._update_curve(idx)

    def _reset_defaults(self):
        for idx, ctrl in enumerate(self.channel_controls):
            hp_def, hp_freq_def = self._startup_defaults[idx]
            lp_def, lp_freq_def = (self._startup_defaults[idx+1]
                                   if idx < 4 else ("None",20000))
            ctrl['enabled'].set(True)
            ctrl['name'].set(f"Channel {idx+1}")
            ctrl['hp_type'].set(hp_def)
            ctrl['hp_slope'].set('24')
            ctrl['hp_freq'].set(str(hp_freq_def))
            ctrl['lp_type'].set(lp_def)
            ctrl['lp_slope'].set('24')
            ctrl['lp_freq'].set(str(lp_freq_def))
            self._on_filter_change(idx)
            self._update_curve(idx)
        self._check_all_alerts()

    def _update_curve(self, idx):
        ctrl = self.channel_controls[idx]
        if not ctrl['enabled'].get():
            self.plot_frame.clear_channel(idx)
        else:
            fc1 = FilterConfig(ctrl['hp_type'].get(), 
                               int(ctrl['hp_slope'].get()), 
                               float(ctrl['hp_freq'].get()))
            fc2 = FilterConfig(ctrl['lp_type'].get(), 
                               int(ctrl['lp_slope'].get()), 
                               float(ctrl['lp_freq'].get()))
            curve = generate_target_curve(fc1, fc2)
            self.plot_frame.update_channel_curve(idx, 
                                                 ctrl['name'].get(), 
                                                 curve)
        self._check_all_alerts()

    def _check_all_alerts(self):
        msgs = []
        for i in range(len(self.channel_controls)-1):
            c1 = self.channel_controls[i]
            c2 = self.channel_controls[i+1]
            if (c1['enabled'].get() and c2['enabled'].get()
               and c1['lp_type'].get()!='None' and c2['hp_type'].get()!='None'):
                try:
                    if (float(c1['lp_freq'].get()) != float(c2['hp_freq'].get())
                        or c1['lp_type'].get()!=c2['hp_type'].get()
                        or c1['lp_slope'].get()!=c2['hp_slope'].get()):
                        msgs.append(f"LP of {c1['name'].get()} != HP of {c2['name'].get()}")
                except ValueError:
                    msgs.append(f"Invalid freq on {c1['name'].get()} or {c2['name'].get()}")
        if msgs:
            self.alert_var.set("⚠️ Click to view mismatches")
            self.alert_label.config(bg='yellow', fg='red')
            self.alert_label.bind("<Button-1>", 
                lambda e: messagebox.showinfo("Alerts", "\n".join(msgs)))
        else:
            self.alert_var.set("")
            self.alert_label.config(bg=self.controls_frame.cget('bg'))

if __name__ == '__main__':
    app = TuningCompanionApp()
    app.mainloop()
