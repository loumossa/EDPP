"""EDPP Cycle Tab - Weekly PowerPlay cycle tracking and merit breakdown."""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from collections import defaultdict

from models import DashboardState


# PowerPlay cycles reset every Thursday at 07:00 UTC
CYCLE_RESET_WEEKDAY = 3  # Thursday (Monday=0)
CYCLE_RESET_HOUR = 7


def _get_cycle_start(dt: datetime) -> datetime:
    """Get the start of the PowerPlay cycle that contains the given datetime.

    Cycles reset every Thursday at 07:00 UTC.
    """
    # Find the most recent Thursday 07:00 UTC at or before dt
    days_since_thursday = (dt.weekday() - CYCLE_RESET_WEEKDAY) % 7
    candidate = dt.replace(hour=CYCLE_RESET_HOUR, minute=0, second=0, microsecond=0)
    candidate -= timedelta(days=days_since_thursday)

    # If we're before the reset time on Thursday, go back a week
    if dt < candidate:
        candidate -= timedelta(days=7)

    return candidate


def _get_cycle_end(cycle_start: datetime) -> datetime:
    """Get the end of a cycle (= start of next cycle)."""
    return cycle_start + timedelta(days=7)


def _parse_ts(ts: str) -> datetime:
    """Parse journal timestamp to datetime."""
    try:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return datetime.min


def _format_cycle_label(cycle_start: datetime) -> str:
    """Format a cycle as a readable date range."""
    end = _get_cycle_end(cycle_start) - timedelta(seconds=1)
    return f"{cycle_start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}"


def _classify_merit_source(merits_gained: int) -> str:
    """Classify merit gains into approximate activity categories.

    Based on analysis of actual journal data:
    - Small (2-10): Individual kills, combat ticks, small actions
    - Medium (11-99): Larger combat, cargo, hacking
    - Large (100-999): Voucher redemptions, deliveries, multi-kills
    - Very Large (1000+): Exploration data sales, large bounty redemptions
    """
    if merits_gained <= 10:
        return "Combat/Small"
    elif merits_gained <= 99:
        return "Combat/Medium"
    elif merits_gained <= 999:
        return "Vouchers/Delivery"
    else:
        return "Exploration/Large"


