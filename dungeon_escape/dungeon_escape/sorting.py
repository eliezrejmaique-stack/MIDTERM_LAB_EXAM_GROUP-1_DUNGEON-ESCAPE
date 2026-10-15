"""Hand-written sorting algorithms for Dungeon Escape.

The course asks us to write Bubble Sort, Insertion Sort and Selection Sort
ourselves, so this file never calls the built-in sort() or sorted().

Every function here:
  * takes a list `items` and an optional `key` function (what to compare),
  * takes descending=True to put the LARGEST value first,
  * returns a NEW list and leaves the original list unchanged,
  * fills the optional `stats` dictionary (comparisons, swaps, shifts ...)
    so the game can show the player what the algorithm just did.
"""


def _same(value):
    """Default key: compare the items themselves."""
    return value


def _count(stats, name):
    """Add 1 to a named counter if the caller gave us a stats dictionary."""
    if stats is not None:
        stats[name] = stats.get(name, 0) + 1


def _out_of_order(left, right, descending):
    """True when `left` must go AFTER `right` to reach the wanted order."""
    if descending:
        return left < right
    return left > right


# --------------------------------------------------------------------------
# Bubble Sort: repeated adjacent comparisons.
# Game use: GameState.ranked_monsters() ranks monsters in a room by HP.
# --------------------------------------------------------------------------
def bubble_sort(items, key=_same, descending=False, stats=None):
    result = list(items)
    for last in range(len(result) - 1, 0, -1):
        swapped_this_pass = False
        _count(stats, "passes")
        for i in range(last):
            _count(stats, "comparisons")
            if _out_of_order(key(result[i]), key(result[i + 1]), descending):
                result[i], result[i + 1] = result[i + 1], result[i]
                swapped_this_pass = True
                _count(stats, "swaps")
        if not swapped_this_pass:      # already ordered: stop early
            break
    return result


# --------------------------------------------------------------------------
# Insertion Sort: insert one new item into an already ordered list.
# Game use: GameState._collect_equipment() slots new gear into the pack.
# --------------------------------------------------------------------------
def insertion_insert(ordered_items, new_item, key=_same, descending=False,
                     stats=None):
    """Return a new ordered list that also contains `new_item`."""
    result = list(ordered_items)
    result.append(new_item)                    # start at the far end
    position = len(result) - 1
    while position > 0:
        _count(stats, "comparisons")
        if _out_of_order(key(result[position - 1]), key(new_item), descending):
            result[position] = result[position - 1]    # shift right
            _count(stats, "shifts")
            position -= 1
        else:
            break
    result[position] = new_item
    return result


def insertion_sort(items, key=_same, descending=False, stats=None):
    """Sort a whole list by inserting its items one at a time."""
    result = []
    for item in items:
        result = insertion_insert(result, item, key, descending, stats)
    return result


# --------------------------------------------------------------------------
# Selection Sort: repeatedly select the smallest (or largest) remaining value.
# Game use: GameState.strike_weakest() selects the weakest monster.
# --------------------------------------------------------------------------
def index_of_extreme(items, start, key=_same, descending=False, stats=None):
    """Index of the smallest (largest if descending) item from `start` on."""
    best = start
    for i in range(start + 1, len(items)):
        _count(stats, "comparisons")
        if _out_of_order(key(items[best]), key(items[i]), descending):
            best = i
    return best


def selection_sort(items, key=_same, descending=False, stats=None):
    result = list(items)
    for start in range(len(result) - 1):
        best = index_of_extreme(result, start, key, descending, stats)
        if best != start:
            result[start], result[best] = result[best], result[start]
            _count(stats, "swaps")
    return result
