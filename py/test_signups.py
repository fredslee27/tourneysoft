#!/usr/bin/env python3

import unittest
import signups

class TestSignups (unittest.TestCase):
    def test_SignupsStore0 (self):
        subj = signups.SignupsStore()
        self.assertIsNotNone(subj.presetlist)
        self.assertTrue(len(subj.presetlist) > 1)
        self.assertIsNotNone(subj.entrantlist)
        self.assertTrue(len(subj.entrantlist) == 0)

    def test_SignupsStore1 (self):
        subj = signups.SignupsStore()
        self.assertIsNotNone(subj.presetlist)
        self.assertTrue(len(subj.presetlist) > 1)
        undo = subj.do_add_entrant("Alice", None)
        self.assertIsNotNone(undo)
        #self.assertTrue("do_remove_player" in undo[0])
        self.assertEqual(undo[0], subj.do_remove_entrant)

    def test_gamelist1 (self):
        # Add one game.
        subj = signups.SignupsStore()
        self.assertIsNotNone(subj.gamelist)
        undo = subj.do_add_games([("PONG", "Pong", "PONG=Pong")])
        self.assertEqual(len(subj.gamelist), 1)
        self.assertIsNotNone(undo)
        self.assertTrue(undo[0] == subj.do_remove_games)

    def test_gamelist2 (self):
        # Add two games, once at time.
        subj = signups.SignupsStore()
        self.assertIsNotNone(subj.gamelist)
        undo = subj.do_add_games([("PONG", "Pong", "PONG=Pong")])
        self.assertEqual(len(subj.gamelist), 1)
        self.assertIsNotNone(undo)
        self.assertEqual(undo[0], subj.do_remove_games)
        undo = subj.do_add_games([("ASTR", "Asteroids", "ASTR=Astroids")])
        self.assertTrue(len(subj.gamelist) == 2)
        self.assertIsNotNone(undo)
        self.assertEqual(undo[0], subj.do_remove_games)

    def test_gamelist3 (self):
        # Add three games at once.
        subj = signups.SignupsStore()
        self.assertIsNotNone(subj.gamelist)
        undo = subj.do_add_games([
          ("PONG", "Pong", "PONG=Pong"),
          ("ASTR", "Asteroids", "ASTR=Asteroids"),
          ("POLP", "Pole Position", "POLP=Pole Position"),
          ])
        self.assertEqual(len(subj.gamelist), 3)
        self.assertIsNotNone(undo)
        self.assertEqual(undo[0], subj.do_remove_games)

    def test_gamelist3 (self):
        # Add three games at once.
        subj = signups.SignupsStore()
        self.assertIsNotNone(subj.gamelist)
        undo = subj.do_add_games([
          ("PONG", "Pong", "PONG=Pong"),
          ("ASTR", "Asteroids", "ASTR=Asteroids"),
          ("POLP", "Pole Position", "POLP=Pole Position"),
          ])
        self.assertEqual(len(subj.gamelist), 3)
        self.assertIsNotNone(undo)
        self.assertEqual(undo[0], subj.do_remove_games)
        # execute undo
        redo = undo[0](*undo[1])
        self.assertEqual(len(subj.gamelist), 0)

    def test_gamelist4 (self):
        subj = signups.SignupsStore()
        self.assertIsNotNone(subj.gamelist)
        # Add three games.
        undo = subj.do_add_games([
          ("PONG", "Pong", "PONG=Pong"),
          ("ASTR", "Asteroids", "ASTR=Asteroids"),
          ("POLP", "Pole Position", "POLP=Pole Position"),
          ])
        self.assertEqual(len(subj.gamelist), 3)
        self.assertIsNotNone(undo)
        self.assertEqual(undo[0], subj.do_remove_games)

        # Remove one game.
        undo = subj.do_remove_games(['ASTR'])
        self.assertEqual(len(subj.gamelist), 2)
        self.assertIsNotNone(undo)
        self.assertFalse('ASTR' in [ row[0] for row in subj.gamelist ])
        self.assertEqual(undo[0], subj.do_add_games)

        self.assertEqual(len(subj.gamelist), 2)

    def test_gamelist5 (self):
        subj = signups.SignupsStore()
        self.assertIsNotNone(subj.gamelist)
        # Add three games.
        undo = subj.do_add_games([
          ("PONG", "Pong", "PONG=Pong"),
          ("ASTR", "Asteroids", "ASTR=Asteroids"),
          ("POLP", "Pole Position", "POLP=Pole Position"),
          ])
        self.assertTrue(len(subj.gamelist) == 3)
        self.assertIsNotNone(undo)
        self.assertTrue(undo[0] == subj.do_remove_games)

        # Remove one game.
        undo = subj.do_remove_games(['ASTR'])
        self.assertTrue(len(subj.gamelist) == 2)
        self.assertIsNotNone(undo)
        self.assertFalse('ASTR' in [ row[0] for row in subj.gamelist ])
        self.assertTrue(undo[0] == subj.do_add_games)

        # Undo remove.
        redo = apply(*undo)
        self.assertTrue(len(subj.gamelist) == 3)
        # check order
        self.assertEqual(":".join([row[0] for row in subj.gamelist]), "PONG:ASTR:POLP")

    def test_gamelist6 (self):
        subj = signups.SignupsStore()
        self.assertIsNotNone(subj.gamelist)
        # Add three games.
        undo = subj.do_add_games([
          ("PONG", "Pong", "PONG=Pong"),
          ("ASTR", "Asteroids", "ASTR=Asteroids"),
          ("POLP", "Pole Position", "POLP=Pole Position"),
          ])
        self.assertEqual(len(subj.gamelist), 3)
        self.assertIsNotNone(undo)
        self.assertEqual(undo[0], subj.do_remove_games)

        # Remove one game.
        undo = subj.do_remove_games(['ASTR'])
        self.assertEqual(len(subj.gamelist), 2)
        self.assertIsNotNone(undo)
        self.assertFalse('ASTR' in [ row[0] for row in subj.gamelist ])
        self.assertEqual(undo[0], subj.do_add_games)

        # Undo remove.
        redo = apply(*undo)
        self.assertEqual(len(subj.gamelist), 3)
        # check order
        self.assertEqual(":".join([row[0] for row in subj.gamelist]), "PONG:ASTR:POLP")

        # Redo
        apply(*redo)
        self.assertEqual(len(subj.gamelist), 2)
        self.assertEqual(":".join([row[0] for row in subj.gamelist]), "PONG:POLP")

    def test_gamelist7 (self):
        # Test ActionHistory.
        subj = signups.SignupsStore()
        history = signups.ActionHistory()
        self.assertIsNotNone(subj.gamelist)
        # Add three games, one at a time.
        history.advance(subj.do_add_games, [("PONG", "Pong", "PONG=Pong")])
        history.advance(subj.do_add_games, [("ASTR", "Asteroids", "ASTR=Asteroids")])
        history.advance(subj.do_add_games, [("POLP", "Pole Position", "POLP=Pole Position")])
        self.assertEqual(len(subj.gamelist), 3)
        self.assertEqual(len(history), 3)

        # Undo
        history.backtrack()
        self.assertEqual(len(subj.gamelist), 2)
        self.assertEqual(":".join(row[0] for row in subj.gamelist), "PONG:ASTR")

        # Redo
        history.foretrack()
        self.assertEqual(len(subj.gamelist), 3)
        self.assertEqual(":".join(row[0] for row in subj.gamelist), "PONG:ASTR:POLP")

        # Double undo
        history.backtrack()
        history.backtrack()
        self.assertEqual(len(subj.gamelist), 1)
        self.assertEqual(":".join(row[0] for row in subj.gamelist), "PONG")

        # One redo
        history.foretrack()
        self.assertEqual(len(subj.gamelist), 2)
        self.assertEqual(":".join(row[0] for row in subj.gamelist), "PONG:ASTR")

        # Redo again
        history.foretrack()
        self.assertEqual(len(subj.gamelist), 3)
        self.assertEqual(":".join(row[0] for row in subj.gamelist), "PONG:ASTR:POLP")

        return

    def test_ui0 (self):
        subj = signups.SignupsUI()


if __name__ == "__main__":
    unittest.main()