class CycleTab:
    def __init__(self, parent: ttk.Notebook):
        self.frame = ttk.Frame(parent, padding=10)
        self._build()

    def _build(self):
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(2, weight=1)

        # --- Current Cycle Summary ---
        current_frame = ttk.LabelFrame(self.frame, text="Current Cycle", padding=10)
        current_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        current_frame.columnconfigure(1, weight=1)

        self.current_labels = {}
        fields = [
            ("Cycle Period", "period"),
            ("Days Remaining", "remaining"),
            ("Merits This Cycle", "merits"),
            ("Daily Average", "daily_avg"),
            ("Activity Breakdown", "breakdown"),
        ]
        for i, (label, key) in enumerate(fields):
            ttk.Label(current_frame, text=f"{label}:",
                      font=("Segoe UI", 10, "bold")).grid(
                row=i, column=0, sticky="w", padx=(0, 15), pady=3)
            val_label = ttk.Label(current_frame, text="--",
                                  font=("Segoe UI", 10))
            val_label.grid(row=i, column=1, sticky="w", pady=3)
            self.current_labels[key] = val_label

        # --- Cycle History Table ---
        history_frame = ttk.LabelFrame(self.frame, text="Cycle History", padding=5)
        history_frame.grid(row=1, column=0, sticky="ew", pady=(0, 5))
        history_frame.columnconfigure(0, weight=1)

        cycle_cols = ("cycle", "merits", "events", "daily_avg",
                      "combat_small", "combat_med", "vouchers", "exploration")
        self.cycle_tree = ttk.Treeview(history_frame, columns=cycle_cols,
                                       show="headings", height=6)

        self.cycle_tree.heading("cycle", text="Cycle")
        self.cycle_tree.heading("merits", text="Total Merits")
        self.cycle_tree.heading("events", text="Events")
        self.cycle_tree.heading("daily_avg", text="Daily Avg")
        self.cycle_tree.heading("combat_small", text="Combat/Small")
        self.cycle_tree.heading("combat_med", text="Combat/Med")
        self.cycle_tree.heading("vouchers", text="Vouchers/Dlvr")
        self.cycle_tree.heading("exploration", text="Explore/Large")

        self.cycle_tree.column("cycle", width=180, minwidth=150)
        self.cycle_tree.column("merits", width=100, minwidth=80, anchor="e")
        self.cycle_tree.column("events", width=70, minwidth=50, anchor="e")
        self.cycle_tree.column("daily_avg", width=90, minwidth=70, anchor="e")
        self.cycle_tree.column("combat_small", width=100, minwidth=70, anchor="e")
        self.cycle_tree.column("combat_med", width=100, minwidth=70, anchor="e")
        self.cycle_tree.column("vouchers", width=100, minwidth=70, anchor="e")
        self.cycle_tree.column("exploration", width=100, minwidth=70, anchor="e")

        cycle_scroll = ttk.Scrollbar(history_frame, orient="vertical",
                                     command=self.cycle_tree.yview)
        self.cycle_tree.configure(yscrollcommand=cycle_scroll.set)
        self.cycle_tree.grid(row=0, column=0, sticky="nsew")
        cycle_scroll.grid(row=0, column=1, sticky="ns")

        # --- Daily Detail Table ---
        daily_frame = ttk.LabelFrame(self.frame, text="Daily Merit Breakdown (Current Cycle)", padding=5)
        daily_frame.grid(row=2, column=0, sticky="nsew")
        daily_frame.columnconfigure(0, weight=1)
        daily_frame.rowconfigure(0, weight=1)

        daily_cols = ("date", "merits", "events", "combat_small",
                      "combat_med", "vouchers", "exploration")
        self.daily_tree = ttk.Treeview(daily_frame, columns=daily_cols,
                                       show="headings", height=8)

        self.daily_tree.heading("date", text="Date")
        self.daily_tree.heading("merits", text="Merits")
        self.daily_tree.heading("events", text="Events")
        self.daily_tree.heading("combat_small", text="Combat/Small")
        self.daily_tree.heading("combat_med", text="Combat/Med")
        self.daily_tree.heading("vouchers", text="Vouchers/Dlvr")
        self.daily_tree.heading("exploration", text="Explore/Large")

        self.daily_tree.column("date", width=120, minwidth=100)
        self.daily_tree.column("merits", width=100, minwidth=70, anchor="e")
        self.daily_tree.column("events", width=70, minwidth=50, anchor="e")
        self.daily_tree.column("combat_small", width=100, minwidth=70, anchor="e")
        self.daily_tree.column("combat_med", width=100, minwidth=70, anchor="e")
        self.daily_tree.column("vouchers", width=100, minwidth=70, anchor="e")
        self.daily_tree.column("exploration", width=100, minwidth=70, anchor="e")

        daily_scroll = ttk.Scrollbar(daily_frame, orient="vertical",
                                     command=self.daily_tree.yview)
        self.daily_tree.configure(yscrollcommand=daily_scroll.set)
        self.daily_tree.grid(row=0, column=0, sticky="nsew")
        daily_scroll.grid(row=0, column=1, sticky="ns")

    def update(self, state: DashboardState):
        """Refresh cycle tab with merit data organized by PP cycles."""
        now = datetime.utcnow()
        current_cycle_start = _get_cycle_start(now)
        current_cycle_end = _get_cycle_end(current_cycle_start)

        # Organize merit events by cycle
        cycles = defaultdict(lambda: {
            "merits": 0, "events": 0,
            "Combat/Small": 0, "Combat/Medium": 0,
            "Vouchers/Delivery": 0, "Exploration/Large": 0,
        })
        # Daily breakdown for current cycle
        daily = defaultdict(lambda: {
            "merits": 0, "events": 0,
            "Combat/Small": 0, "Combat/Medium": 0,
            "Vouchers/Delivery": 0, "Exploration/Large": 0,
        })

        for evt in state.merit_events:
            dt = _parse_ts(evt.timestamp)
            if dt == datetime.min:
                continue

            cycle_start = _get_cycle_start(dt)
            source = _classify_merit_source(evt.merits_gained)

            cycles[cycle_start]["merits"] += evt.merits_gained
            cycles[cycle_start]["events"] += 1
            cycles[cycle_start][source] += evt.merits_gained

            # If in current cycle, also track daily
            if cycle_start == current_cycle_start:
                day_key = dt.strftime("%Y-%m-%d")
                daily[day_key]["merits"] += evt.merits_gained
                daily[day_key]["events"] += 1
                daily[day_key][source] += evt.merits_gained

        # --- Update Current Cycle Summary ---
        cc = cycles.get(current_cycle_start)
        if cc:
            days_elapsed = (now - current_cycle_start).total_seconds() / 86400
            days_remaining = max(0, (current_cycle_end - now).total_seconds() / 86400)
            daily_avg = int(cc["merits"] / max(1, days_elapsed))

            self.current_labels["period"].configure(
                text=_format_cycle_label(current_cycle_start))
            self.current_labels["remaining"].configure(
                text=f"{days_remaining:.1f} days")
            self.current_labels["merits"].configure(
                text=f"{cc['merits']:,}")
            self.current_labels["daily_avg"].configure(
                text=f"{daily_avg:,} merits/day")

            # Breakdown
            parts = []
            for cat in ["Combat/Small", "Combat/Medium", "Vouchers/Delivery", "Exploration/Large"]:
                if cc[cat] > 0:
                    pct = cc[cat] / max(1, cc["merits"]) * 100
                    parts.append(f"{cat}: {cc[cat]:,} ({pct:.0f}%)")
            self.current_labels["breakdown"].configure(
                text="  |  ".join(parts) if parts else "No activity")
        else:
            self.current_labels["period"].configure(
                text=_format_cycle_label(current_cycle_start))
            days_remaining = max(0, (current_cycle_end - now).total_seconds() / 86400)
            self.current_labels["remaining"].configure(
                text=f"{days_remaining:.1f} days")
            self.current_labels["merits"].configure(text="0")
            self.current_labels["daily_avg"].configure(text="0 merits/day")
            self.current_labels["breakdown"].configure(text="No activity this cycle")

        # --- Cycle History Table ---
        self.cycle_tree.delete(*self.cycle_tree.get_children())
        for cycle_start in sorted(cycles.keys(), reverse=True):
            data = cycles[cycle_start]
            cycle_end = _get_cycle_end(cycle_start)
            elapsed_days = min(7, (min(now, cycle_end) - cycle_start).total_seconds() / 86400)
            daily_avg = int(data["merits"] / max(1, elapsed_days))

            # Highlight current cycle
            tag = "current" if cycle_start == current_cycle_start else ""

            self.cycle_tree.insert("", "end", values=(
                _format_cycle_label(cycle_start),
                f"{data['merits']:,}",
                f"{data['events']:,}",
                f"{daily_avg:,}/day",
                f"{data['Combat/Small']:,}" if data["Combat/Small"] else "-",
                f"{data['Combat/Medium']:,}" if data["Combat/Medium"] else "-",
                f"{data['Vouchers/Delivery']:,}" if data["Vouchers/Delivery"] else "-",
                f"{data['Exploration/Large']:,}" if data["Exploration/Large"] else "-",
            ), tags=(tag,))

        # Style the current cycle row
        self.cycle_tree.tag_configure("current", background="#e6f3ff")

        # --- Daily Breakdown Table ---
        self.daily_tree.delete(*self.daily_tree.get_children())
        for day_key in sorted(daily.keys(), reverse=True):
            data = daily[day_key]
            try:
                day_display = datetime.strptime(day_key, "%Y-%m-%d").strftime("%A, %b %d")
            except ValueError:
                day_display = day_key

            # Highlight today
            today = now.strftime("%Y-%m-%d")
            tag = "today" if day_key == today else ""

            self.daily_tree.insert("", "end", values=(
                day_display,
                f"{data['merits']:,}",
                f"{data['events']:,}",
                f"{data['Combat/Small']:,}" if data["Combat/Small"] else "-",
                f"{data['Combat/Medium']:,}" if data["Combat/Medium"] else "-",
                f"{data['Vouchers/Delivery']:,}" if data["Vouchers/Delivery"] else "-",
                f"{data['Exploration/Large']:,}" if data["Exploration/Large"] else "-",
            ), tags=(tag,))

        self.daily_tree.tag_configure("today", background="#e6ffe6")
