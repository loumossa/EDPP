"""EDPP Journal Parser - Two-phase parsing of Elite Dangerous journal files."""

import json
import glob
import os
import time
from datetime import datetime, timedelta, timezone

from config import JOURNAL_DIR, SNAPSHOT_EVENTS, ACTIVITY_EVENTS, DEFAULT_HISTORY_DAYS
from models import (
    DashboardState, CommanderInfo, PowerplayStatus,
    PowerplayMeritEvent, PowerplayCargoEvent, PowerplayRankEvent,
    SystemVisit, RankInfo, ProgressInfo, ReputationInfo,
    MissionEvent,
)


def _extract_event_fast(line: str) -> str:
    """Extract event name from a journal line without full JSON parse.

    Journal lines always contain "event":"EventName" near the start.
    Two str.find() calls are much faster than json.loads() for filtering.
    """
    idx = line.find('"event":"')
    if idx == -1:
        return ""
    start = idx + 9
    end = line.find('"', start)
    if end == -1:
        return ""
    return line[start:end]


def _compute_cutoff_filename(history_days: int) -> str:
    """Convert a history window (days) to a journal filename prefix for filtering."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=history_days)
    return f"Journal.{cutoff.strftime('%Y-%m-%dT%H%M%S')}.01.log"


def _parse_system_visit(entry: dict) -> SystemVisit:
    """Parse an FSDJump or Location event into a SystemVisit."""
    sv = SystemVisit()
    sv.timestamp = entry.get("timestamp", "")
    sv.star_system = entry.get("StarSystem", "")
    sv.system_address = entry.get("SystemAddress", 0)
    sv.star_pos = entry.get("StarPos", [])

    # PowerPlay fields (may be absent in uninhabited systems)
    powers = entry.get("Powers", [])
    sv.powers = powers
    sv.controlling_power = powers[0] if powers else ""
    sv.powerplay_state = entry.get("PowerplayState", "")

    # Detailed PP state fields (PowerPlay 2.0 format)
    sv.powerplay_state_control_progress = entry.get("PowerplayStateControlProgress", 0.0)
    sv.powerplay_state_reinforcement = entry.get("PowerplayStateReinforcement", 0)
    sv.powerplay_state_undermining = entry.get("PowerplayStateUndermining", 0)
    sv.conflict_progress = entry.get("PowerplayConflictProgress", [])

    # System info
    sv.allegiance = entry.get("SystemAllegiance", "")
    sv.economy = entry.get("SystemEconomy", "")
    sv.economy_localised = entry.get("SystemEconomy_Localised", "")
    sv.government = entry.get("SystemGovernment", "")
    sv.government_localised = entry.get("SystemGovernment_Localised", "")
    sv.security = entry.get("SystemSecurity", "")
    sv.security_localised = entry.get("SystemSecurity_Localised", "")
    sv.population = entry.get("Population", 0)

    faction = entry.get("SystemFaction", {})
    sv.controlling_faction = faction.get("Name", "") if isinstance(faction, dict) else ""

    return sv


def _apply_snapshot_event(entry: dict, event_name: str, state: DashboardState):
    """Apply a snapshot event to the dashboard state."""
    if event_name == "Commander":
        state.commander.name = entry.get("Name", "")
        state.commander.fid = entry.get("FID", "")

    elif event_name == "LoadGame":
        state.commander.name = state.commander.name or entry.get("Commander", "")
        state.commander.fid = state.commander.fid or entry.get("FID", "")
        state.commander.ship = entry.get("Ship", "")
        state.commander.ship_localised = entry.get("Ship_Localised", entry.get("Ship", ""))
        state.commander.ship_name = entry.get("ShipName", "")
        state.commander.ship_ident = entry.get("ShipIdent", "")
        state.commander.credits = entry.get("Credits", 0)
        state.commander.game_mode = entry.get("GameMode", "")
        state.commander.game_version = entry.get("gameversion", "")
        state.commander.horizons = entry.get("Horizons", False)
        state.commander.odyssey = entry.get("Odyssey", False)

    elif event_name == "Powerplay":
        state.powerplay.power = entry.get("Power", "")
        state.powerplay.rank = entry.get("Rank", 0)
        state.powerplay.merits = entry.get("Merits", 0)
        state.powerplay.time_pledged_seconds = entry.get("TimePledged", 0)
        state.last_parsed_timestamp = entry.get("timestamp", "")

    elif event_name == "Rank":
        state.ranks.combat = entry.get("Combat", 0)
        state.ranks.trade = entry.get("Trade", 0)
        state.ranks.explore = entry.get("Explore", 0)
        state.ranks.soldier = entry.get("Soldier", 0)
        state.ranks.exobiologist = entry.get("Exobiologist", 0)
        state.ranks.empire = entry.get("Empire", 0)
        state.ranks.federation = entry.get("Federation", 0)
        state.ranks.cqc = entry.get("CQC", 0)

    elif event_name == "Progress":
        state.progress.combat = entry.get("Combat", 0)
        state.progress.trade = entry.get("Trade", 0)
        state.progress.explore = entry.get("Explore", 0)
        state.progress.soldier = entry.get("Soldier", 0)
        state.progress.exobiologist = entry.get("Exobiologist", 0)
        state.progress.empire = entry.get("Empire", 0)
        state.progress.federation = entry.get("Federation", 0)
        state.progress.cqc = entry.get("CQC", 0)

    elif event_name == "Reputation":
        state.reputation.empire = entry.get("Empire", 0.0)
        state.reputation.federation = entry.get("Federation", 0.0)
        state.reputation.independent = entry.get("Independent", 0.0)
        state.reputation.alliance = entry.get("Alliance", 0.0)

    elif event_name == "Location":
        state.current_system = _parse_system_visit(entry)

    elif event_name == "Statistics":
        state.statistics = entry

    elif event_name == "Missions":
        pass  # Active missions snapshot - could be used later


def _apply_activity_event(entry: dict, event_name: str, state: DashboardState):
    """Apply an activity event to the dashboard state."""
    if event_name == "PowerplayMerits":
        evt = PowerplayMeritEvent(
            timestamp=entry.get("timestamp", ""),
            merits_gained=entry.get("MeritsGained", 0),
            total_merits=entry.get("TotalMerits", 0),
        )
        state.merit_events.append(evt)

    elif event_name == "PowerplayCollect":
        evt = PowerplayCargoEvent(
            timestamp=entry.get("timestamp", ""),
            event_type="Collect",
            power=entry.get("Power", ""),
            cargo_type=entry.get("Type", ""),
            cargo_type_localised=entry.get("Type_Localised", ""),
            count=entry.get("Count", 0),
        )
        state.cargo_events.append(evt)

    elif event_name == "PowerplayDeliver":
        evt = PowerplayCargoEvent(
            timestamp=entry.get("timestamp", ""),
            event_type="Deliver",
            power=entry.get("Power", ""),
            cargo_type=entry.get("Type", ""),
            cargo_type_localised=entry.get("Type_Localised", ""),
            count=entry.get("Count", 0),
        )
        state.cargo_events.append(evt)

    elif event_name == "PowerplayRank":
        evt = PowerplayRankEvent(
            timestamp=entry.get("timestamp", ""),
            power=entry.get("Power", ""),
            rank=entry.get("Rank", 0),
        )
        state.rank_events.append(evt)

    elif event_name == "PowerplayJoin":
        # Record the pledge timestamp
        state.powerplay.pledge_timestamp = entry.get("timestamp", "")
        state.powerplay.power = state.powerplay.power or entry.get("Power", "")

    elif event_name == "FSDJump":
        sv = _parse_system_visit(entry)
        state.systems_visited.append(sv)
        state.current_system = sv

    elif event_name in ("MissionAccepted", "MissionCompleted",
                        "MissionAbandoned", "MissionFailed"):
        status_map = {
            "MissionAccepted": "Accepted",
            "MissionCompleted": "Completed",
            "MissionAbandoned": "Abandoned",
            "MissionFailed": "Failed",
        }
        evt = MissionEvent(
            timestamp=entry.get("timestamp", ""),
            event_type=status_map[event_name],
            mission_id=entry.get("MissionID", 0),
            name=entry.get("Name", ""),
            localised_name=entry.get("LocalisedName", entry.get("Name_Localised", "")),
            faction=entry.get("Faction", ""),
            target_faction=entry.get("TargetFaction", ""),
            destination_system=entry.get("DestinationSystem", ""),
            destination_station=entry.get("DestinationStation", ""),
            reward=entry.get("Reward", 0),
            influence=str(entry.get("Influence", "")),
            expiry=entry.get("Expiry", ""),
        )
        state.mission_events.append(evt)


def _parse_latest_state(files: list, state: DashboardState):
    """Phase 1: Read newest file(s) backwards to populate snapshot fields."""
    needed = set(SNAPSHOT_EVENTS)

    for filepath in files:
        if not needed:
            break
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    event_name = _extract_event_fast(line)
                    if event_name not in needed:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    _apply_snapshot_event(entry, event_name, state)
                    needed.discard(event_name)
                    if not needed:
                        break
        except (OSError, IOError):
            continue


def _parse_activity_history(files: list, state: DashboardState):
    """Phase 2: Scan recent files chronologically for activity events."""
    for filepath in files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    event_name = _extract_event_fast(line)
                    if event_name not in ACTIVITY_EVENTS:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    _apply_activity_event(entry, event_name, state)
        except (OSError, IOError):
            continue


def parse_journals(journal_dir: str = JOURNAL_DIR,
                   history_days: int = DEFAULT_HISTORY_DAYS) -> DashboardState:
    """Parse Elite Dangerous journal files and return a DashboardState.

    Phase 1: Read the most recent file(s) for snapshot state (fast).
    Phase 2: Scan recent files for activity history (configurable window).
    """
    state = DashboardState()
    start_time = time.monotonic()

    # Discover all journal files, sorted newest-first
    pattern = os.path.join(journal_dir, "Journal.*.log")
    all_files = sorted(glob.glob(pattern), reverse=True)
    state.total_journal_files = len(all_files)

    if not all_files:
        state.parse_duration_seconds = time.monotonic() - start_time
        return state

    # Phase 1: Latest snapshot state
    _parse_latest_state(all_files, state)

    # Phase 2: Activity history from recent files
    cutoff = _compute_cutoff_filename(history_days)
    # Filter to files within the history window (compare basenames)
    recent_files = [f for f in all_files
                    if os.path.basename(f) >= cutoff]
    # Sort chronologically for history building
    recent_files.sort()
    _parse_activity_history(recent_files, state)

    state.journal_files_parsed = len(recent_files)
    state.parse_duration_seconds = time.monotonic() - start_time

    return state


# CLI test: run this module directly to verify parsing
if __name__ == "__main__":
    print(f"Parsing journals from: {JOURNAL_DIR}")
    print(f"History window: {DEFAULT_HISTORY_DAYS} days")
    print()

    result = parse_journals()

    print(f"=== Parse Results ===")
    print(f"Duration: {result.parse_duration_seconds:.2f}s")
    print(f"Files: {result.journal_files_parsed} parsed / {result.total_journal_files} total")
    print()
    print(f"=== Commander ===")
    print(f"Name: CMDR {result.commander.name}")
    print(f"Ship: {result.commander.ship_localised} '{result.commander.ship_name}'")
    print(f"Credits: {result.commander.credits:,}")
    print()
    print(f"=== PowerPlay ===")
    print(f"Power: {result.powerplay.power}")
    print(f"Rank: {result.powerplay.rank}")
    print(f"Merits: {result.powerplay.merits:,}")
    days = result.powerplay.time_pledged_seconds // 86400
    hours = (result.powerplay.time_pledged_seconds % 86400) // 3600
    print(f"Time Pledged: {days} days, {hours} hours")
    print(f"Pledge Date: {result.powerplay.pledge_timestamp}")
    print()
    print(f"=== Current System ===")
    if result.current_system:
        cs = result.current_system
        print(f"System: {cs.star_system}")
        print(f"PP State: {cs.powerplay_state}")
        print(f"Controlling Power: {cs.controlling_power}")
    else:
        print("No current system data")
    print()
    print(f"=== Reputation ===")
    print(f"Federation: {result.reputation.federation:.1f}%")
    print(f"Alliance: {result.reputation.alliance:.1f}%")
    print(f"Empire: {result.reputation.empire:.1f}%")
    print(f"Independent: {result.reputation.independent:.1f}%")
    print()
    print(f"=== Activity Summary ===")
    print(f"Merit events: {len(result.merit_events)}")
    print(f"Cargo events: {len(result.cargo_events)}")
    print(f"Rank events: {len(result.rank_events)}")
    print(f"Systems visited: {len(result.systems_visited)}")
    print(f"Mission events: {len(result.mission_events)}")
