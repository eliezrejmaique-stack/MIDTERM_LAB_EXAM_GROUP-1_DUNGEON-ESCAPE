# Dungeon Escape

A turn-based dungeon crawler written in Python with **Tkinter**.
You wake up in a sealed dungeon. Explore the rooms, fight monsters, collect gear
and three relics, then defeat the Dungeon Warden to escape.

*Midterm Lab Exam project, Python Game Development. Game type: Group 1, Dungeon Quest.*

## Objective

1. Explore the 4 x 4 dungeon.
2. Collect **3 different artifacts** (Ruby Eye, Silver Key, Moon Crest). This unlocks the Warden's Chamber.
3. Defeat the **Dungeon Warden** in the Warden's Chamber (bottom-right room) to **win**.
4. If your HP reaches 0 you **lose**. Press **Play again** (or Enter) to restart, or **Quit** to exit.

## Rules

- Every room has monsters, loot, or both. Entering a monster room starts combat; you cannot walk away, only fight, drink a potion, or **flee** (monsters get one parting blow).
- Combat is turn-based: you act, then every living monster hits you. Armor reduces damage taken.
- Clearing a room restores a little HP. Then **search** it once for gear, potions and artifacts.
- Your **best weapon** raises your attack and your **best armor** lowers damage. Both are equipped automatically.
- A second Silver Key is hidden in the dungeon on purpose: the artifact **set** ignores duplicates, so you must find 3 *different* artifacts.
- The **lantern** (3 charges) reveals every room within 2 steps on the map.
- Skipping rooms means skipping gear and potions, which makes the Warden much harder.

## Controls

| Action | Key | Button |
|---|---|---|
| Move | Arrow keys or W A S D | Move pad |
| Attack the selected monster | Space | Attack selected |
| Select a target | 1 - 5, or click the monster | |
| Strike the weakest monster | Q | Strike weakest |
| Drink a potion | H | Potion |
| Flee to the previous room | F | Flee |
| Search the room | E | Search room |
| Use the lantern | L | Lantern |
| Start / play again | Enter | |

## Team

| Member | Primary role | Main coding contribution |
|---|---|---|
| *Name 1* | Team coordinator and integrator | *e.g. `main.py`, `GameState.reset/move/flee`, merges* |
| *Name 2* | Gameplay programmer | *e.g. combat, potions, win/loss in `game_state.py`* |
| *Name 3* | Data structures and algorithms programmer | *e.g. `sorting.py`, `scout_rooms` in `dungeon_map.py`* |
| *Name 4* | Interface and asset designer | *e.g. `ui.py` screens, map drawing, colours* |
| *Name 5* | QA, documentation and release lead | *e.g. `tests/`, this README, a small feature or bug fix* |

> Replace the placeholders with your real names and what each person actually committed.
> With four members, merge the QA/documentation/release duties into the coordinator role.

## Framework and Python version

- Framework: **Tkinter** (included with Python, no `pip install` needed)
- Python: **3.8 or newer** (game rules and tests verified on Python 3.12)
- Assets: none. Everything on screen is drawn with Tkinter shapes and text, so there are no image or sound files to license.

## Setup and launch

```bash
git clone <your-repository-link>
cd dungeon_escape
python main.py          # on macOS/Linux you may need: python3 main.py
```

Tkinter ships with the Windows and macOS installers from python.org.
On Debian/Ubuntu Linux install it with `sudo apt install python3-tk`.
There is no `pip install` step: `requirements.txt` only records that no external packages are used.

## Feature map (where each required concept lives)

Line numbers are approximate: search for the function name if the file has changed.

