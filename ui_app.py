"""EDPP Main Application Window - Header, tabs, refresh, status bar."""

import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from config import APP_TITLE, JOURNAL_DIR, DEFAULT_HISTORY_DAYS
from models import DashboardState
from journal_parser import parse_journals
from ui_tabs.powerplay_tab import PowerPlayTab
from ui_tabs.activity_tab import ActivityTab
from ui_tabs.systems_tab import SystemsTab
from ui_tabs.commander_tab import CommanderTab
from ui_tabs.missions_tab import MissionsTab
from ui_tabs.cycle_tab import CycleTab


def format_time_pledged(seconds: int) -> str:
    """Convert seconds to human-readable 'X days, Y hours'."""
    if seconds <= 0:
        return "N/A"
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    if days > 0:
        return f"{days}d {hours}h"
    return f"{hours}h"


def format_credits(amount: int) -> str:
    """Format credits with appropriate suffix."""
    if amount >= 1_000_000_000:
        return f"{amount / 1_000_000_000:.2f}B CR"
    elif amount >= 1_000_000:
        return f"{amount / 1_000_000:.1f}M CR"
    elif amount >= 1_000:
        return f"{amount / 1_000:.1f}K CR"
    else:
        return f"{amount:,} CR"


def format_timestamp(ts: str) -> str:
    """Format a journal timestamp for display."""
    if not ts:
        return "N/A"
    try:
        dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except ValueError:
        return ts


def format_timestamp_short(ts: str) -> str:
    """Format timestamp as short date/time."""
    if not ts:
        return ""
    try:
        dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return ts


class EDPPApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.state = DashboardState()
        self._build_ui()
        self._do_refresh()

    def _build_ui(self):
        """Build the main application layout."""
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)  # notebook gets all stretch

        # --- Header Frame ---
        self._build_header()

        # --- Tab Notebook ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))

        self.tab_powerplay = PowerPlayTab(self.notebook)
        self.tab_cycle = CycleTab(self.notebook)
        self.tab_activity = ActivityTab(self.notebook)
        self.tab_systems = SystemsTab(self.notebook)
        self.tab_commander = CommanderTab(self.notebook)
        self.tab_missions = MissionsTab(self.notebook)

        self.notebook.add(self.tab_powerplay.frame, text="  PowerPlay  ")
        self.notebook.add(self.tab_cycle.frame, text="  Cycle Tracker  ")
        self.notebook.add(self.tab_activity.frame, text="  Activity  ")
        self.notebook.add(self.tab_systems.frame, text="  Systems  ")
        self.notebook.add(self.tab_commander.frame, text="  Commander  ")
        self.notebook.add(self.tab_missions.frame, text="  Missions  ")

        # --- Status Bar ---
        self._build_status_bar()

    def _build_header(self):
        """Build the header bar with commander info and refresh button."""
        header = ttk.Frame(self.root, padding=10)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)

        # Left side: commander info (two rows)
        info_frame = ttk.Frame(header)
        info_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        info_frame.columnconfigure(0, weight=1)

        self.lbl_line1 = ttk.Label(info_frame, text="Loading...",
                                   font=("Segoe UI", 12, "bold"))
        self.lbl_line1.grid(row=0, column=0, sticky="w")

        self.lbl_line2 = ttk.Label(info_frame, text="",
                                   font=("Segoe UI", 10))
        self.lbl_line2.grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Right side: refresh button + last updated
        btn_frame = ttk.Frame(header)
        btn_frame.grid(row=0, column=2, sticky="ne", padx=(20, 0))

        self.refresh_btn = ttk.Button(btn_frame, text="Refresh Data",
                                      command=self._do_refresh)
        self.refresh_btn.grid(row=0, column=0, sticky="e")

        self.lbl_updated = ttk.Label(btn_frame, text="",
                                     font=("Segoe UI", 8))
        self.lbl_updated.grid(row=1, column=0, sticky="e", pady=(2, 0))

        # Separator
        sep = ttk.Separator(self.root, orient="horizontal")
        sep.grid(row=0, column=0, sticky="ews", padx=5)

    def _build_status_bar(self):
        """Build the bottom status bar."""
        status_frame = ttk.Frame(self.root, padding=(10, 3))
        status_frame.grid(row=2, column=0, sticky="ew")

        self.lbl_status = ttk.Label(status_frame, text="Ready",
                                    font=("Segoe UI", 8))
        self.lbl_status.pack(side="left")

    def _do_refresh(self):
        """Kick off journal parsing on a background thread."""
        self.refresh_btn.configure(state="disabled")
        self.lbl_updated.configure(text="Loading...")
        self.lbl_status.configure(text="Parsing journal files...")

        thread = threading.Thread(target=self._parse_in_background, daemon=True)
        thread.start()

    def _parse_in_background(self):
        """Runs on background thread."""
        try:
            new_state = parse_journals(JOURNAL_DIR, DEFAULT_HISTORY_DAYS)
            self.root.after(0, self._apply_state, new_state)
        except Exception as e:
            self.root.after(0, self._show_error, str(e))

    def _apply_state(self, new_state: DashboardState):
        """Update all UI elements with new state. Runs on main thread."""
        self.state = new_state
        self._update_header()
        self.tab_powerplay.update(new_state)
        self.tab_cycle.update(new_state)
        self.tab_activity.update(new_state)
        self.tab_systems.update(new_state)
        self.tab_commander.update(new_state)
        self.tab_missions.update(new_state)

        self.refresh_btn.configure(state="normal")
        now = datetime.now().strftime("%H:%M:%S")
        self.lbl_updated.configure(
            text=f"Updated {now} ({new_state.parse_duration_seconds:.1f}s)")
        self.lbl_status.configure(
            text=f"{new_state.journal_files_parsed} of {new_state.total_journal_files} "
                 f"journal files parsed  |  {DEFAULT_HISTORY_DAYS}-day history  |  "
                 f"{new_state.parse_duration_seconds:.2f}s")

    def _update_header(self):
        """Update the header labels with current state."""
        s = self.state
        cmdr = s.commander.name or "Unknown"
        power = s.powerplay.power or "Not Pledged"
        rank = s.powerplay.rank
        merits = f"{s.powerplay.merits:,}"
        pledged = format_time_pledged(s.powerplay.time_pledged_seconds)

        self.lbl_line1.configure(
            text=f"CMDR {cmdr}  |  {power}  |  Rank {rank}  |  Merits: {merits}")

        # Line 2: system, ship, credits
        system = "Unknown"
        pp_state = ""
        if s.current_system:
            system = s.current_system.star_system
            if s.current_system.powerplay_state:
                pp_state = f" ({s.current_system.powerplay_state})"

        ship = s.commander.ship_localised or s.commander.ship or "Unknown"
        ship_name = f" '{s.commander.ship_name}'" if s.commander.ship_name else ""
        credits = format_credits(s.commander.credits)

        self.lbl_line2.configure(
            text=f"System: {system}{pp_state}  |  "
                 f"Ship: {ship}{ship_name}  |  "
                 f"{credits}  |  Pledged: {pledged}")

    def _show_error(self, msg: str):
        """Show an error dialog. Runs on main thread."""
        self.refresh_btn.configure(state="normal")
        self.lbl_updated.configure(text="Error")
        self.lbl_status.configure(text=f"Error: {msg}")
        messagebox.showerror("Parse Error", f"Failed to parse journals:\n\n{msg}")
