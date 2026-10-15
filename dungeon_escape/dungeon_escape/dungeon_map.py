"""Builds the dungeon graph and explores it with recursion."""

from dungeon_data import (CONNECTIONS, DIRECTION_OFFSETS, OPPOSITE, ROOM_INFO,
                          make_monster)

# (dx, dy) tuple -> "North"/"East"/...  (reverse of DIRECTION_OFFSETS)
OFFSET_TO_DIRECTION = {offset: name for name, offset in DIRECTION_OFFSETS.items()}


def _label_duplicates(monsters):
    """Rename repeated monsters so the player can tell them apart (Goblin A/B)."""
    totals = {}
    for monster in monsters:
        totals[monster["kind"]] = totals.get(monster["kind"], 0) + 1
    seen = {}
    for monster in monsters:
        kind = monster["kind"]
        if totals[kind] > 1:
            seen[kind] = seen.get(kind, 0) + 1
            monster["name"] = kind + " " + "ABCDE"[seen[kind] - 1]


def build_rooms():
    """Return {(x, y): room dictionary} with exits wired between rooms."""
    rooms = {}
    for position, info in ROOM_INFO.items():
        monsters = [make_monster(kind) for kind in info["monsters"]]
        _label_duplicates(monsters)
        rooms[position] = {
            "name": info["name"],
            "description": info["description"],
            "monsters": monsters,
            "equipment": info.get("equipment"),
            "artifact": info.get("artifact"),
            "potions": info.get("potions", 0),
            "searched": False,
            "exits": {},                       # direction name -> (x, y) tuple
        }
    for first, second in CONNECTIONS:
        offset = (second[0] - first[0], second[1] - first[1])
        direction = OFFSET_TO_DIRECTION[offset]
        rooms[first]["exits"][direction] = second
        rooms[second]["exits"][OPPOSITE[direction]] = first
    return rooms


# --------------------------------------------------------------------------
# RECURSION: the lantern explores connected rooms.
# Game use: GameState.use_lantern() reveals every room within LANTERN_DEPTH.
# --------------------------------------------------------------------------
def scout_rooms(rooms, position, depth, reached=None):
    """Recursively explore rooms connected to `position`.

    Returns {room tuple: steps of light left when the room was reached}.

    Base cases (the calls stop here):
      1. depth < 0   - the light has run out;
      2. the room was already reached with at least as much light left.
    Progress: every recursive call uses depth - 1, so depth always shrinks
    toward the first base case and the recursion must end.

    Trace for scout_rooms(rooms, (0, 0), 1):
        (0, 0) depth 1 -> marks (0, 0), then calls its neighbours at depth 0
        (1, 0) depth 0 -> marks (1, 0), calls neighbours at depth -1 -> stop
        (0, 1) depth 0 -> marks (0, 1), calls neighbours at depth -1 -> stop
    """
    if reached is None:
        reached = {}
    if depth < 0:                                   # base case 1
        return reached
    if position in reached and reached[position] >= depth:   # base case 2
        return reached
    reached[position] = depth
    for neighbour in rooms[position]["exits"].values():
        scout_rooms(rooms, neighbour, depth - 1, reached)   # recursive call
    return reached
