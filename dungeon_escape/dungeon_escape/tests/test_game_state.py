"""Tests for the dungeon map, recursion, and game rules (no window needed)."""

import unittest
from collections import deque

from dungeon_data import (ARTIFACTS_REQUIRED, BOSS_ROOM, LANTERN_CHARGES,
                          OPPOSITE, START_ROOM, make_monster)
from dungeon_map import build_rooms, scout_rooms
from game_state import GameState


def messages_text(game):
    return " ".join(text for tag, text in game.messages)


class DungeonMapTests(unittest.TestCase):
    def setUp(self):
        self.rooms = build_rooms()

    def test_sixteen_rooms_keyed_by_tuples(self):
        self.assertEqual(len(self.rooms), 16)
        for position in self.rooms:
            self.assertIsInstance(position, tuple)
            self.assertEqual(len(position), 2)

    def test_exits_are_two_way(self):
        for position, room in self.rooms.items():
            for direction, neighbour in room["exits"].items():
                back = self.rooms[neighbour]["exits"].get(OPPOSITE[direction])
                self.assertEqual(back, position)

    def test_every_room_is_reachable(self):
        reached = scout_rooms(self.rooms, START_ROOM, 99)
        self.assertEqual(len(reached), 16)

    def test_enough_unique_artifacts_exist(self):
        found = set(room["artifact"] for room in self.rooms.values()
                    if room["artifact"])
        self.assertGreaterEqual(len(found), ARTIFACTS_REQUIRED)

    def test_duplicate_monsters_get_letters(self):
        names = [m["name"] for m in self.rooms[(1, 1)]["monsters"]]
        self.assertIn("Goblin A", names)
        self.assertIn("Goblin B", names)


class RecursionTests(unittest.TestCase):
    def setUp(self):
        self.rooms = build_rooms()

    def test_depth_zero_reaches_only_start(self):
        self.assertEqual(scout_rooms(self.rooms, (0, 0), 0), {(0, 0): 0})

    def test_negative_depth_reaches_nothing(self):          # base case 1
        self.assertEqual(scout_rooms(self.rooms, (0, 0), -1), {})

    def test_depth_one_reaches_direct_neighbours(self):
        reached = scout_rooms(self.rooms, (0, 0), 1)
        self.assertEqual(set(reached), {(0, 0), (1, 0), (0, 1)})

    def test_depth_two(self):
        reached = scout_rooms(self.rooms, (0, 0), 2)
        self.assertEqual(set(reached), {(0, 0), (1, 0), (0, 1), (2, 0),
                                        (1, 1), (0, 2)})

    def test_room_reached_by_two_paths_keeps_most_light(self):
        # (1, 1) is 2 steps away; it must be stored with 0 light left.
        self.assertEqual(scout_rooms(self.rooms, (0, 0), 2)[(1, 1)], 0)

    def test_loop_in_dungeon_does_not_repeat_forever(self):
        # (0,2)-(0,3)-(1,3)-(1,2)-(1,1)-(0,1) forms a loop; this must finish.
        self.assertEqual(len(scout_rooms(self.rooms, (0, 3), 50)), 16)


