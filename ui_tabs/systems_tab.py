"""EDPP Systems Tab - Visited systems with PowerPlay state."""

import tkinter as tk
from tkinter import ttk
from datetime import datetime

from models import DashboardState


class SystemsTab:
    def __init__(self, parent: ttk.Notebook):
        self.frame = ttk.Frame(parent, padding=10)
        self._all_systems = []
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
        filters = ["All", "Has PowerPlay", "Stronghold", "Fortified",
                    "Exploited", "Contested", "Unoccupied"]
        for f in filters:
            ttk.Radiobutton(filter_frame, text=f, variable=self.filter_var,
                            value=f, command=self._apply_filter).pack(
                side="left", padx=3)

        self.lbl_count = ttk.Label(filter_frame, text="",
                                   font=("Segoe UI", 9))
        self.lbl_count.pack(side="right")

        # --- Systems Treeview ---
        tree_frame = ttk.Frame(self.frame)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        columns = ("timestamp", "system", "ctrl_power", "state",
                    "allegiance", "population")
        self.tree = ttk.Treeview(tree_frame, columns=columns,
                                 show="headings", height=20)

        self.tree.heading("timestamp", text="Timestamp",
                          command=lambda: self._sort_column("timestamp", False))
        self.tree.heading("system", text="System",
                          command=lambda: self._sort_column("system", False))
        self.tree.heading("ctrl_power", text="Controlling Power",
                          command=lambda: self._sort_column("ctrl_power", False))
        self.tree.heading("state", text="PP State",
                          command=lambda: self._sort_column("state", False))
        self.tree.heading("allegiance", text="Allegiance",
                          command=lambda: self._sort_column("allegiance", False))
        self.tree.heading("population", text="Population",
                          command=lambda: self._sort_column("population", False))

        self.tree.column("timestamp", width=140, minwidth=120)
        self.tree.column("system", width=180, minwidth=120)
        self.tree.column("ctrl_power", width=160, minwidth=100)
        self.tree.column("state", width=120, minwidth=80)
        self.tree.column("allegiance", width=100, minwidth=70)
        self.tree.column("population", width=120, minwidth=80, anchor="e")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    def _format_ts(self, ts: str) -> str:
        try:
            dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return ts

    def _sort_column(self, col: str, reverse: bool):
        """Sort treeview by column."""
        data = [(self.tree.set(child, col), child)
                for child in self.tree.get_children("")]
        # Try numeric sort for population
        if col == "population":
            try:
                data.sort(key=lambda t: int(t[0].replace(",", "") or "0"),
                          reverse=reverse)
            except ValueError:
                data.sort(key=lambda t: t[0], reverse=reverse)
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
        for sv in reversed(self._all_systems):
            if filter_val == "All":
                pass
            elif filter_val == "Has PowerPlay":
                if not sv.powerplay_state:
                    continue
            else:
                if sv.powerplay_state != filter_val:
                    continue

            self.tree.insert("", "end", values=(
                self._format_ts(sv.timestamp),
                sv.star_system,
                sv.controlling_power or "None",
                sv.powerplay_state or "None",
                sv.allegiance or "N/A",
                f"{sv.population:,}" if sv.population else "0",
            ))
            shown += 1

        self.lbl_count.configure(text=f"Showing {shown:,} of {len(self._all_systems):,} systems")

    def update(self, state: DashboardState):
        """Refresh systems tab data."""
        self._all_systems = state.systems_visited
        self._apply_filter()
