"""EDPP Data Models - Dataclasses for all parsed journal state."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CommanderInfo:
    name: str = ""
    fid: str = ""
    ship: str = ""
    ship_localised: str = ""
    ship_name: str = ""
    ship_ident: str = ""
    credits: int = 0
    game_mode: str = ""
    game_version: str = ""
    horizons: bool = False
    odyssey: bool = False


@dataclass
class PowerplayStatus:
    power: str = ""
    rank: int = 0
    merits: int = 0
    time_pledged_seconds: int = 0
    pledge_timestamp: str = ""


@dataclass
class PowerplayMeritEvent:
    timestamp: str = ""
    merits_gained: int = 0
    total_merits: int = 0


@dataclass
class PowerplayCargoEvent:
    timestamp: str = ""
    event_type: str = ""          # "Collect" or "Deliver"
    power: str = ""
    cargo_type: str = ""
    cargo_type_localised: str = ""
    count: int = 0


@dataclass
class PowerplayRankEvent:
    timestamp: str = ""
    power: str = ""
    rank: int = 0


@dataclass
class SystemVisit:
    timestamp: str = ""
    star_system: str = ""
    system_address: int = 0
    star_pos: list = field(default_factory=list)
    controlling_power: str = ""
    powers: list = field(default_factory=list)
    powerplay_state: str = ""
    powerplay_state_control_progress: float = 0.0
    powerplay_state_reinforcement: int = 0
    powerplay_state_undermining: int = 0
    conflict_progress: list = field(default_factory=list)
    allegiance: str = ""
    economy: str = ""
    economy_localised: str = ""
    government: str = ""
    government_localised: str = ""
    security: str = ""
    security_localised: str = ""
    population: int = 0
    controlling_faction: str = ""


@dataclass
class RankInfo:
    combat: int = 0
    trade: int = 0
    explore: int = 0
    soldier: int = 0
    exobiologist: int = 0
    empire: int = 0
    federation: int = 0
    cqc: int = 0


@dataclass
class ProgressInfo:
    combat: int = 0
    trade: int = 0
    explore: int = 0
    soldier: int = 0
    exobiologist: int = 0
    empire: int = 0
    federation: int = 0
    cqc: int = 0


@dataclass
class ReputationInfo:
    empire: float = 0.0
    federation: float = 0.0
    independent: float = 0.0
    alliance: float = 0.0


@dataclass
class MissionEvent:
    timestamp: str = ""
    event_type: str = ""         # "Accepted", "Completed", "Abandoned", "Failed"
    mission_id: int = 0
    name: str = ""
    localised_name: str = ""
    faction: str = ""
    target_faction: str = ""
    destination_system: str = ""
    destination_station: str = ""
    reward: int = 0
    influence: str = ""
    expiry: str = ""


@dataclass
class DashboardState:
    """Top-level container holding all parsed state."""
    commander: CommanderInfo = field(default_factory=CommanderInfo)
    powerplay: PowerplayStatus = field(default_factory=PowerplayStatus)
    ranks: RankInfo = field(default_factory=RankInfo)
    progress: ProgressInfo = field(default_factory=ProgressInfo)
    reputation: ReputationInfo = field(default_factory=ReputationInfo)

    # Activity history lists
    merit_events: list = field(default_factory=list)
    cargo_events: list = field(default_factory=list)
    rank_events: list = field(default_factory=list)
    systems_visited: list = field(default_factory=list)
    mission_events: list = field(default_factory=list)

    # Current location (most recent FSDJump or Location)
    current_system: Optional[SystemVisit] = None

    # Statistics (raw dict - too complex/variable for a dataclass)
    statistics: dict = field(default_factory=dict)

    # Parse metadata
    last_parsed_timestamp: str = ""
    journal_files_parsed: int = 0
    total_journal_files: int = 0
    parse_duration_seconds: float = 0.0
