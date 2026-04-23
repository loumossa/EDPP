"""EDPP Configuration - Constants, paths, and lookup tables."""

import os

# Journal file location
JOURNAL_DIR = r"C:\Users\Lou\Saved Games\Frontier Developments\Elite Dangerous"
JOURNAL_GLOB = "Journal.*.log"

# Events we care about (all others are skipped for speed)
SNAPSHOT_EVENTS = frozenset({
    "Commander", "LoadGame",
    "Powerplay", "Rank", "Progress", "Reputation",
    "Statistics", "Location", "Missions",
})

ACTIVITY_EVENTS = frozenset({
    "PowerplayMerits", "PowerplayCollect", "PowerplayDeliver", "PowerplayRank",
    "PowerplayJoin",
    "FSDJump",
    "MissionAccepted", "MissionCompleted", "MissionAbandoned", "MissionFailed",
})

RELEVANT_EVENTS = SNAPSHOT_EVENTS | ACTIVITY_EVENTS

# Default history window for activity events
DEFAULT_HISTORY_DAYS = 30

# Rank name lookup tables
COMBAT_RANKS = {
    0: "Harmless", 1: "Mostly Harmless", 2: "Novice", 3: "Competent",
    4: "Expert", 5: "Master", 6: "Dangerous", 7: "Deadly", 8: "Elite",
    9: "Elite I", 10: "Elite II", 11: "Elite III", 12: "Elite IV", 13: "Elite V",
}

TRADE_RANKS = {
    0: "Penniless", 1: "Mostly Penniless", 2: "Peddler", 3: "Dealer",
    4: "Merchant", 5: "Broker", 6: "Entrepreneur", 7: "Tycoon", 8: "Elite",
    9: "Elite I", 10: "Elite II", 11: "Elite III", 12: "Elite IV", 13: "Elite V",
}

EXPLORE_RANKS = {
    0: "Aimless", 1: "Mostly Aimless", 2: "Scout", 3: "Surveyor",
    4: "Trailblazer", 5: "Pathfinder", 6: "Ranger", 7: "Pioneer", 8: "Elite",
    9: "Elite I", 10: "Elite II", 11: "Elite III", 12: "Elite IV", 13: "Elite V",
}

SOLDIER_RANKS = {
    0: "Defenceless", 1: "Mostly Defenceless", 2: "Rookie", 3: "Soldier",
    4: "Gunslinger", 5: "Warrior", 6: "Gladiator", 7: "Deadeye", 8: "Elite",
    9: "Elite I", 10: "Elite II", 11: "Elite III", 12: "Elite IV", 13: "Elite V",
}

EXOBIOLOGY_RANKS = {
    0: "Directionless", 1: "Mostly Directionless", 2: "Compiler", 3: "Collector",
    4: "Cataloguer", 5: "Taxonomist", 6: "Ecologist", 7: "Geneticist", 8: "Elite",
    9: "Elite I", 10: "Elite II", 11: "Elite III", 12: "Elite IV", 13: "Elite V",
}

CQC_RANKS = {
    0: "Helpless", 1: "Mostly Helpless", 2: "Amateur", 3: "Semi Professional",
    4: "Professional", 5: "Champion", 6: "Hero", 7: "Legend", 8: "Elite",
    9: "Elite I", 10: "Elite II", 11: "Elite III", 12: "Elite IV", 13: "Elite V",
}

FEDERATION_RANKS = {
    0: "None", 1: "Recruit", 2: "Cadet", 3: "Midshipman", 4: "Petty Officer",
    5: "Chief Petty Officer", 6: "Warrant Officer", 7: "Ensign", 8: "Lieutenant",
    9: "Lt. Commander", 10: "Post Commander", 11: "Post Captain",
    12: "Rear Admiral", 13: "Vice Admiral", 14: "Admiral",
}

EMPIRE_RANKS = {
    0: "None", 1: "Outsider", 2: "Serf", 3: "Master", 4: "Squire",
    5: "Knight", 6: "Lord", 7: "Baron", 8: "Viscount", 9: "Count",
    10: "Earl", 11: "Marquis", 12: "Duke", 13: "Prince", 14: "King",
}

# Map rank field names to their lookup tables
RANK_TABLES = {
    "combat": COMBAT_RANKS,
    "trade": TRADE_RANKS,
    "explore": EXPLORE_RANKS,
    "soldier": SOLDIER_RANKS,
    "exobiologist": EXOBIOLOGY_RANKS,
    "cqc": CQC_RANKS,
    "federation": FEDERATION_RANKS,
    "empire": EMPIRE_RANKS,
}

# Window appearance
APP_TITLE = "EDPP - Elite Dangerous PowerPlay Dashboard"
WINDOW_MIN_WIDTH = 1100
WINDOW_MIN_HEIGHT = 700
WINDOW_DEFAULT_GEOMETRY = "1200x800"
