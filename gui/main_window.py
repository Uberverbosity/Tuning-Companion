# gui/main_window.py (Full Regeneration without Logging)
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from typing import Any, Dict, List

from gui.plot_frame import PlotFrame
from logic.curves import (
    FREQUENCIES,
    get_selected_house_curve,
    get_selected_house_curve_name,
    generate_target_curve,
    FilterConfig,
    CUSTOM_CURVES,
    reset_custom_curves,
    set_selected_house_curve
)
from logic.filters import FILTER_TYPES

SETTINGS_FILE = "tuning_companion_settings.json"

class TuningCompanionApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Tuning Companion")
        self.geometry("1200x700")
        self.resizable(True, True)

        self.channel_colors = ['red', 'orange', 'green', 'blue', 'purple']
        self.channel_controls: List[Dict[str, Any]] = []
        self.output_folder: str = ""

        self._startup_defaults = [
            ("None", 0),
            ("Linkwitz-Riley", 45),
            ("Linkwitz-Riley", 90),
            ("Linkwitz-Riley", 350),
            ("Linkwitz-Riley", 3500)
        ]

        self.alert_var = tk.StringVar()
        self.alert_label = tk.Label(self, textvariable=self.alert_var, fg="red", bg="yellow", anchor="w")

        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        layout = tk.Frame(self)
        layout.pack(fill="both", expand=True)

        left = tk.Frame(layout)
        left.pack(side="left", fill="both", expand=True)

        right = tk.Frame(layout)
        right.pack(side="right", fill="y")

        self.plot_frame = PlotFrame(left, FREQUENCIES, get_selected_house_curve(), self.channel_colors)
        self.plot_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.controls_frame = tk.Frame(left)
        self.controls_frame.pack(fill="x")

        headers = ["Enable", "Name", "HP Filter", "dB/oct", "HP Freq", "LP Filter", "dB/oct", "LP Freq", "Output"]
        for col, txt in enumerate(headers):
            ttk.Label(self.controls_frame, text=txt).grid(row=0, column=col, padx=2, pady=2)

        for idx in range(5):
            self._add_channel_row(idx)

        self.folder_label = ttk.Label(self.controls_frame, text="Output Folder: Not set")
        self.folder_label.grid(row=6, column=0, columnspan=3, sticky="w")
        ttk.Button(self.controls_frame, text="Set Output Folder", command=self._set_output_folder).grid(row=6, column=3, sticky="w")
        ttk.Button(self.controls_frame, text="Reset", command=self._reset_defaults, width=12).grid(row=6, column=6, sticky="w")
        ttk.Button(self.controls_frame, text="Exit", command=self.quit, width=12).grid(row=6, column=7, sticky="w")
        ttk.Button(self.controls_frame, text="Output All", command=self._output_all, width=12).grid(row=6, column=8, sticky="w")

        self._build_house_curve_editor(right)

        for i in range(5):
            self._update_curve(i)
        self._check_all_alerts()

    def _reset_defaults(self):
        for idx, ctrl in enumerate(self.channel_controls):
            hp_def, hp_freq = self._startup_defaults[idx]
            lp_def, lp_freq = self._startup_defaults[idx + 1] if idx < 4 else ("None", 20000)
            ctrl['enabled'].set(True)
            ctrl['name'].set(f"Channel {idx + 1}")
            ctrl['hp_type'].set(hp_def)
            ctrl['hp_slope'].set("24")
            ctrl['hp_freq'].set(str(hp_freq))
            ctrl['lp_type'].set(lp_def)
            ctrl['lp_slope'].set("24")
            ctrl['lp_freq'].set(str(lp_freq))
            self._on_filter_change(idx)
        for i in range(5):
            self._update_curve(i)
        self._check_all_alerts()

    def _add_channel_row(self, idx: int) -> None:
        row = idx + 1
        ctrl: Dict[str, Any] = {}
        hp_def, hp_freq = self._startup_defaults[idx]
        lp_def, lp_freq = self._startup_defaults[idx + 1] if idx < 4 else ("None", 20000)

        ctrl['enabled'] = tk.BooleanVar(value=True)
        ctrl['name'] = tk.StringVar(value=f"Channel {idx+1}")
        ctrl['hp_type'] = tk.StringVar(value=hp_def)
        ctrl['hp_slope'] = tk.StringVar(value="24")
        ctrl['hp_freq'] = tk.StringVar(value=str(hp_freq))
        ctrl['lp_type'] = tk.StringVar(value=lp_def)
        ctrl['lp_slope'] = tk.StringVar(value="24")
        ctrl['lp_freq'] = tk.StringVar(value=str(lp_freq))

        ttk.Checkbutton(self.controls_frame, variable=ctrl['enabled'], command=lambda i=idx: self._update_curve(i)).grid(row=row, column=0)
        ttk.Entry(self.controls_frame, textvariable=ctrl['name'], width=10).grid(row=row, column=1)

        ctrl['hp_type_menu'] = self._option_menu(row, 2, ctrl['hp_type'], FILTER_TYPES, lambda *_: self._on_filter_change(idx), width=14)
        ctrl['hp_slope_menu'] = self._option_menu(row, 3, ctrl['hp_slope'], ["12", "24", "36"], lambda *_: self._on_filter_change(idx), width=4)
        ctrl['hp_freq_entry'] = self._entry(row, 4, ctrl['hp_freq'], lambda *_: self._on_filter_change(idx))

        ctrl['lp_type_menu'] = self._option_menu(row, 5, ctrl['lp_type'], FILTER_TYPES, lambda *_: self._on_filter_change(idx), width=14)
        ctrl['lp_slope_menu'] = self._option_menu(row, 6, ctrl['lp_slope'], ["12", "24", "36"], lambda *_: self._on_filter_change(idx), width=4)
        ctrl['lp_freq_entry'] = self._entry(row, 7, ctrl['lp_freq'], lambda *_: self._on_filter_change(idx))

        ttk.Button(self.controls_frame, text="Output Target", command=lambda i=idx: self._output_single(i)).grid(row=row, column=8)

        self.channel_controls.append(ctrl)
        self._on_filter_change(idx)

    def _option_menu(self, row: int, col: int, var: tk.StringVar, options: List[str], callback, width: int = 10):
        menu = ttk.OptionMenu(self.controls_frame, var, var.get(), *options, command=callback)
        menu.grid(row=row, column=col)
        menu.config(width=width)
        return menu

    def _entry(self, row: int, col: int, var: tk.StringVar, callback):
        ent = ttk.Entry(self.controls_frame, textvariable=var, width=6)
        ent.grid(row=row, column=col)
        ent.bind("<Return>", callback)
        return ent

    def _on_filter_change(self, idx: int) -> None:
        ctrl = self.channel_controls[idx]
        state_hp = 'disabled' if ctrl['hp_type'].get() == 'None' else 'normal'
        ctrl['hp_slope_menu'].config(state=state_hp)
        ctrl['hp_freq_entry'].config(state=state_hp)
        state_lp = 'disabled' if ctrl['lp_type'].get() == 'None' else 'normal'
        ctrl['lp_slope_menu'].config(state=state_lp)
        ctrl['lp_freq_entry'].config(state=state_lp)
        self._update_curve(idx)

    def _update_curve(self, idx: int) -> None:
        ctrl = self.channel_controls[idx]
        if not ctrl['enabled'].get():
            self.plot_frame.clear_channel(idx)
            return
        try:
            hp = FilterConfig(ctrl['hp_type'].get(), int(ctrl['hp_slope'].get()), float(ctrl['hp_freq'].get()))
            lp = FilterConfig(ctrl['lp_type'].get(), int(ctrl['lp_slope'].get()), float(ctrl['lp_freq'].get()))
            curve = generate_target_curve(hp, lp)
            self.plot_frame.update_channel_curve(idx, ctrl['name'].get(), curve)
        except ValueError:
            pass
        self._check_all_alerts()

    def _build_house_curve_editor(self, container: tk.Frame) -> None:
        self.house_frame = tk.Frame(container)
        self.house_frame.pack(side="top", fill="y", anchor="n", padx=5, pady=5)
        tk.Label(self.house_frame, text="House Curve Editor", font=(None, 12, 'bold')).grid(row=0, column=0, columnspan=len(CUSTOM_CURVES)+2)
        tk.Label(self.house_frame, text="Freq (Hz)").grid(row=1, column=0)
        tk.Label(self.house_frame, text="Active HC").grid(row=1, column=1)
        for j, name in enumerate(CUSTOM_CURVES, start=2):
            tk.Label(self.house_frame, text=name).grid(row=1, column=j)
            ttk.Button(self.house_frame, text="Load HC", command=lambda n=name: self._load_custom_curve(n)).grid(row=0, column=j)
        self.house_entries = []
        for i, f in enumerate(FREQUENCIES):
            r = i + 2
            tk.Label(self.house_frame, text=f"{int(f)}").grid(row=r, column=0)
            active_lbl = tk.Label(self.house_frame, text="0.0")
            active_lbl.grid(row=r, column=1)
            row_vars = []
            for name in CUSTOM_CURVES:
                dv = tk.DoubleVar(value=CUSTOM_CURVES[name][i])
                ent = ttk.Entry(self.house_frame, textvariable=dv, width=6)
                ent.grid(row=r, column=list(CUSTOM_CURVES).index(name)+2)
                ent.bind("<FocusOut>", lambda e, idx=i, nm=name, var=dv: self._update_custom_curve(idx, nm, var.get()))
                row_vars.append(dv)
            self.house_entries.append((active_lbl, row_vars))
        ttk.Button(self.house_frame, text="Reset Custom Curves", command=self._reset_custom_curves).grid(row=len(FREQUENCIES)+2, column=0, columnspan=len(CUSTOM_CURVES)+2)

    def _update_custom_curve(self, idx: int, name: str, value: float) -> None:
        CUSTOM_CURVES[name][idx] = value
        self._refresh_house_editor()
        self.plot_frame.update_house_curve(get_selected_house_curve(), get_selected_house_curve_name())

    def _reset_custom_curves(self) -> None:
        reset_custom_curves()
        set_selected_house_curve(get_selected_house_curve_name())
        self._refresh_house_editor()
        self.plot_frame.update_house_curve(get_selected_house_curve(), get_selected_house_curve_name())

    def _refresh_house_editor(self) -> None:
        hc = get_selected_house_curve()
        for i, (active_lbl, vars_) in enumerate(self.house_entries):
            active_lbl.config(text=f"{hc[i]:.1f}")
            for j, nm in enumerate(CUSTOM_CURVES):
                vars_[j].set(CUSTOM_CURVES[nm][i])

    def _check_all_alerts(self) -> None:
        msgs = []
        for i in range(len(self.channel_controls)-1):
            c1 = self.channel_controls[i]
            c2 = self.channel_controls[i+1]
            try:
                if all([
                    c1['enabled'].get(),
                    c2['enabled'].get(),
                    (c1['lp_type'].get(), c1['lp_slope'].get(), c1['lp_freq'].get()) != (c2['hp_type'].get(), c2['hp_slope'].get(), c2['hp_freq'].get())
                ]):
                    msgs.append(f"Mismatch between {c1['name'].get()} and {c2['name'].get()}")
            except ValueError:
                msgs.append("Invalid frequency input")
        if msgs:
            self.alert_var.set("⚠️ Click to view mismatches")
            self.alert_label.config(bg='yellow', fg='red')
            self.alert_label.bind("<Button-1>", lambda e: messagebox.showinfo("Alerts", "\n".join(msgs)))
            self.alert_label.pack(fill="x", side="top")
        else:
            self.alert_label.pack_forget()

    def _output_all(self) -> None:
        for idx in range(len(self.channel_controls)):
            self._output_single(idx)

    def _output_single(self, idx: int) -> None:
        pass

    def _set_output_folder(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.output_folder = path
            self.folder_label.config(text=f"Output Folder: {path}")
            self._save_settings()

    def _save_settings(self) -> None:
        try:
            settings = {
                "output_folder": self.output_folder,
                "channel_names": [ctrl['name'].get() for ctrl in self.channel_controls]
            }
            with open(SETTINGS_FILE, "w") as f:
                json.dump(settings, f)
        except Exception:
            pass

    def _load_settings(self) -> None:
        if not os.path.exists(SETTINGS_FILE):
            return
        try:
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
            self.output_folder = settings.get("output_folder", "")
            self.folder_label.config(text=f"Output Folder: {self.output_folder or 'Not set'}")
            for i, name in enumerate(settings.get("channel_names", [])):
                if i < len(self.channel_controls):
                    self.channel_controls[i]['name'].set(name)
        except Exception:
            pass