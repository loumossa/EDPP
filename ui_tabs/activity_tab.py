"""EDPP Activity Tab - PowerPlay collect/deliver log, rank progression."""

import tkinter as tk
from tkinter import ttk
from datetime import datetime

from models import DashboardState


class ActivityTab:
    def __init__(self, parent: ttk.Notebook):
        self.frame = ttk.Frame(parent, padding=10)
        self._build()

    def _build(self):
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=3)
        self.frame.rowconfigure(1, weight=1)

        # --- Top: Collect/Deliver Log ---
        cargo_frame = ttk.LabelFrame(self.frame, text="PowerPlay Logistics", padding=5)
        cargo_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        cargo_frame.columnconfigure(0, weight=1)
        cargo_frame.rowconfigure(0, weight=1)

        cargo_cols = ("timestamp", "action", "cargo", "count")
        self.cargo_tree = ttk.Treeview(cargo_frame, columns=cargo_cols,
                                       show="headings", height=10)
        self.cargo_tree.heading("timestamp", text="Timestamp")
        self.cargo_tree.heading("action", text="Action")
        self.cargo_tree.heading("cargo", text="Cargo Type")
        self.cargo_tree.heading("count", text="Count")

        self.cargo_tree.column("timestamp", width=160, minwidth=140)
        self.cargo_tree.column("action", width=80, minwidth=60)
        self.cargo_tree.column("cargo", width=250, minwidth=150)
        self.cargo_tree.column("count", width=80, minwidth=50, anchor="e")

        cargo_scroll = ttk.Scrollbar(cargo_frame, orient="vertical",
                                     command=self.cargo_tree.yview)
        self.cargo_tree.configure(yscrollcommand=cargo_scroll.set)

        self.cargo_tree.grid(row=0, column=0, sticky="nsew")
        cargo_scroll.grid(row=0, column=1, sticky="ns")

        self.lbl_cargo_summary = ttk.Label(cargo_frame, text="",
                                           font=("Segoe UI", 9))
        self.lbl_cargo_summary.grid(row=1, column=0, sticky="w", pady=(3, 0))

        # --- Bottom: Rank Progression ---
        rank_frame = ttk.LabelFrame(self.frame, text="Rank Progression", padding=5)
        rank_frame.grid(row=1, column=0, sticky="nsew")
        rank_frame.columnconfigure(0, weight=1)
        rank_frame.rowconfigure(0, weight=1)

        rank_cols = ("timestamp", "power", "rank")
        self.rank_tree = ttk.Treeview(rank_frame, columns=rank_cols,
                                      show="headings", height=6)
        self.rank_tree.heading("timestamp", text="Timestamp")
        self.rank_tree.heading("power", text="Power")
        self.rank_tree.heading("rank", text="New Rank")

        self.rank_tree.column("timestamp", width=160, minwidth=140)
        self.rank_tree.column("power", width=200, minwidth=120)
        self.rank_tree.column("rank", width=80, minwidth=50, anchor="e")

        rank_scroll = ttk.Scrollbar(rank_frame, orient="vertical",
                                    command=self.rank_tree.yview)
        self.rank_tree.configure(yscrollcommand=rank_scroll.set)

        self.rank_tree.grid(row=0, column=0, sticky="nsew")
        rank_scroll.grid(row=0, column=1, sticky="ns")

    def _format_ts(self, ts: str) -> str:
        try:
            dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return ts

    def update(self, state: DashboardState):
        """Refresh activity tab data."""
        # Cargo events (most recent first)
        self.cargo_tree.delete(*self.cargo_tree.get_children())
        total_collected = 0
        total_delivered = 0
        for evt in reversed(state.cargo_events):
            cargo_name = evt.cargo_type_localised or evt.cargo_type
            self.cargo_tree.insert("", "end", values=(
                self._format_ts(evt.timestamp),
                evt.event_type,
                cargo_name,
                f"{evt.count:,}",
            ))
            if evt.event_type == "Collect":
                total_collected += evt.count
            else:
                total_delivered += evt.count

        self.lbl_cargo_summary.configure(
            text=f"Total collected: {total_collected:,}  |  "
                 f"Total delivered: {total_delivered:,}  |  "
                 f"Events: {len(state.cargo_events)}")

        # Rank progression (most recent first)
        self.rank_tree.delete(*self.rank_tree.get_children())
        for evt in reversed(state.rank_events):
            self.rank_tree.insert("", "end", values=(
                self._format_ts(evt.timestamp),
                evt.power,
                str(evt.rank),
            ))