class GameRulesTests(unittest.TestCase):
    def setUp(self):
        self.game = GameState(seed=1)

    def test_starting_state(self):
        game = self.game
        self.assertEqual(game.status, "playing")
        self.assertEqual(game.position, START_ROOM)
        self.assertEqual(game.artifacts, set())
        self.assertEqual(game.equipment, [])
        self.assertEqual(game.player["hp"], game.player["max_hp"])

    def test_move_updates_tuple_position(self):
        self.game.search_room()
        self.assertTrue(self.game.move("East"))
        self.assertEqual(self.game.position, (1, 0))

    def test_no_exit_message(self):
        self.assertFalse(self.game.move("North"))
        self.assertIn("no exit", messages_text(self.game))

    def test_monsters_block_movement(self):
        self.game.move("East")                          # Armory has a goblin
        self.assertTrue(self.game.in_combat())
        self.assertFalse(self.game.move("East"))
        self.assertEqual(self.game.position, (1, 0))

    def test_flee_returns_to_previous_room_and_costs_hp(self):
        self.game.move("East")
        hp_before = self.game.player["hp"]
        self.assertTrue(self.game.flee())
        self.assertEqual(self.game.position, START_ROOM)
        self.assertLess(self.game.player["hp"], hp_before)

    def test_boss_door_needs_all_artifacts(self):
        self.game.position = (3, 2)                     # Forge, next to boss
        self.game.room()["monsters"] = []
        self.game.artifacts = {"Ruby Eye", "Silver Key"}
        self.assertFalse(self.game.move("South"))
        self.assertEqual(self.game.position, (3, 2))
        self.game.artifacts.add("Moon Crest")
        self.assertTrue(self.game.move("South"))
        self.assertEqual(self.game.position, BOSS_ROOM)

    def test_search_gives_gear_once(self):
        self.assertTrue(self.game.search_room())
        self.assertEqual(self.game.equipment[0]["name"], "Rusty Dagger")
        self.assertFalse(self.game.search_room())
        self.assertEqual(len(self.game.equipment), 1)

    def test_cannot_search_during_combat(self):
        self.game.move("East")
        self.assertFalse(self.game.search_room())

    def test_set_ignores_duplicate_artifacts(self):
        self.game._collect_artifact("Silver Key")
        self.game._collect_artifact("Silver Key")
        self.assertEqual(self.game.artifacts, {"Silver Key"})
        self.assertIn("duplicates", messages_text(self.game))

    def test_pack_stays_ordered_by_power(self):
        for name in ("Steel Axe", "Rusty Dagger", "Chain Mail", "Iron Sword"):
            self.game._collect_equipment(name)
        powers = [item["power"] for item in self.game.equipment]
        self.assertEqual(powers, [2, 3, 4, 6])

    def test_best_gear_boosts_stats(self):
        base_attack = self.game.attack_power()
        self.game._collect_equipment("Iron Sword")
        self.game._collect_equipment("Rusty Dagger")
        self.assertEqual(self.game.attack_power(), base_attack + 4)
        self.game._collect_equipment("Chain Mail")
        self.assertEqual(self.game.armor_power(), 3)

    def test_ranked_monsters_are_in_descending_hp_order(self):
        self.game.position = (1, 1)                     # Goblin Den
        self.game.monsters_here()[2]["hp"] = 4
        hps = [m["hp"] for m in self.game.ranked_monsters()]
        self.assertEqual(hps, [15, 15, 4])

    def test_strike_weakest_hits_lowest_hp_monster(self):
        self.game.position = (1, 1)
        monsters = self.game.monsters_here()
        for monster, hp in zip(monsters, (15, 12, 9)):
            monster["hp"] = hp
        weakest = monsters[2]
        self.game.strike_weakest()
        self.assertLess(weakest["hp"], 9)
        self.assertEqual(monsters[0]["hp"], 15)
        self.assertIn("Selection Sort", messages_text(self.game))

    def test_attack_needs_a_target(self):
        self.game.move("East")
        self.assertFalse(self.game.attack(None))

    def test_attack_rejects_monster_from_another_room(self):
        self.game.move("East")
        self.assertFalse(self.game.attack(make_monster("Orc")))

    def test_clearing_a_room_heals_a_little(self):
        self.game.move("East")
        self.game.player["hp"] = 30
        while self.game.in_combat():
            self.game.strike_weakest()
        self.assertGreater(self.game.player["hp"], 30 - 10)
        self.assertIn("catch your breath", messages_text(self.game))

    def test_potion_heals_and_is_used_up(self):
        self.game.player["hp"] = 10
        self.assertTrue(self.game.use_potion())
        self.assertEqual(self.game.player["hp"], 35)
        self.assertEqual(self.game.player["potions"], 0)
        self.assertFalse(self.game.use_potion())

    def test_potion_refused_at_full_health(self):
        self.assertFalse(self.game.use_potion())
        self.assertEqual(self.game.player["potions"], 1)

    def test_lantern_reveals_rooms_and_uses_a_charge(self):
        self.assertTrue(self.game.use_lantern())
        self.assertEqual(self.game.lantern_charges, LANTERN_CHARGES - 1)
        self.assertIn((2, 0), self.game.revealed)
        self.assertNotIn((3, 3), self.game.revealed)

    def test_lantern_runs_out(self):
        for _ in range(LANTERN_CHARGES):
            self.assertTrue(self.game.use_lantern())
        self.assertFalse(self.game.use_lantern())

    def test_losing_at_zero_hp(self):
        self.game.move("East")
        self.game.player["hp"] = 1
        self.game.strike_weakest()
        self.assertEqual(self.game.status, "lost")
        self.assertEqual(self.game.player["hp"], 0)
        self.assertFalse(self.game.move("West"))        # game is over

    def test_beating_the_boss_wins(self):
        self.game.position = BOSS_ROOM
        self.game.monsters_here()[:] = [make_monster("Dungeon Warden")]
        self.game.monsters_here()[0]["hp"] = 1
        self.game.strike_weakest()
        self.assertEqual(self.game.status, "won")

    def test_reset_starts_a_fresh_game(self):
        self.game.move("East")
        self.game.reset()
        self.assertEqual(self.game.position, START_ROOM)
        self.assertTrue(self.game.rooms[(1, 0)]["monsters"])


def walk_path(game, goal):
    """Breadth-first search for the directions leading to `goal`."""
    queue = deque([(game.position, [])])
    seen = {game.position}
    while queue:
        position, path = queue.popleft()
        if position == goal:
            return path
        for direction, destination in game.rooms[position]["exits"].items():
            if destination not in seen:
                seen.add(destination)
                queue.append((destination, path + [direction]))
    return []


def play_full_game(seed):
    """A simple bot: clear every non-boss room, then fight the Warden."""
    game = GameState(seed)
    seen = set()

    def fight():
        while game.status == "playing" and game.in_combat():
            if game.player["hp"] <= 22 and game.player["potions"] > 0:
                game.use_potion()
            else:
                game.strike_weakest()

    def explore():
        seen.add(game.position)
        fight()
        if game.status != "playing":
            return
        game.search_room()
        for direction, destination in list(game.room()["exits"].items()):
            if destination in seen or destination == BOSS_ROOM:
                continue
            game.move(direction)
            explore()
            if game.status != "playing":
                return
            game.move(OPPOSITE[direction])
            fight()

    explore()
    for direction in walk_path(game, BOSS_ROOM):
        game.move(direction)
    fight()
    return game


class FullPlaythroughTests(unittest.TestCase):
    def test_game_can_be_won(self):
        for seed in range(20):
            game = play_full_game(seed)
            self.assertEqual(game.status, "won", f"seed {seed}")
            self.assertEqual(len(game.artifacts), ARTIFACTS_REQUIRED)

    def test_rushing_the_boss_is_not_possible(self):
        game = GameState(seed=3)
        game.position = (3, 2)
        game.room()["monsters"] = []
        self.assertFalse(game.move("South"))


if __name__ == "__main__":
    unittest.main()
