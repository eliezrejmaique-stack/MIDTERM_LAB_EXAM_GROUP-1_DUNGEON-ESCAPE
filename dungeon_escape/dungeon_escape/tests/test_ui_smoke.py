"""Smoke test for ui.py that needs no window.

A stand-in for the tkinter module is installed while ui.py is imported, so
every screen-drawing and button-handling line runs without a display.
(Real on-screen testing is the manual checklist in README.md.)
"""

import sys
import types
import unittest
from unittest.mock import MagicMock, patch


class UiSmokeTests(unittest.TestCase):
    def setUp(self):
        self.fake_tk = MagicMock()
        self.fake_tk.Listbox.return_value.curselection.return_value = (0,)
        patcher = patch.dict(sys.modules, {"tkinter": self.fake_tk})
        patcher.start()
        self.addCleanup(patcher.stop)
        sys.modules.pop("ui", None)
        import ui
        self.addCleanup(sys.modules.pop, "ui", None)
        self.root = MagicMock()
        self.root.after.side_effect = lambda delay, callback: callback()
        self.app = ui.DungeonEscapeApp(self.root)

    def press(self, key):
        self.app._on_key(types.SimpleNamespace(keysym=key))

    def test_start_screen_then_game_screen(self):
        self.assertEqual(self.app.screen, "start")
        self.press("Return")
        self.assertEqual(self.app.screen, "game")
        self.assertEqual(self.app.state.status, "playing")

    def test_keys_move_and_fight(self):
        self.press("Return")
        self.press("e")                                  # search the hall
        self.assertEqual(len(self.app.state.equipment), 1)
        self.press("d")                                  # east into the Armory
        self.assertEqual(self.app.state.position, (1, 0))
        self.assertTrue(self.app.state.in_combat())
        self.press("1")                                  # select target
        self.press("space")                              # attack it
        self.press("q")                                  # strike weakest
        self.assertGreater(self.app.state.turns, 1)

    def test_losing_shows_the_end_screen_and_enter_restarts(self):
        self.press("Return")
        self.app.state.player["hp"] = 1
        self.press("d")
        self.press("q")
        self.assertEqual(self.app.screen, "end")
        self.press("Return")
        self.assertEqual(self.app.screen, "game")
        self.assertEqual(self.app.state.position, (0, 0))

    def test_keys_ignored_on_start_screen(self):
        self.press("d")
        self.assertEqual(self.app.state.position, (0, 0))


if __name__ == "__main__":
    unittest.main()
