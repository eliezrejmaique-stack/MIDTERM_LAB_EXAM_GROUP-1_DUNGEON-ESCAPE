"""Dungeon Escape: start the game with   python main.py"""

import tkinter as tk

from ui import DungeonEscapeApp


def main():
    root = tk.Tk()
    DungeonEscapeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
