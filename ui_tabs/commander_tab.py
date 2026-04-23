"""EDPP Commander Tab - Ranks, progress, reputation, statistics."""

import tkinter as tk
from tkinter import ttk

from config import RANK_TABLES
from models import DashboardState


class CommanderTab:
    def __init__(self, parent: ttk.Notebook):
        self.frame = ttk.Frame(parent, padding=10)
        self._build()

    def _build(self):
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(0, weight=0)
        self.frame.rowconfigure(1, weight=0)
        self.frame.rowconfigure(2, weight=1)

        # --- Top Left: Ranks & Progress ---
        rank_frame = ttk.LabelFrame(self.frame, text="Ranks & Progress", padding=10)
        rank_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=(0, 5))

        self.rank_widgets = {}
        rank_fields = [
            ("Combat", "combat"),
            ("Trade", "trade"),
            ("Exploration", "explore"),
            ("Mercenary", "soldier"),
            ("Exobiologist", "exobiologist"),
            ("CQC", "cqc"),
            ("Federation", "federation"),
            ("Empire", "empire"),
        ]
        for i, (display_name, key) in enumerate(rank_fields):
            ttk.Label(rank_frame, text=f"{display_name}:",
                      font=("Segoe UI", 9, "bold")).grid(
                row=i, column=0, sticky="w", padx=(0, 8), pady=2)

            rank_label = ttk.Label(rank_frame, text="--",
                                   font=("Segoe UI", 9), width=22)
            rank_label.grid(row=i, column=1, sticky="w", pady=2)

            progress_bar = ttk.Progressbar(rank_frame, length=150,
                                           mode="determinate", maximum=100)
            progress_bar.grid(row=i, column=2, sticky="w", padx=(5, 5), pady=2)

            pct_label = ttk.Label(rank_frame, text="", font=("Segoe UI", 8), width=5)
            pct_label.grid(row=i, column=3, sticky="w", pady=2)

            self.rank_widgets[key] = (rank_label, progress_bar, pct_label)

        # --- Top Right: Superpower Reputation ---
        rep_frame = ttk.LabelFrame(self.frame, text="Superpower Reputation", padding=10)
        rep_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=(0, 5))

        self.rep_widgets = {}
        rep_fields = [
            ("Federation", "federation"),
            ("Alliance", "alliance"),
            ("Empire", "empire"),
            ("Independent", "independent"),
        ]
        for i, (display_name, key) in enumerate(rep_fields):
            ttk.Label(rep_frame, text=f"{display_name}:",
                      font=("Segoe UI", 10, "bold")).grid(
                row=i, column=0, sticky="w", padx=(0, 10), pady=5)

            progress_bar = ttk.Progressbar(rep_frame, length=250,
                                           mode="determinate", maximum=100)
            progress_bar.grid(row=i, column=1, sticky="w", padx=(0, 8), pady=5)

            pct_label = ttk.Label(rep_frame, text="0.0%",
                                  font=("Segoe UI", 10), width=7)
            pct_label.grid(row=i, column=2, sticky="w", pady=5)

            self.rep_widgets[key] = (progress_bar, pct_label)

        # --- Commander Info ---
        info_frame = ttk.LabelFrame(self.frame, text="Commander Info", padding=10)
        info_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        self.info_labels = {}
        info_fields = [
            ("Commander", "name"),
            ("Frontier ID", "fid"),
            ("Ship", "ship"),
            ("Credits", "credits"),
            ("Game Version", "version"),
        ]
        info_frame.columnconfigure(1, weight=1)
        info_frame.columnconfigure(3, weight=1)
        for i, (display_name, key) in enumerate(info_fields):
            col = (i // 3) * 2
            row = i % 3
            ttk.Label(info_frame, text=f"{display_name}:",
                      font=("Segoe UI", 9, "bold")).grid(
                row=row, column=col, sticky="w", padx=(0, 8), pady=2)
            val_label = ttk.Label(info_frame, text="--", font=("Segoe UI", 9))
            val_label.grid(row=row, column=col + 1, sticky="w", padx=(0, 20), pady=2)
            self.info_labels[key] = val_label

        # --- Bottom: Statistics ---
        stats_frame = ttk.LabelFrame(self.frame, text="Statistics", padding=10)
        stats_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.rowconfigure(0, weight=1)

        # Use a text widget for flexible stats display
        self.stats_text = tk.Text(stats_frame, wrap="word", font=("Consolas", 9),
                                  state="disabled", bg="#f5f5f5", relief="flat",
                                  padx=10, pady=5)
        stats_scroll = ttk.Scrollbar(stats_frame, orient="vertical",
                                     command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=stats_scroll.set)
        self.stats_text.grid(row=0, column=0, sticky="nsew")
        stats_scroll.grid(row=0, column=1, sticky="ns")

    def update(self, state: DashboardState):
        """Refresh commander tab data."""
        self._update_ranks(state)
        self._update_reputation(state)
        self._update_info(state)
        self._update_statistics(state)

    def _update_ranks(self, state: DashboardState):
        """Update rank labels and progress bars."""
        for key, (rank_label, progress_bar, pct_label) in self.rank_widgets.items():
            rank_val = getattr(state.ranks, key, 0)
            progress_val = getattr(state.progress, key, 0)
            table = RANK_TABLES.get(key, {})

            rank_name = table.get(rank_val, f"Rank {rank_val}")

            # Find next rank name
            next_rank = rank_val + 1
            next_name = table.get(next_rank, "")
            if next_name and progress_val < 100:
                display = f"{rank_name} -> {next_name}"
            else:
                display = rank_name

            rank_label.configure(text=display)
            progress_bar["value"] = progress_val
            pct_label.configure(text=f"{progress_val}%")

    def _update_reputation(self, state: DashboardState):
        """Update reputation progress bars."""
        for key, (progress_bar, pct_label) in self.rep_widgets.items():
            val = getattr(state.reputation, key, 0.0)
            # Reputation can be negative in some cases; clamp to 0-100
            display_val = max(0.0, min(100.0, val))
            progress_bar["value"] = display_val
            pct_label.configure(text=f"{val:.1f}%")

    def _update_info(self, state: DashboardState):
        """Update commander info labels."""
        cmdr = state.commander
        self.info_labels["name"].configure(text=f"CMDR {cmdr.name}" if cmdr.name else "--")
        self.info_labels["fid"].configure(text=cmdr.fid or "--")

        ship_text = cmdr.ship_localised or cmdr.ship or "--"
        if cmdr.ship_name:
            ship_text += f" '{cmdr.ship_name}'"
        if cmdr.ship_ident:
            ship_text += f" [{cmdr.ship_ident}]"
        self.info_labels["ship"].configure(text=ship_text)

        if cmdr.credits > 0:
            self.info_labels["credits"].configure(text=f"{cmdr.credits:,} CR")
        else:
            self.info_labels["credits"].configure(text="--")

        version = cmdr.game_version or "--"
        extras = []
        if cmdr.horizons:
            extras.append("Horizons")
        if cmdr.odyssey:
            extras.append("Odyssey")
        if extras:
            version += f" ({', '.join(extras)})"
        self.info_labels["version"].configure(text=version)

    def _update_statistics(self, state: DashboardState):
        """Update the statistics text area."""
        self.stats_text.configure(state="normal")
        self.stats_text.delete("1.0", "end")

        stats = state.statistics
        if not stats:
            self.stats_text.insert("end", "No statistics available")
            self.stats_text.configure(state="disabled")
            return

        sections = [
            ("Bank Account", "Bank_Account", [
                ("Current Wealth", "Current_Wealth", "{:,} CR"),
                ("Insurance Claims", "Insurance_Claims", "{:,}"),
                ("Total Insurance Payouts", "Owned_Ship_Free_Amount", "{:,} CR"),
            ]),
            ("Combat", "Combat", [
                ("Bounties Claimed", "Bounties_Claimed", "{:,}"),
                ("Bounty Hunting Profit", "Bounty_Hunting_Profit", "{:,} CR"),
                ("Combat Bonds", "Combat_Bonds", "{:,}"),
                ("Combat Bond Profits", "Combat_Bond_Profits", "{:,} CR"),
                ("Assassinations", "Assassinations", "{:,}"),
                ("Skimmers Killed", "Skimmers_Killed", "{:,}"),
            ]),
            ("Trading", "Trading", [
                ("Markets Traded With", "Markets_Traded_With", "{:,}"),
                ("Market Profits", "Market_Profits", "{:,} CR"),
                ("Resources Traded", "Resources_Traded", "{:,}"),
                ("Average Profit", "Average_Profit", "{:,} CR"),
            ]),
            ("Mining", "Mining", [
                ("Mining Profits", "Mining_Profits", "{:,} CR"),
                ("Quantity Mined", "Quantity_Mined", "{:,}"),
                ("Materials Collected", "Materials_Collected", "{:,}"),
            ]),
            ("Exploration", "Exploration", [
                ("Systems Visited", "Systems_Visited", "{:,}"),
                ("Total Hyperspace Distance", "Total_Hyperspace_Distance", "{:,} Ly"),
                ("Total Hyperspace Jumps", "Total_Hyperspace_Jumps", "{:,}"),
                ("Exploration Profits", "Exploration_Profits", "{:,} CR"),
                ("Planets Scanned To Level 2", "Planets_Scanned_To_Level_2", "{:,}"),
                ("Planets Scanned To Level 3", "Planets_Scanned_To_Level_3", "{:,}"),
                ("Highest Payout", "Highest_Payout", "{:,} CR"),
                ("Greatest Distance From Start", "Greatest_Distance_From_Start", "{:.1f} Ly"),
                ("Time Played", "Time_Played", None),
            ]),
            ("Exobiology", "Exobiology", [
                ("Organic Genus Encountered", "Organic_Genus_Encountered", "{:,}"),
                ("Organic Species Encountered", "Organic_Species_Encountered", "{:,}"),
                ("Organics Profit", "Organics_Profit", "{:,} CR"),
                ("First Logged Profits", "First_Logged_Profits", "{:,} CR"),
                ("First Logged", "First_Logged", "{:,}"),
            ]),
            ("Passengers", "Passengers", [
                ("Passengers Delivered", "Passengers_Missions_Delivered", "{:,}"),
                ("No VIPs Delivered", "Passengers_Missions_Bulk", "{:,}"),
                ("VIPs Delivered", "Passengers_Missions_VIP", "{:,}"),
            ]),
        ]

        for section_name, section_key, fields in sections:
            section_data = stats.get(section_key, {})
            if not section_data:
                continue

            self.stats_text.insert("end", f"\n  {section_name}\n")
            self.stats_text.insert("end", "  " + "-" * 50 + "\n")

            for display_name, field_key, fmt in fields:
                value = section_data.get(field_key)
                if value is None:
                    continue
                if fmt is None:
                    # Special: Time_Played is in seconds
                    if isinstance(value, (int, float)):
                        hours = int(value) // 3600
                        mins = (int(value) % 3600) // 60
                        formatted = f"{hours:,} hours, {mins} minutes"
                    else:
                        formatted = str(value)
                else:
                    try:
                        formatted = fmt.format(value)
                    except (ValueError, TypeError):
                        formatted = str(value)
                self.stats_text.insert("end", f"  {display_name:.<40} {formatted}\n")

        self.stats_text.configure(state="disabled")
