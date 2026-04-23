"""EDPP PowerPlay Tab - Pledge status, merits, current system PP state."""

import tkinter as tk
from tkinter import ttk

from models import DashboardState


class PowerPlayTab:
    def __init__(self, parent: ttk.Notebook):
        self.frame = ttk.Frame(parent, padding=10)
        self._build()

    def _build(self):
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(2, weight=1)

        # --- Top Left: Pledge Status ---
        pledge_frame = ttk.LabelFrame(self.frame, text="Pledge Status", padding=10)
        pledge_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=(0, 5))

        self.pledge_labels = {}
        fields = [
            ("Power", "power"),
            ("Rank", "rank"),
            ("Merits", "merits"),
            ("Time Pledged", "time_pledged"),
            ("Pledged Since", "pledge_date"),
        ]
        for i, (label, key) in enumerate(fields):
            ttk.Label(pledge_frame, text=f"{label}:",
                      font=("Segoe UI", 10, "bold")).grid(
                row=i, column=0, sticky="w", padx=(0, 10), pady=2)
            val_label = ttk.Label(pledge_frame, text="--",
                                  font=("Segoe UI", 10))
            val_label.grid(row=i, column=1, sticky="w", pady=2)
            self.pledge_labels[key] = val_label

        # --- Top Right: Current System PowerPlay ---
        system_frame = ttk.LabelFrame(self.frame, text="Current System PowerPlay", padding=10)
        system_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=(0, 5))

        self.system_labels = {}
        sys_fields = [
            ("System", "system"),
            ("PP State", "pp_state"),
            ("Controlling Power", "ctrl_power"),
            ("Powers Present", "powers"),
            ("Control Progress", "control_pct"),
            ("Reinforcement", "reinforcement"),
            ("Undermining", "undermining"),
            ("Allegiance", "allegiance"),
            ("Population", "population"),
        ]
        for i, (label, key) in enumerate(sys_fields):
            ttk.Label(system_frame, text=f"{label}:",
                      font=("Segoe UI", 10, "bold")).grid(
                row=i, column=0, sticky="w", padx=(0, 10), pady=2)
            val_label = ttk.Label(system_frame, text="--",
                                  font=("Segoe UI", 10))
            val_label.grid(row=i, column=1, sticky="w", pady=2)
            self.system_labels[key] = val_label

        # --- Summary Row ---
        summary_frame = ttk.LabelFrame(self.frame, text="Merit Summary", padding=10)
        summary_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        self.lbl_merit_summary = ttk.Label(summary_frame, text="--",
                                           font=("Segoe UI", 10))
        self.lbl_merit_summary.pack(anchor="w")

        # --- Bottom: Recent Merit Gains Table ---
        table_frame = ttk.LabelFrame(self.frame, text="Recent Merit Gains", padding=5)
        table_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = ("timestamp", "gained", "total")
        self.merit_tree = ttk.Treeview(table_frame, columns=columns,
                                       show="headings", height=12)
        self.merit_tree.heading("timestamp", text="Timestamp")
        self.merit_tree.heading("gained", text="Merits Gained")
        self.merit_tree.heading("total", text="Total Merits")

        self.merit_tree.column("timestamp", width=180, minwidth=150)
        self.merit_tree.column("gained", width=120, minwidth=80, anchor="e")
        self.merit_tree.column("total", width=120, minwidth=80, anchor="e")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical",
                                  command=self.merit_tree.yview)
        self.merit_tree.configure(yscrollcommand=scrollbar.set)

        self.merit_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    def update(self, state: DashboardState):
        """Refresh all PowerPlay tab data."""
        pp = state.powerplay

        # Pledge status
        self.pledge_labels["power"].configure(text=pp.power or "Not Pledged")
        self.pledge_labels["rank"].configure(text=str(pp.rank))
        self.pledge_labels["merits"].configure(text=f"{pp.merits:,}")

        if pp.time_pledged_seconds > 0:
            days = pp.time_pledged_seconds // 86400
            hours = (pp.time_pledged_seconds % 86400) // 3600
            self.pledge_labels["time_pledged"].configure(text=f"{days} days, {hours} hours")
        else:
            self.pledge_labels["time_pledged"].configure(text="N/A")

        if pp.pledge_timestamp:
            try:
                from datetime import datetime
                dt = datetime.strptime(pp.pledge_timestamp, "%Y-%m-%dT%H:%M:%SZ")
                self.pledge_labels["pledge_date"].configure(
                    text=dt.strftime("%Y-%m-%d %H:%M UTC"))
            except ValueError:
                self.pledge_labels["pledge_date"].configure(text=pp.pledge_timestamp)
        else:
            self.pledge_labels["pledge_date"].configure(text="N/A")

        # Current system
        cs = state.current_system
        if cs:
            self.system_labels["system"].configure(text=cs.star_system or "N/A")
            self.system_labels["pp_state"].configure(text=cs.powerplay_state or "None")
            self.system_labels["ctrl_power"].configure(text=cs.controlling_power or "None")
            powers_text = ", ".join(cs.powers) if cs.powers else "None"
            self.system_labels["powers"].configure(text=powers_text)
            if cs.powerplay_state_control_progress > 0:
                self.system_labels["control_pct"].configure(
                    text=f"{cs.powerplay_state_control_progress:.1%}")
            else:
                self.system_labels["control_pct"].configure(text="N/A")
            self.system_labels["reinforcement"].configure(
                text=f"{cs.powerplay_state_reinforcement:,}" if cs.powerplay_state_reinforcement else "0")
            self.system_labels["undermining"].configure(
                text=f"{cs.powerplay_state_undermining:,}" if cs.powerplay_state_undermining else "0")
            self.system_labels["allegiance"].configure(text=cs.allegiance or "N/A")
            self.system_labels["population"].configure(
                text=f"{cs.population:,}" if cs.population else "0")
        else:
            for key in self.system_labels:
                self.system_labels[key].configure(text="N/A")

        # Merit summary
        total_gained = sum(e.merits_gained for e in state.merit_events)
        self.lbl_merit_summary.configure(
            text=f"Total merits earned in period: {total_gained:,}  |  "
                 f"Merit events: {len(state.merit_events):,}")

        # Merit events table (most recent first, limit 200)
        self.merit_tree.delete(*self.merit_tree.get_children())
        for evt in reversed(state.merit_events[-200:]):
            ts = evt.timestamp
            try:
                from datetime import datetime
                dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
                ts = dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
            self.merit_tree.insert("", "end", values=(
                ts,
                f"+{evt.merits_gained:,}",
                f"{evt.total_merits:,}",
            ))
