"""Tests for the three hand-written sorting algorithms.

Each sort is tested with: an empty list, a one-item list, and short game-data
lists (monsters by HP, gear by power).  Expected results are written out by
hand, so the built-in sorted() is never used.
"""

import unittest

from sorting import (bubble_sort, index_of_extreme, insertion_insert,
                     insertion_sort, selection_sort)


def hp(monster):
    return monster["hp"]


def power(item):
    return item["power"]


def make_monsters():
    return [{"name": "Goblin", "hp": 15}, {"name": "Bat", "hp": 9},
            {"name": "Orc", "hp": 30}, {"name": "Skeleton", "hp": 20}]


def names(items):
    return [item["name"] for item in items]


class SortTestsMixin:
    """The same checks run against every algorithm."""

    sort = None

    def run_sort(self, items, **kwargs):
        return type(self).sort(items, **kwargs)

    def test_empty_list(self):
        self.assertEqual(self.run_sort([]), [])

    def test_one_item(self):
        self.assertEqual(self.run_sort([7]), [7])

    def test_numbers_ascending(self):
        self.assertEqual(self.run_sort([5, 2, 9, 1, 5]), [1, 2, 5, 5, 9])

    def test_already_sorted(self):
        self.assertEqual(self.run_sort([1, 2, 3, 4]), [1, 2, 3, 4])

    def test_reverse_order(self):
        self.assertEqual(self.run_sort([4, 3, 2, 1]), [1, 2, 3, 4])

    def test_monsters_by_hp_ascending(self):
        result = self.run_sort(make_monsters(), key=hp)
        self.assertEqual(names(result), ["Bat", "Goblin", "Skeleton", "Orc"])

    def test_monsters_by_hp_descending(self):
        result = self.run_sort(make_monsters(), key=hp, descending=True)
        self.assertEqual(names(result), ["Orc", "Skeleton", "Goblin", "Bat"])

    def test_input_list_is_not_changed(self):
        original = make_monsters()
        self.run_sort(original, key=hp)
        self.assertEqual(names(original),
                         ["Goblin", "Bat", "Orc", "Skeleton"])

    def test_strings(self):
        self.assertEqual(self.run_sort(["Ruby Eye", "Moon Crest", "Silver Key"]),
                         ["Moon Crest", "Ruby Eye", "Silver Key"])

    def test_stats_are_counted(self):
        stats = {}
        self.run_sort([3, 1, 2], stats=stats)
        self.assertGreater(stats["comparisons"], 0)


class BubbleSortTests(SortTestsMixin, unittest.TestCase):
    sort = staticmethod(bubble_sort)

    def test_sorted_list_needs_one_pass_only(self):
        stats = {}
        bubble_sort([1, 2, 3, 4], stats=stats)
        self.assertEqual(stats["passes"], 1)
        self.assertEqual(stats.get("swaps", 0), 0)

    def test_hand_traced_swaps(self):
        # [3, 1, 2]: pass 1 swaps 3<->1 then 3<->2; pass 2 swaps nothing.
        stats = {}
        self.assertEqual(bubble_sort([3, 1, 2], stats=stats), [1, 2, 3])
        self.assertEqual(stats["swaps"], 2)
        self.assertEqual(stats["comparisons"], 3)


class SelectionSortTests(SortTestsMixin, unittest.TestCase):
    sort = staticmethod(selection_sort)

    def test_index_of_extreme_finds_weakest(self):
        monsters = make_monsters()
        self.assertEqual(monsters[index_of_extreme(monsters, 0, key=hp)]["name"],
                         "Bat")

    def test_index_of_extreme_finds_strongest(self):
        monsters = make_monsters()
        index = index_of_extreme(monsters, 0, key=hp, descending=True)
        self.assertEqual(monsters[index]["name"], "Orc")

    def test_index_of_extreme_respects_start(self):
        monsters = make_monsters()          # Bat (index 1) is skipped
        self.assertEqual(monsters[index_of_extreme(monsters, 2, key=hp)]["name"],
                         "Skeleton")

    def test_hand_traced_swaps(self):
        # [3, 1, 2]: select 1 (swap), select 2 (swap) -> 2 swaps, 3 comparisons
        stats = {}
        self.assertEqual(selection_sort([3, 1, 2], stats=stats), [1, 2, 3])
        self.assertEqual(stats["swaps"], 2)
        self.assertEqual(stats["comparisons"], 3)


class InsertionSortTests(SortTestsMixin, unittest.TestCase):
    sort = staticmethod(insertion_sort)

    def gear(self):
        return [{"name": "Dagger", "power": 2}, {"name": "Axe", "power": 6}]

    def test_insert_into_empty_list(self):
        sword = {"name": "Sword", "power": 4}
        self.assertEqual(insertion_insert([], sword, key=power), [sword])

    def test_insert_in_the_middle(self):
        sword = {"name": "Sword", "power": 4}
        result = insertion_insert(self.gear(), sword, key=power)
        self.assertEqual(names(result), ["Dagger", "Sword", "Axe"])

    def test_insert_at_the_front(self):
        stick = {"name": "Stick", "power": 1}
        result = insertion_insert(self.gear(), stick, key=power)
        self.assertEqual(names(result), ["Stick", "Dagger", "Axe"])

    def test_insert_at_the_end(self):
        runed = {"name": "Runed", "power": 8}
        stats = {}
        result = insertion_insert(self.gear(), runed, key=power, stats=stats)
        self.assertEqual(names(result), ["Dagger", "Axe", "Runed"])
        self.assertEqual(stats.get("shifts", 0), 0)

    def test_shifts_are_counted(self):
        stick = {"name": "Stick", "power": 1}
        stats = {}
        insertion_insert(self.gear(), stick, key=power, stats=stats)
        self.assertEqual(stats["shifts"], 2)

    def test_insert_does_not_change_original(self):
        original = self.gear()
        insertion_insert(original, {"name": "Sword", "power": 4}, key=power)
        self.assertEqual(names(original), ["Dagger", "Axe"])

    def test_equal_power_keeps_older_item_first(self):
        twin = {"name": "Twin", "power": 6}
        result = insertion_insert(self.gear(), twin, key=power)
        self.assertEqual(names(result), ["Dagger", "Axe", "Twin"])


if __name__ == "__main__":
    unittest.main()
