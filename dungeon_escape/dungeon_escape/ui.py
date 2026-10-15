"""Tkinter interface for Dungeon Escape.

This file only draws the screens and forwards clicks/keys to GameState.
All game rules live in game_state.py.
"""

import tkinter as tk

from dungeon_data import (ARTIFACTS_REQUIRED, BOSS_ROOM, GRID_HEIGHT,
                          GRID_WIDTH, LANTERN_CHARGES)
from game_state import GameState
from sorting import bubble_sort

COLORS = {
    "bg": "#1b1d24",          # dungeon slate
    "panel": "#242731",
    "raised": "#2f3340",
    "edge": "#454a5a",
    "text": "#ece3cb",        # parchment
    "muted": "#9a9486",
    "torch": "#f0b24a",       # torch light: the one warm accent
    "torch_hi": "#ffc766",
    "blood": "#d0524a",
    "moss": "#79b36e",
    "verdigris": "#52b3a6",   # used for the sorting/recursion trace lines
}
LOG_COLORS = {"info": COLORS["text"], "good": COLORS["moss"],
              "bad": COLORS["blood"], "sort": COLORS["verdigris"]}

TITLE_FONT = ("Georgia", 36, "bold")
HEAD_FONT = ("Georgia", 15, "bold")
ROOM_FONT = ("Georgia", 22, "bold")
BODY_FONT = ("Helvetica", 11)
BOLD_FONT = ("Helvetica", 11, "bold")
SMALL_FONT = ("Helvetica", 10)
MONO_FONT = ("Courier", 11)

CELL = 78                     # map: distance between room centres
ROOM_SIZE = 58                # map: size of one room square
MARGIN = 10
MAP_WIDTH = MARGIN * 2 + CELL * (GRID_WIDTH - 1) + ROOM_SIZE
MAP_HEIGHT = MARGIN * 2 + CELL * (GRID_HEIGHT - 1) + ROOM_SIZE
HP_BAR_WIDTH = 250

HOW_TO_PLAY = [
    "Goal: collect 3 different artifacts to unlock the Warden's Chamber, "
    "then defeat the Dungeon Warden.",
    "Every room hides monsters or loot. Clear a room, then search it for "
    "gear, potions and artifacts.",
    "Monsters are ranked by HP with Bubble Sort. Strike Weakest finds its "
    "target with Selection Sort.",
    "New gear slides into your pack in power order (Insertion Sort). Your "
    "best weapon and armor are used automatically.",
    "Artifacts live in a set, so a duplicate never counts twice.",
    "The lantern uses recursion to reveal rooms up to 2 steps away "
    "(3 charges).",
    "Reach 0 HP and the dungeon keeps you.",
]
CONTROLS = [
    "Move: arrow keys or W A S D",
    "Attack selected monster: Space",
    "Select a target: click it, or press 1-5",
    "Strike weakest monster: Q",
    "Drink potion: H",
    "Flee to the last room: F",
    "Search room: E",
    "Lantern: L",
    "Start / play again: Enter",
]


class FlatButton:
    """A label-based button so colours look the same on Windows, macOS, Linux."""

    def __init__(self, parent, text, command, accent=False, width=None):
        self.command = command
        self.accent = accent
        self.enabled = True
        self.label = tk.Label(parent, text=text, font=BOLD_FONT, padx=10,
                              pady=6, highlightthickness=1,
                              highlightbackground=COLORS["edge"], takefocus=0)
        if width is not None:
            self.label.configure(width=width)
        self.label.bind("<Button-1>", self._clicked)
        self.label.bind("<Enter>", lambda event: self._paint(True))
        self.label.bind("<Leave>", lambda event: self._paint(False))
        self._paint(False)

    def _paint(self, hovering):
        if not self.enabled:
            background, foreground = COLORS["panel"], COLORS["muted"]
        elif self.accent:
            background = COLORS["torch_hi"] if hovering else COLORS["torch"]
            foreground = COLORS["bg"]
        else:
            background = COLORS["edge"] if hovering else COLORS["raised"]
            foreground = COLORS["text"]
        self.label.configure(bg=background, fg=foreground,
                             cursor="hand2" if self.enabled else "arrow")

    def _clicked(self, event):
        if self.enabled:
            self.command()

    def set_enabled(self, enabled):
        self.enabled = enabled
        self._paint(False)

    def grid(self, **options):
        self.label.grid(**options)

    def pack(self, **options):
        self.label.pack(**options)


