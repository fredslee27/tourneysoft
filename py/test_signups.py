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
        self.assertTrue(undo[0] == subj.do_remove_entrant)

    def test_gamelist1 (self):
        # Add one game.
        subj = signups.SignupsStore()
        self.assertIsNotNone(subj.gamelist)
        undo = subj.do_add_games([("PONG", "Pong", "PONG=Pong")])
        self.assertTrue(len(subj.gamelist) == 1)
        self.assertIsNotNone(undo)
        self.assertTrue(undo[0] == subj.do_remove_games)

    def test_gamelist2 (self):
        # Add two games, once at time.
        subj = signups.SignupsStore()
        self.assertIsNotNone(subj.gamelist)
        undo = subj.do_add_games([("PONG", "Pong", "PONG=Pong")])
        self.assertTrue(len(subj.gamelist) == 1)
        self.assertIsNotNone(undo)
        self.assertTrue(undo[0] == subj.do_remove_games)
        undo = subj.do_add_games([("ASTR", "Asteroids", "ASTR=Astroids")])
        self.assertTrue(len(subj.gamelist) == 2)
        self.assertIsNotNone(undo)
        self.assertTrue(undo[0] == subj.do_remove_games)

    def test_gamelist3 (self):
        # Add three games at once.
        subj = signups.SignupsStore()
        self.assertIsNotNone(subj.gamelist)
        undo = subj.do_add_games([
          ("PONG", "Pong", "PONG=Pong"),
          ("ASTR", "Asteroids", "ASTR=Asteroids"),
          ("POLP", "Pole Position", "POLP=Pole Position"),
          ])
        self.assertTrue(len(subj.gamelist) == 3)
        self.assertIsNotNone(undo)
        self.assertTrue(undo[0] == subj.do_remove_games)

    def test_gamelist3 (self):
        # Add three games at once.
        subj = signups.SignupsStore()
        self.assertIsNotNone(subj.gamelist)
        undo = subj.do_add_games([
          ("PONG", "Pong", "PONG=Pong"),
          ("ASTR", "Asteroids", "ASTR=Asteroids"),
          ("POLP", "Pole Position", "POLP=Pole Position"),
          ])
        self.assertTrue(len(subj.gamelist) == 3)
        self.assertIsNotNone(undo)
        self.assertTrue(undo[0] == subj.do_remove_games)
        # execute undo
        redo = undo[0](*undo[1])
        self.assertTrue(len(subj.gamelist) == 0)

    def test_gamelist4 (self):
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

        self.assertTrue(len(subj.gamelist) == 2)

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
        self.assertTrue(":".join([row[0] for row in subj.gamelist]) == "PONG:ASTR:POLP")

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
        self.assertTrue(":".join([row[0] for row in subj.gamelist]) == "PONG:ASTR:POLP")

        # Redo
        apply(*redo)
        self.assertTrue(len(subj.gamelist) == 2)
        self.assertTrue(":".join([row[0] for row in subj.gamelist]) == "PONG:POLP")

    def test_ui0 (self):
        subj = signups.SignupsUI()


if __name__ == "__main__":
    unittest.main()

