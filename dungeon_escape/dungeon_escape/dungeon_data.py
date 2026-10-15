"""Static game data for Dungeon Escape.

Coordinates are TUPLES (x, y).  Templates and rooms are DICTIONARIES.
game_state.py and dungeon_map.py turn this data into a playable dungeon.
"""

GRID_WIDTH = 4
GRID_HEIGHT = 4
START_ROOM = (0, 0)           # tuple: the room where the hero wakes up
BOSS_ROOM = (3, 3)            # tuple: the Warden's Chamber
ARTIFACTS_REQUIRED = 3        # unique artifacts needed to open the boss door
LANTERN_CHARGES = 3
LANTERN_DEPTH = 2             # how many rooms deep the lantern reveals
POTION_HEAL = 25
CLEAR_HEAL = 8                # HP regained when you clear a room of monsters

PLAYER_START = {"name": "Hero", "hp": 60, "max_hp": 60,
                "base_attack": 5, "potions": 1}

MONSTER_TEMPLATES = {
    "Bat":            {"hp": 9,  "attack": 4},
    "Goblin":         {"hp": 15, "attack": 5},
    "Spider":         {"hp": 14, "attack": 6},
    "Skeleton":       {"hp": 20, "attack": 6},
    "Wraith":         {"hp": 24, "attack": 7},
    "Orc":            {"hp": 30, "attack": 8},
    "Dungeon Warden": {"hp": 70, "attack": 11, "boss": True},
}

EQUIPMENT = {
    "Rusty Dagger":      {"kind": "weapon", "power": 2},
    "Iron Sword":        {"kind": "weapon", "power": 4},
    "Steel Axe":         {"kind": "weapon", "power": 6},
    "Runed Sword":       {"kind": "weapon", "power": 8},
    "Leather Vest":      {"kind": "armor", "power": 1},
    "Chain Mail":        {"kind": "armor", "power": 3},
    "Dragon Scale Mail": {"kind": "armor", "power": 5},
}

# Rooms are keyed by their (x, y) tuple.  x grows East, y grows South.
ROOM_INFO = {
    (0, 0): {"name": "Entrance Hall",
             "description": "Cold torches flank the gate that slammed shut behind you. Something glints by the wall.",
             "monsters": [], "equipment": "Rusty Dagger"},
    (1, 0): {"name": "Armory",
             "description": "Racks of rotten spears. A goblin guards the one blade that is still sharp.",
             "monsters": ["Goblin"], "equipment": "Iron Sword"},
    (2, 0): {"name": "Crypt",
             "description": "Stone coffins stand open. A red gem pulses in a skeleton's grip.",
             "monsters": ["Skeleton", "Bat"], "artifact": "Ruby Eye", "potions": 1},
    (3, 0): {"name": "Library",
             "description": "Shelves sag under moldy scrolls. Bats nest among the rafters.",
             "monsters": ["Bat", "Bat"], "artifact": "Silver Key"},
    (0, 1): {"name": "Dark Hallway",
             "description": "A long corridor. Your torch barely reaches the walls.",
             "monsters": ["Bat"], "potions": 1},
    (1, 1): {"name": "Goblin Den",
             "description": "Stolen goods and gnawed bones cover the floor.",
             "monsters": ["Goblin", "Goblin", "Bat"], "equipment": "Leather Vest"},
    (2, 1): {"name": "Fungus Cave",
             "description": "Glowing mushrooms light a cavern draped in silk.",
             "monsters": ["Spider"], "potions": 1},
    (3, 1): {"name": "Spider Nest",
             "description": "Webs thick as rope hide a pale, moon-shaped crest.",
             "monsters": ["Spider", "Spider", "Bat"], "artifact": "Moon Crest"},
    (0, 2): {"name": "Cellar",
             "description": "Barrels of sour wine. A skeleton still guards the cellar's best axe.",
             "monsters": ["Skeleton"], "equipment": "Steel Axe"},
    (1, 2): {"name": "Barracks",
             "description": "Rows of cots. An orc captain sleeps in a chain mail shirt.",
             "monsters": ["Orc"], "equipment": "Chain Mail"},
    (2, 2): {"name": "Flooded Hall",
             "description": "Knee-deep water. A wraith drifts over a drowned supply crate.",
             "monsters": ["Wraith"], "potions": 1},
    (3, 2): {"name": "Forge",
             "description": "The anvil still glows. An orc smith hammers a rune-etched sword.",
             "monsters": ["Orc", "Goblin"], "equipment": "Runed Sword"},
    (0, 3): {"name": "Prison Cells",
             "description": "Empty cells. Skeleton guards hold a second silver key.",
             "monsters": ["Skeleton", "Skeleton"], "artifact": "Silver Key"},
    (1, 3): {"name": "Bone Pit",
             "description": "Scales of some old dragon gleam among the bones.",
             "monsters": ["Wraith", "Bat"], "equipment": "Dragon Scale Mail"},
    (2, 3): {"name": "Treasury",
             "description": "Most chests are empty. An orc and a skeleton guard what is left.",
             "monsters": ["Orc", "Skeleton"], "potions": 2},
    (3, 3): {"name": "Warden's Chamber",
             "description": "A vast hall. The Dungeon Warden rises from his throne, keys rattling at his belt.",
             "monsters": ["Dungeon Warden", "Skeleton"]},
}

# Corridors between rooms: pairs of (x, y) tuples.
CONNECTIONS = [
    ((0, 0), (1, 0)), ((0, 0), (0, 1)),
    ((1, 0), (2, 0)), ((1, 0), (1, 1)),
    ((2, 0), (3, 0)), ((2, 0), (2, 1)),
    ((3, 0), (3, 1)),
    ((0, 1), (1, 1)), ((0, 1), (0, 2)),
    ((1, 1), (1, 2)),
    ((2, 1), (2, 2)),
    ((3, 1), (3, 2)),
    ((0, 2), (0, 3)),
    ((1, 2), (1, 3)), ((1, 2), (2, 2)),
    ((2, 2), (2, 3)),
    ((3, 2), (3, 3)),
    ((0, 3), (1, 3)),
    ((2, 3), (3, 3)),
]

DIRECTION_OFFSETS = {"North": (0, -1), "East": (1, 0),
                     "South": (0, 1), "West": (-1, 0)}
OPPOSITE = {"North": "South", "South": "North", "East": "West", "West": "East"}


def make_monster(kind):
    """Create a fresh monster dictionary from its template."""
    template = MONSTER_TEMPLATES[kind]
    return {"kind": kind, "name": kind, "hp": template["hp"],
            "max_hp": template["hp"], "attack": template["attack"],
            "boss": template.get("boss", False)}


def make_equipment(name):
    """Create an equipment dictionary: name, kind (weapon/armor), power."""
    template = EQUIPMENT[name]
    return {"name": name, "kind": template["kind"], "power": template["power"]}