class DungeonEscapeApp:
    def __init__(self, root):
        self.root = root
        self.state = GameState()
        self.screen = "start"
        self.frames = {}
        self.ranked = []          # monsters in list order (Bubble Sort result)
        self.selected = None      # the monster the player is targeting

        root.title("Dungeon Escape")
        root.geometry("1120x720")
        root.minsize(1040, 680)
        root.configure(bg=COLORS["bg"])

        # key name -> action (a dictionary, again)
        self.keymap = {
            "up": lambda: self.do_move("North"),
            "w": lambda: self.do_move("North"),
            "down": lambda: self.do_move("South"),
            "s": lambda: self.do_move("South"),
            "left": lambda: self.do_move("West"),
            "a": lambda: self.do_move("West"),
            "right": lambda: self.do_move("East"),
            "d": lambda: self.do_move("East"),
            "space": self.do_attack,
            "q": self.do_weakest,
            "h": self.do_potion,
            "f": self.do_flee,
            "e": self.do_search,
            "l": self.do_lantern,
        }

        self._build_start_screen()
        self._build_game_screen()
        self._build_end_screen()
        root.bind("<Key>", self._on_key)
        # Lists and the log must never keep keyboard focus, or the arrow
        # keys and Space would act on them as well as on the game.
        for widget in (self.monster_list, self.gear_list, self.log):
            widget.bind("<FocusIn>", lambda event: self.root.focus_set())
        self.show_screen("start")

    # ------------------------------------------------------------------
    # screens
    # ------------------------------------------------------------------
    def show_screen(self, name):
        self.screen = name
        for frame in self.frames.values():
            frame.pack_forget()
        self.frames[name].pack(fill="both", expand=True)

    def _info_card(self, parent, title, lines, wrap):
        card = tk.Frame(parent, bg=COLORS["panel"], highlightthickness=1,
                        highlightbackground=COLORS["edge"])
        tk.Label(card, text=title, font=HEAD_FONT, fg=COLORS["torch"],
                 bg=COLORS["panel"]).pack(anchor="w", padx=14, pady=(12, 6))
        for line in lines:
            tk.Label(card, text=line, font=BODY_FONT, fg=COLORS["text"],
                     bg=COLORS["panel"], justify="left", anchor="w",
                     wraplength=wrap).pack(anchor="w", padx=14, pady=3)
        tk.Frame(card, bg=COLORS["panel"], height=8).pack()
        return card

    def _build_start_screen(self):
        frame = tk.Frame(self.root, bg=COLORS["bg"])
        self.frames["start"] = frame
        box = tk.Frame(frame, bg=COLORS["bg"])
        box.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(box, text="Dungeon Escape", font=TITLE_FONT,
                 fg=COLORS["torch"], bg=COLORS["bg"]).pack()
        tk.Label(box, text="The gate is sealed. Three relics open the way to "
                 "the Warden.", font=BODY_FONT, fg=COLORS["muted"],
                 bg=COLORS["bg"]).pack(pady=(2, 16))
        cards = tk.Frame(box, bg=COLORS["bg"])
        cards.pack()
        self._info_card(cards, "How to play", HOW_TO_PLAY, 430).grid(
            row=0, column=0, padx=8, sticky="n")
        self._info_card(cards, "Controls", CONTROLS, 280).grid(
            row=0, column=1, padx=8, sticky="n")
        FlatButton(box, "Enter the dungeon  (Enter)", self.start_game,
                   accent=True).pack(pady=18)

    def _section_label(self, parent, text):
        tk.Label(parent, text=text, font=BOLD_FONT, fg=COLORS["muted"],
                 bg=COLORS["bg"], anchor="w").pack(fill="x", pady=(10, 4))

    def _build_game_screen(self):
        frame = tk.Frame(self.root, bg=COLORS["bg"])
        self.frames["game"] = frame
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)

        # --- header -------------------------------------------------
        header = tk.Frame(frame, bg=COLORS["panel"])
        header.grid(row=0, column=0, columnspan=3, sticky="ew")
        tk.Label(header, text="Dungeon Escape", font=HEAD_FONT,
                 fg=COLORS["torch"], bg=COLORS["panel"]).pack(
            side="left", padx=14, pady=8)
        self.turn_label = tk.Label(header, text="Turn 0", font=BODY_FONT,
                                   fg=COLORS["text"], bg=COLORS["panel"])
        self.turn_label.pack(side="left", padx=14)
        self.score_label = tk.Label(header, text="Score 0", font=BODY_FONT,
                                    fg=COLORS["text"], bg=COLORS["panel"])
        self.score_label.pack(side="left", padx=14)
        FlatButton(header, "Quit", self.root.destroy).pack(
            side="right", padx=(4, 12), pady=6)
        FlatButton(header, "Restart", self.start_game).pack(
            side="right", padx=4, pady=6)

        # --- left column: map and movement ---------------------------
        left = tk.Frame(frame, bg=COLORS["bg"])
        left.grid(row=1, column=0, sticky="ns", padx=(14, 7), pady=6)
        self._section_label(left, "Dungeon map")
        self.map_canvas = tk.Canvas(left, width=MAP_WIDTH, height=MAP_HEIGHT,
                                    bg=COLORS["panel"], highlightthickness=1,
                                    highlightbackground=COLORS["edge"])
        self.map_canvas.pack()
        self._section_label(left, "Move")
        pad = tk.Frame(left, bg=COLORS["bg"])
        pad.pack()
        self.move_buttons = {}
        pad_cells = {"North": (0, 1), "West": (1, 0),
                     "East": (1, 2), "South": (2, 1)}
        for direction, (row, column) in pad_cells.items():
            button = FlatButton(pad, direction,
                                lambda d=direction: self.do_move(d), width=7)
            button.grid(row=row, column=column, padx=2, pady=2)
            self.move_buttons[direction] = button
        tools = tk.Frame(left, bg=COLORS["bg"])
        tools.pack(pady=(12, 0))
        self.search_button = FlatButton(tools, "Search room (E)",
                                        self.do_search, width=16)
        self.search_button.grid(row=0, column=0, padx=2, pady=2)
        self.lantern_button = FlatButton(tools, "Lantern (L)",
                                         self.do_lantern, width=16)
        self.lantern_button.grid(row=1, column=0, padx=2, pady=2)

        # --- centre column: room, combat, log ------------------------
        center = tk.Frame(frame, bg=COLORS["bg"])
        center.grid(row=1, column=1, sticky="nsew", padx=7, pady=6)
        center.columnconfigure(0, weight=1)
        center.rowconfigure(3, weight=1)
        self.room_title = tk.Label(center, text="", font=ROOM_FONT,
                                   fg=COLORS["torch"], bg=COLORS["bg"],
                                   anchor="w")
        self.room_title.grid(row=0, column=0, sticky="ew")
        self.room_text = tk.Label(center, text="", font=BODY_FONT,
                                  fg=COLORS["text"], bg=COLORS["bg"],
                                  anchor="w", justify="left", wraplength=520)
        self.room_text.grid(row=1, column=0, sticky="ew", pady=(2, 6))

        combat = tk.Frame(center, bg=COLORS["panel"], highlightthickness=1,
                          highlightbackground=COLORS["edge"])
        combat.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        tk.Label(combat, text="Monsters, ranked by HP (Bubble Sort)",
                 font=BOLD_FONT, fg=COLORS["muted"],
                 bg=COLORS["panel"]).pack(anchor="w", padx=10, pady=(8, 4))
        self.monster_list = tk.Listbox(
            combat, height=4, font=MONO_FONT, bg=COLORS["raised"],
            fg=COLORS["text"], selectbackground=COLORS["torch"],
            selectforeground=COLORS["bg"], bd=0, highlightthickness=0,
            activestyle="none", exportselection=False, takefocus=0)
        self.monster_list.pack(fill="x", padx=10)
        self.monster_list.bind("<<ListboxSelect>>", self._on_monster_click)
        buttons = tk.Frame(combat, bg=COLORS["panel"])
        buttons.pack(fill="x", padx=10, pady=8)
        self.attack_button = FlatButton(buttons, "Attack selected (Space)",
                                        self.do_attack, accent=True)
        self.attack_button.grid(row=0, column=0, padx=(0, 4))
        self.weakest_button = FlatButton(buttons, "Strike weakest (Q)",
                                         self.do_weakest)
        self.weakest_button.grid(row=0, column=1, padx=4)
        self.potion_button = FlatButton(buttons, "Potion (H)", self.do_potion)
        self.potion_button.grid(row=0, column=2, padx=4)
        self.flee_button = FlatButton(buttons, "Flee (F)", self.do_flee)
        self.flee_button.grid(row=0, column=3, padx=4)

        self.log = tk.Text(center, height=10, wrap="word", font=MONO_FONT,
                           bg=COLORS["panel"], fg=COLORS["text"], bd=0,
                           highlightthickness=1,
                           highlightbackground=COLORS["edge"], padx=10,
                           pady=8, state="disabled", takefocus=0,
                           cursor="arrow")
        self.log.grid(row=3, column=0, sticky="nsew")
        for tag, color in LOG_COLORS.items():
            self.log.tag_configure(tag, foreground=color)
        tk.Label(center, text="Move: arrows / WASD   Attack: Space   "
                 "Weakest: Q   Potion: H   Flee: F   Search: E   Lantern: L",
                 font=SMALL_FONT, fg=COLORS["muted"], bg=COLORS["bg"],
                 anchor="w").grid(row=4, column=0, sticky="ew", pady=(6, 0))

        # --- right column: hero --------------------------------------
        right = tk.Frame(frame, bg=COLORS["bg"])
        right.grid(row=1, column=2, sticky="ns", padx=(7, 14), pady=6)
        self._section_label(right, "Hero")
        self.hp_label = tk.Label(right, text="", font=BOLD_FONT,
                                 fg=COLORS["text"], bg=COLORS["bg"],
                                 anchor="w")
        self.hp_label.pack(fill="x")
        self.hp_bar = tk.Canvas(right, width=HP_BAR_WIDTH, height=14,
                                bg=COLORS["raised"], highlightthickness=0)
        self.hp_bar.pack(pady=(2, 6))
        self.stats_label = tk.Label(right, text="", font=BODY_FONT,
                                    fg=COLORS["text"], bg=COLORS["bg"],
                                    anchor="w", justify="left")
        self.stats_label.pack(fill="x")
        self._section_label(right, "Artifacts (a set: no duplicates)")
        self.artifact_label = tk.Label(right, text="", font=BODY_FONT,
                                       fg=COLORS["torch"], bg=COLORS["bg"],
                                       anchor="w", justify="left",
                                       wraplength=HP_BAR_WIDTH)
        self.artifact_label.pack(fill="x")
        self._section_label(right, "Pack, by power (Insertion Sort)")
        self.gear_list = tk.Listbox(
            right, height=8, width=29, font=MONO_FONT, bg=COLORS["panel"],
            fg=COLORS["text"], bd=0, highlightthickness=1,
            highlightbackground=COLORS["edge"], activestyle="none",
            selectbackground=COLORS["panel"], selectforeground=COLORS["text"],
            exportselection=False, takefocus=0)
        self.gear_list.pack(fill="x")
        tk.Label(right, text="* = equipped (best of its kind)", font=SMALL_FONT,
                 fg=COLORS["muted"], bg=COLORS["bg"], anchor="w").pack(
            fill="x", pady=(4, 0))

    def _build_end_screen(self):
        frame = tk.Frame(self.root, bg=COLORS["bg"])
        self.frames["end"] = frame
        box = tk.Frame(frame, bg=COLORS["bg"])
        box.place(relx=0.5, rely=0.5, anchor="center")
        self.end_title = tk.Label(box, text="", font=TITLE_FONT,
                                  fg=COLORS["torch"], bg=COLORS["bg"])
        self.end_title.pack()
        self.end_text = tk.Label(box, text="", font=HEAD_FONT,
                                 fg=COLORS["text"], bg=COLORS["bg"],
                                 justify="center")
        self.end_text.pack(pady=18)
        FlatButton(box, "Play again  (Enter)", self.start_game,
                   accent=True).pack(pady=4)
        FlatButton(box, "Quit", self.root.destroy).pack(pady=4)

    # ------------------------------------------------------------------
    # starting, ending, input
    # ------------------------------------------------------------------
    def start_game(self):
        self.state = GameState()
        self.selected = None
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self.show_screen("game")
        self._flush_messages()
        self.refresh()

    def show_end(self):
        if self.state.status == "playing":      # player restarted meanwhile
            return
        state = self.state
        won = state.status == "won"
        self.end_title.configure(
            text="You escaped!" if won else "The dungeon wins",
            fg=COLORS["moss"] if won else COLORS["blood"])
        self.end_text.configure(
            text=f"Score {state.score}\nTurns {state.turns}\n"
                 f"Monsters defeated {state.kills}\n"
                 f"Artifacts {len(state.artifacts)} / {ARTIFACTS_REQUIRED}")
        self.show_screen("end")

    def _on_key(self, event):
        key = event.keysym.lower()
        if key in ("return", "kp_enter") and self.screen in ("start", "end"):
            self.start_game()
        elif self.screen == "game" and key in self.keymap:
            self.keymap[key]()
        elif self.screen == "game" and key.isdigit():
            self.select_by_number(int(key))

    # ------------------------------------------------------------------
    # actions (each one asks GameState, then redraws)
    # ------------------------------------------------------------------
    def _act(self, action, *args):
        if self.screen != "game" or self.state.status != "playing":
            return
        action(*args)
        self._flush_messages()
        self.refresh()
        if self.state.status != "playing":
            self.root.after(1200, self.show_end)

    def do_move(self, direction):
        self._act(self.state.move, direction)

    def do_attack(self):
        self._act(self.state.attack, self.selected)

    def do_weakest(self):
        self._act(self.state.strike_weakest)

    def do_potion(self):
        self._act(self.state.use_potion)

    def do_flee(self):
        self._act(self.state.flee)

    def do_search(self):
        self._act(self.state.search_room)

    def do_lantern(self):
        self._act(self.state.use_lantern)

    def select_by_number(self, number):
        if 1 <= number <= len(self.ranked):
            self.selected = self.ranked[number - 1]
            self._refresh_monsters()

    def _on_monster_click(self, event):
        picked = self.monster_list.curselection()
        if picked and picked[0] < len(self.ranked):
            self.selected = self.ranked[picked[0]]

    def _flush_messages(self):
        self.log.configure(state="normal")
        for tag, text in self.state.pop_messages():
            self.log.insert("end", text + "\n", tag)
        self.log.configure(state="disabled")
        self.log.see("end")

    # ------------------------------------------------------------------
    # drawing
    # ------------------------------------------------------------------
    def refresh(self):
        state = self.state
        room = state.room()
        self.turn_label.configure(text=f"Turn {state.turns}")
        self.score_label.configure(text=f"Score {state.score}")
        # state.position is a tuple (x, y): shown next to the room name
        self.room_title.configure(text=f"{room['name']}  {state.position}")
        exits = ", ".join(room["exits"].keys())
        self.room_text.configure(
            text=f"{room['description']}\nExits: {exits}")
        self._refresh_monsters()
        self._refresh_hero()
        self._draw_map()
        self._update_buttons()

    def _refresh_monsters(self):
        self.ranked = self.state.ranked_monsters()      # Bubble Sort by HP
        if not any(m is self.selected for m in self.ranked):
            self.selected = self.ranked[0] if self.ranked else None
        self.monster_list.delete(0, "end")
        if not self.ranked:
            self.monster_list.insert("end", "No monsters here.")
            return
        for number, monster in enumerate(self.ranked, start=1):
            self.monster_list.insert(
                "end", f"{number}. {monster['name']:<15} "
                       f"HP {monster['hp']:>3}/{monster['max_hp']:<3} "
                       f"ATK {monster['attack']}")
            if monster is self.selected:
                self.monster_list.selection_set(number - 1)

    def _refresh_hero(self):
        state = self.state
        player = state.player
        self.hp_label.configure(text=f"HP {player['hp']} / {player['max_hp']}")
        fraction = player["hp"] / player["max_hp"]
        self.hp_bar.delete("all")
        color = COLORS["moss"] if fraction > 0.35 else COLORS["blood"]
        self.hp_bar.create_rectangle(0, 0, int(HP_BAR_WIDTH * fraction), 14,
                                     fill=color, width=0)
        self.stats_label.configure(
            text=f"Attack {state.attack_power()}    Armor {state.armor_power()}"
                 f"\nPotions {player['potions']}    "
                 f"Lantern {state.lantern_charges}/{LANTERN_CHARGES}")
        names = bubble_sort(list(state.artifacts))      # our own sort again
        listing = ", ".join(names) if names else "none yet"
        self.artifact_label.configure(
            text=f"{len(names)} / {ARTIFACTS_REQUIRED}: {listing}")
        self.gear_list.delete(0, "end")
        if not state.equipment:
            self.gear_list.insert("end", "Empty. Search rooms.")
        best_weapon = state.best_equipped("weapon")
        best_armor = state.best_equipped("armor")
        for item in reversed(state.equipment):          # strongest first
            mark = "*" if item is best_weapon or item is best_armor else " "
            self.gear_list.insert(
                "end", f"{mark} {item['name']:<17} +{item['power']} "
                       f"{item['kind'][:3]}")

    def _update_buttons(self):
        state = self.state
        playing = state.status == "playing"
        combat = playing and state.in_combat()
        exits = state.room()["exits"]
        for direction, button in self.move_buttons.items():
            button.set_enabled(playing and not combat and direction in exits)
        self.attack_button.set_enabled(combat)
        self.weakest_button.set_enabled(combat)
        self.flee_button.set_enabled(combat)
        self.potion_button.set_enabled(
            playing and state.player["potions"] > 0
            and state.player["hp"] < state.player["max_hp"])
        self.search_button.set_enabled(
            playing and not combat and not state.room()["searched"])
        self.lantern_button.set_enabled(
            playing and not combat and state.lantern_charges > 0)

    def _room_box(self, position):
        """Top-left corner of a room square; position is an (x, y) tuple."""
        x, y = position
        return MARGIN + x * CELL, MARGIN + y * CELL

    def _draw_map(self):
        state = self.state
        canvas = self.map_canvas
        canvas.delete("all")
        known = state.visited | state.revealed          # set union
        half = ROOM_SIZE // 2
        for position in known:                          # corridors first
            for neighbour in state.rooms[position]["exits"].values():
                if neighbour in known and position < neighbour:
                    x1, y1 = self._room_box(position)
                    x2, y2 = self._room_box(neighbour)
                    canvas.create_line(x1 + half, y1 + half, x2 + half,
                                       y2 + half, fill=COLORS["edge"], width=3)
        for position in known:
            x, y = self._room_box(position)
            visited = position in state.visited
            if position == state.position:
                outline = COLORS["torch"]
            elif position == BOSS_ROOM:
                outline = COLORS["blood"]
            else:
                outline = COLORS["edge"]
            canvas.create_rectangle(
                x, y, x + ROOM_SIZE, y + ROOM_SIZE,
                fill=COLORS["raised"] if visited else COLORS["bg"],
                outline=outline, width=3 if position == state.position else 2)
            centre_x, centre_y = x + half, y + half
            if position == state.position:
                canvas.create_oval(centre_x - 9, centre_y - 9, centre_x + 9,
                                   centre_y + 9, fill=COLORS["torch"],
                                   outline="")
            elif not visited:
                canvas.create_text(centre_x, centre_y, text="?",
                                   fill=COLORS["muted"], font=HEAD_FONT)
            elif state.rooms[position]["monsters"]:
                canvas.create_rectangle(centre_x - 7, centre_y - 7,
                                        centre_x + 7, centre_y + 7,
                                        fill=COLORS["blood"], outline="")
            if position == BOSS_ROOM:
                canvas.create_text(x + half, y + ROOM_SIZE - 9, text="BOSS",
                                   fill=COLORS["blood"], font=SMALL_FONT)