| Course concept | Definition | Where the game uses it |
|---|---|---|
| **Bubble Sort** | `sorting.py` `bubble_sort` (line 37) | `game_state.py` `ranked_monsters` (line 87) ranks the monsters in a room by HP. The monster list on screen is that ranking, rebuilt after every action (`ui.py` `_refresh_monsters`). The artifact list is also ordered with it. |
| **Insertion Sort** | `sorting.py` `insertion_insert` (line 57) and `insertion_sort` (line 75) | `game_state.py` `_collect_equipment` (line 278) inserts each new piece of gear into the already ordered pack. The best weapon and armor are always the last matching items. |
| **Selection Sort** | `sorting.py` `index_of_extreme` (line 87) and `selection_sort` (line 97) | `game_state.py` `strike_weakest` (line 166) selects the lowest-HP monster and attacks it. |
| **Tuple** | `dungeon_data.py` `START_ROOM`, `BOSS_ROOM`, keys of `ROOM_INFO`, `CONNECTIONS` | Every room position is an `(x, y)` tuple. The player is at `game_state.py` `self.position` (line 38). `dungeon_map.py` turns coordinate differences like `(1, 0)` into directions (line 7). `ui.py` `_room_box` (line 522) draws rooms from tuples. |
| **Set** | `game_state.py` `self.artifacts` (line 42), `self.visited` (line 40), `self.revealed` | `_collect_artifact` (line 296) adds to the artifact set, so the duplicate Silver Key never counts twice. The boss door checks `len(self.artifacts)`. The map draws `visited | revealed` (set union). |
| **Dictionary** | `dungeon_data.py` `PLAYER_START` (17), `MONSTER_TEMPLATES` (20), `EQUIPMENT` (30), `ROOM_INFO` (41) | Hero stats (`self.player`, line 36), every monster, piece of gear and room is a dictionary that is read and updated during play. `ui.py` `self.keymap` (line 131) maps keys to actions. |
| **Recursion** | `dungeon_map.py` `scout_rooms` (line 51) | `game_state.py` `use_lantern` (line 312) calls it to reveal connected rooms. Base cases: `depth < 0`, or a room already reached with as much light. Each call uses `depth - 1`, so it always stops. |

### Recursion trace (for the demo)

`scout_rooms(rooms, (0, 0), 1)` marks `(0, 0)`, then calls itself for `(1, 0)` and `(0, 1)` with depth 0.
Each of those marks its room and calls its neighbours with depth -1, which hits the base case and returns.
Result: `{(0, 0): 1, (1, 0): 0, (0, 1): 0}`.

## Project structure

```
dungeon_escape/
  main.py            entry point (python main.py)
  ui.py              Tkinter screens, map drawing, buttons, keyboard
  game_state.py      game rules: movement, combat, items, win/loss
  dungeon_map.py     builds the room graph; recursive lantern search
  dungeon_data.py    rooms, monsters, equipment (tuples and dictionaries)
  sorting.py         Bubble, Insertion and Selection Sort (hand-written)
  tests/             automated tests (unittest)
  requirements.txt   no external packages
```

`game_state.py` never imports Tkinter, so all game rules are tested without a window.

## Testing

Automated tests (83 checks, no window needed):

```bash
python -m unittest -v
```

They cover each sort with an **empty list, a one-item list and short game-data lists**,
the recursion base cases, tuple/set/dictionary behaviour, every combat and item rule,
a scripted bot that wins the full game, and a no-window smoke test of the interface code.

Manual checklist (QA lead: run it in a clean clone and fill in the Result column):

| # | Steps | Expected | Result |
|---|---|---|---|
| 1 | Run `python main.py` | Title screen shows instructions and controls | |
| 2 | Press Enter | Game screen opens with the map, hero stats and a welcome message | |
| 3 | Press E in the Entrance Hall | Rusty Dagger appears in the pack with an Insertion Sort line in the log | |
| 4 | Move East into the Armory | Combat starts, monster list is ranked, move buttons are disabled | |
| 5 | Press Space, then Q | Attack and Strike weakest both damage a monster; monsters hit back | |
| 6 | Press F during combat | You return to the previous room after a parting hit | |
| 7 | Press L | Lantern charge drops 3 to 2 and new rooms show on the map | |
| 8 | Try to enter the Warden's Chamber with fewer than 3 artifacts | Door stays sealed with a message | |
| 9 | Pick up both Silver Keys | Artifact count rises only once | |
| 10 | Let HP reach 0 | "The dungeon wins" screen; Enter restarts a fresh game | |
| 11 | Defeat the Warden | "You escaped!" screen with score; Quit closes the window | |

### Bug log (fill in during development)

| Bug | Found by | Fix | Fixed in commit |
|---|---|---|---|
| *Example: heal exploit: HP regained on every room entry* | *QA* | *Heal once when a room is cleared* | *abc1234* |

## Credits and licenses

No third-party code, images, fonts or sounds are used. Fonts are standard system fonts.
All text, rooms, monsters and code were written by the team.

## Commit history

Commit early and often, one feature per commit, for example
`Add Bubble Sort and tests`, `Add combat loop`, `Draw dungeon map`, `Fix potion at full HP`.
Each member should commit their own feature on a branch and merge it.
Never commit passwords, API keys or other secrets (`.gitignore` already ignores `.env`).
