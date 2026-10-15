"""Game rules and state for Dungeon Escape (no Tkinter in this file).

The interface (ui.py) calls the public methods below and then shows
state.pop_messages().  Keeping rules apart from the screen lets us test
the whole game without opening a window.
"""

import random

from dungeon_data import (ARTIFACTS_REQUIRED, BOSS_ROOM, LANTERN_CHARGES,
                          LANTERN_DEPTH, PLAYER_START, POTION_HEAL,
                          CLEAR_HEAL, START_ROOM, make_equipment)
from dungeon_map import build_rooms, scout_rooms
from sorting import bubble_sort, insertion_insert, selection_sort


def monster_hp(monster):
    """Sort key: a monster's current HP."""
    return monster["hp"]


def item_power(item):
    """Sort key: a piece of equipment's power."""
    return item["power"]


class GameState:
    """Everything that changes while the player explores the dungeon."""

    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.reset()

    def reset(self):
        self.status = "playing"                  # "playing", "won" or "lost"
        self.player = dict(PLAYER_START)         # DICTIONARY of hero stats
        self.rooms = build_rooms()               # {(x, y): room dictionary}
        self.position = START_ROOM               # TUPLE (x, y)
        self.previous_position = START_ROOM      # TUPLE, used by flee()
        self.visited = {START_ROOM}              # SET of room tuples
        self.revealed = set()                    # rooms lit by the lantern
        self.artifacts = set()                   # SET: unique artifacts only
        self.equipment = []                      # kept ordered by power
        self.lantern_charges = LANTERN_CHARGES
        self.turns = 0
        self.score = 0
        self.kills = 0
        self.messages = []                       # (tag, text) tuples
        self._say("You wake in a sealed dungeon. Find 3 artifacts, open the "
                  "Warden's Chamber and escape!", "info")

    # ----- messages ---------------------------------------------------------
    def _say(self, text, tag="info"):
        self.messages.append((tag, text))

    def pop_messages(self):
        """Hand the pending messages to the interface and clear them."""
        pending, self.messages = self.messages, []
        return pending

    # ----- simple questions the interface asks ------------------------------
    def room(self):
        return self.rooms[self.position]

    def monsters_here(self):
        return self.room()["monsters"]

    def in_combat(self):
        return len(self.monsters_here()) > 0

    def best_equipped(self, kind):
        """Strongest weapon/armor.  The pack is ordered, so scan from the end."""
        for item in reversed(self.equipment):
            if item["kind"] == kind:
                return item
        return None

    def attack_power(self):
        weapon = self.best_equipped("weapon")
        return self.player["base_attack"] + (weapon["power"] if weapon else 0)

    def armor_power(self):
        armor = self.best_equipped("armor")
        return armor["power"] if armor else 0

    # ----- BUBBLE SORT: rank the monsters in the room by HP -----------------
    def ranked_monsters(self, announce=False):
        stats = {"comparisons": 0, "swaps": 0}
        ranked = bubble_sort(self.monsters_here(), key=monster_hp,
                             descending=True, stats=stats)
        if announce and len(ranked) > 1:
            self._say(f"[Bubble Sort] Ranked {len(ranked)} monsters by HP: "
                      f"{stats['comparisons']} comparisons, "
                      f"{stats['swaps']} swaps.", "sort")
        return ranked

    # ----- movement ---------------------------------------------------------
    def move(self, direction):
        if self.status != "playing":
            return False
        if self.in_combat():
            self._say("Monsters block the way! Defeat them or flee (F).", "bad")
            return False
        destination = self.room()["exits"].get(direction)
        if destination is None:
            self._say(f"There is no exit to the {direction}.", "bad")
            return False
        if destination == BOSS_ROOM and len(self.artifacts) < ARTIFACTS_REQUIRED:
            self._say(f"The Warden's door is sealed. It needs "
                      f"{ARTIFACTS_REQUIRED} different artifacts "
                      f"(you hold {len(self.artifacts)}).", "bad")
            return False
        self._enter(destination)
        return True

    def _enter(self, destination):
        self.previous_position = self.position
        self.position = destination
        first_visit = destination not in self.visited
        self.visited.add(destination)
        self.turns += 1
        room = self.room()
        if first_visit:
            self._say(f"{room['name']}: {room['description']}", "info")
        else:
            self._say(f"You return to the {room['name']}.", "info")
        if self.monsters_here():
            names = ", ".join(m["name"] for m in self.monsters_here())
            self._say(f"Monsters attack: {names}!", "bad")
            self.ranked_monsters(announce=True)

    def flee(self):
        if self.status != "playing":
            return False
        if not self.in_combat():
            self._say("There is nothing to flee from.", "bad")
            return False
        self._say("You break away, but the monsters strike as you run!", "bad")
        self._monsters_strike()
        if self.status != "playing":
            return True
        self.position = self.previous_position
        self.turns += 1
        self._say(f"You retreat to the {self.room()['name']}.", "info")
        return True

    # ----- combat -----------------------------------------------------------
    def _is_here(self, monster):
        return any(m is monster for m in self.monsters_here())

    def _player_damage(self):
        return self.attack_power() + self.rng.randint(0, 2)

    def attack(self, monster):
        """Attack one chosen monster."""
        if not self._require_combat():
            return False
        if monster is None or not self._is_here(monster):
            self._say("Pick a monster from the list first.", "bad")
            return False
        self._hit_monster(monster, self._player_damage())
        self._end_player_turn()
        return True

    # ----- SELECTION SORT: find the weakest monster -------------------------
    def strike_weakest(self):
        """Use Selection Sort to find the weakest monster, then hit it."""
        if not self._require_combat():
            return False
        stats = {"comparisons": 0, "swaps": 0}
        by_weakness = selection_sort(self.monsters_here(), key=monster_hp,
                                     descending=False, stats=stats)
        weakest = by_weakness[0]
        self._say(f"[Selection Sort] {stats['comparisons']} comparisons: "
                  f"weakest is {weakest['name']} ({weakest['hp']} HP).", "sort")
        self._hit_monster(weakest, self._player_damage())
        self._end_player_turn()
        return True

    def _require_combat(self):
        if self.status != "playing":
            return False
        if not self.in_combat():
            self._say("There is nothing to fight here.", "bad")
            return False
        return True

    def _hit_monster(self, monster, damage):
        monster["hp"] -= damage
        self._say(f"You hit the {monster['name']} for {damage} damage.", "good")
        if monster["hp"] > 0:
            return
        room = self.room()
        room["monsters"] = [m for m in room["monsters"] if m is not monster]
        self.kills += 1
        self.score += monster["max_hp"]
        self._say(f"The {monster['name']} is defeated! "
                  f"(+{monster['max_hp']} score)", "good")
        if monster["boss"]:
            self._win()
        elif not room["monsters"]:
            healed = self._heal(CLEAR_HEAL)
            self._say(f"The room falls silent and you catch your breath "
                      f"(+{healed} HP). Search it (E) or move on.", "info")

    def _end_player_turn(self):
        self.turns += 1
        if self.status != "playing":
            return
        if self.monsters_here():
            self._monsters_strike()
            if self.status == "playing":
                self.ranked_monsters(announce=True)

    def _monsters_strike(self):
        armor = self.armor_power()
        for monster in self.monsters_here():
            damage = max(1, monster["attack"] - armor + self.rng.randint(-1, 1))
            self.player["hp"] -= damage
            self._say(f"The {monster['name']} hits you for {damage}.", "bad")
            if self.player["hp"] <= 0:
                self.player["hp"] = 0
                self.status = "lost"
                self._say("You collapse. The dungeon claims another soul.", "bad")
                return

    def _heal(self, amount):
        """Heal up to `amount` HP and return how much was really restored."""
        missing = self.player["max_hp"] - self.player["hp"]
        healed = min(amount, missing)
        self.player["hp"] += healed
        return healed

    def use_potion(self):
        if self.status != "playing":
            return False
        if self.player["potions"] <= 0:
            self._say("You have no potions left.", "bad")
            return False
        if self.player["hp"] >= self.player["max_hp"]:
            self._say("You are already at full health.", "bad")
            return False
        self.player["potions"] -= 1
        healed = self._heal(POTION_HEAL)
        self._say(f"You drink a potion and recover {healed} HP.", "good")
        self._end_player_turn()
        return True

    # ----- searching rooms --------------------------------------------------
    def search_room(self):
        if self.status != "playing":
            return False
        if self.in_combat():
            self._say("Too dangerous to search while monsters are here.", "bad")
            return False
        room = self.room()
        if room["searched"]:
            self._say("You already searched this room.", "bad")
            return False
        room["searched"] = True
        self.turns += 1
        found_something = False
        if room["equipment"]:
            self._collect_equipment(room["equipment"])
            found_something = True
        if room["artifact"]:
            self._collect_artifact(room["artifact"])
            found_something = True
        if room["potions"]:
            self.player["potions"] += room["potions"]
            self._say(f"You find {room['potions']} potion(s).", "good")
            found_something = True
        if not found_something:
            self._say("Nothing here but dust and old bones.", "info")
        return True

    # ----- INSERTION SORT: new gear slides into an ordered pack -------------
    def _collect_equipment(self, name):
        item = make_equipment(name)
        stats = {"comparisons": 0, "shifts": 0}
        self.equipment = insertion_insert(self.equipment, item, key=item_power,
                                          stats=stats)
        slot = 1
        for i, owned in enumerate(self.equipment):
            if owned is item:
                slot = i + 1
        self._say(f"You find {name} ({item['kind']}, power {item['power']}).",
                  "good")
        self._say(f"[Insertion Sort] Placed in pack slot {slot} of "
                  f"{len(self.equipment)}: {stats['comparisons']} comparisons, "
                  f"{stats['shifts']} shifts.", "sort")
        if self.best_equipped(item["kind"]) is item:
            self._say(f"It is your new best {item['kind']}!", "good")

    # ----- SET: artifacts can never be counted twice ------------------------
    def _collect_artifact(self, name):
        before = len(self.artifacts)
        self.artifacts.add(name)
        if len(self.artifacts) == before:
            self.score += 10
            self._say(f"A second {name}! Your artifact set ignores duplicates "
                      f"(+10 score).", "info")
            return
        self.score += 50
        self._say(f"Artifact found: {name}! ({len(self.artifacts)}/"
                  f"{ARTIFACTS_REQUIRED} unique)", "good")
        if len(self.artifacts) == ARTIFACTS_REQUIRED:
            self._say("A deep rumble shakes the dungeon: the Warden's "
                      "Chamber is unlocked!", "good")

    # ----- RECURSION: the lantern reveals connected rooms -------------------
    def use_lantern(self):
        if self.status != "playing":
            return False
        if self.in_combat():
            self._say("You cannot work the lantern in the middle of a fight.",
                      "bad")
            return False
        if self.lantern_charges <= 0:
            self._say("The lantern is out of oil.", "bad")
            return False
        self.lantern_charges -= 1
        reached = scout_rooms(self.rooms, self.position, LANTERN_DEPTH)
        newly_seen = set(reached) - self.visited - self.revealed
        self.revealed |= set(reached)
        self.turns += 1
        self._say(f"[Recursion] Light spreads {LANTERN_DEPTH} rooms deep "
                  f"through the corridors and reveals {len(newly_seen)} new "
                  f"room(s).", "sort")
        return True

    # ----- ending -----------------------------------------------------------
    def _win(self):
        self.status = "won"
        self.score += 100
        self._say("The Dungeon Warden crumbles. The gate swings open: "
                  "you are free!", "good")
