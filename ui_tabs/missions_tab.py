"""EDPP Missions Tab - Mission history: accepted, completed, failed."""

import tkinter as tk
from tkinter import ttk
from datetime import datetime

from models import DashboardState


class MissionsTab:
    def __init__(self, parent: ttk.Notebook):
        self.frame = ttk.Frame(parent, padding=10)
        self._all_missions = []
        self._build()

    def _build(self):
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)

        # --- Filter Bar ---
        filter_frame = ttk.Frame(self.frame)
        filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        ttk.Label(filter_frame, text="Filter:",
                  font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 5))

        self.filter_var = tk.StringVar(value="All")
        for f in ["All", "Accepted", "Completed", "Abandoned", "Failed"]:
            ttk.Radiobutton(filter_frame, text=f, variable=self.filter_var,
                            value=f, command=self._apply_filter).pack(
                side="left", padx=3)

        self.lbl_count = ttk.Label(filter_frame, text="",
                                   font=("Segoe UI", 9))
        self.lbl_count.pack(side="right")

        # --- Missions Treeview ---
        tree_frame = ttk.Frame(self.frame)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        columns = ("timestamp", "status", "name", "faction",
                    "destination", "reward")
        self.tree = ttk.Treeview(tree_frame, columns=columns,
                                 show="headings", height=20)

        self.tree.heading("timestamp", text="Timestamp",
                          command=lambda: self._sort_column("timestamp", False))
        self.tree.heading("status", text="Status",
                          command=lambda: self._sort_column("status", False))
        self.tree.heading("name", text="Mission",
                          command=lambda: self._sort_column("name", False))
        self.tree.heading("faction", text="Faction",
                          command=lambda: self._sort_column("faction", False))
        self.tree.heading("destination", text="Destination",
                          command=lambda: self._sort_column("destination", False))
        self.tree.heading("reward", text="Reward",
                          command=lambda: self._sort_column("reward", False))

        self.tree.column("timestamp", width=140, minwidth=120)
        self.tree.column("status", width=90, minwidth=70)
        self.tree.column("name", width=280, minwidth=150)
        self.tree.column("faction", width=180, minwidth=100)
        self.tree.column("destination", width=150, minwidth=100)
        self.tree.column("reward", width=100, minwidth=70, anchor="e")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # --- Summary ---
        self.lbl_summary = ttk.Label(self.frame, text="",
                                     font=("Segoe UI", 9))
        self.lbl_summary.grid(row=2, column=0, sticky="w", pady=(3, 0))

    def _format_ts(self, ts: str) -> str:
        try:
            dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return ts

    def _format_reward(self, reward: int) -> str:
        if reward <= 0:
            return ""
        if reward >= 1_000_000:
            return f"{reward / 1_000_000:.1f}M CR"
        elif reward >= 1_000:
            return f"{reward / 1_000:.0f}K CR"
        return f"{reward:,} CR"

    def _clean_mission_name(self, evt) -> str:
        """Get a readable mission name."""
        name = evt.localised_name or evt.name or "Unknown Mission"
        # Internal names often look like "Mission_Collect_Industrial"
        # Use localised name when available
        return name

    def _sort_column(self, col: str, reverse: bool):
        """Sort treeview by column."""
        data = [(self.tree.set(child, col), child)
                for child in self.tree.get_children("")]
        if col == "reward":
            def sort_key(item):
                val = item[0].replace(",", "").replace(" CR", "")
                val = val.replace("M", "e6").replace("K", "e3")
                try:
                    return float(val) if val else 0
                except ValueError:
                    return 0
            data.sort(key=sort_key, reverse=reverse)
        else:
            data.sort(key=lambda t: t[0], reverse=reverse)

        for index, (_, child) in enumerate(data):
            self.tree.move(child, "", index)
        self.tree.heading(col, command=lambda: self._sort_column(col, not reverse))

    def _apply_filter(self):
        """Re-populate tree based on current filter."""
        filter_val = self.filter_var.get()
        self.tree.delete(*self.tree.get_children())

        shown = 0
        total_reward = 0
        completed = 0
        failed = 0

        for evt in reversed(self._all_missions):
            if filter_val != "All" and evt.event_type != filter_val:
                continue

            destination = evt.destination_system
            if evt.destination_station:
                destination = f"{evt.destination_system} / {evt.destination_station}"

            self.tree.insert("", "end", values=(
                self._format_ts(evt.timestamp),
                evt.event_type,
                self._clean_mission_name(evt),
                evt.faction,
                destination,
                self._format_reward(evt.reward),
            ))
            shown += 1

        # Compute summary from all missions (not filtered)
        for evt in self._all_missions:
            if evt.event_type == "Completed":
                completed += 1
                total_reward += evt.reward
            elif evt.event_type == "Failed":
                failed += 1

        self.lbl_count.configure(
            text=f"Showing {shown:,} of {len(self._all_missions):,} events")
        self.lbl_summary.configure(
            text=f"Completed: {completed:,}  |  Failed: {failed:,}  |  "
                 f"Total Rewards: {self._format_reward(total_reward)}")

    def update(self, state: DashboardState):
        """Refresh missions tab data."""
        self._all_missions = state.mission_events
        self._apply_filter()
