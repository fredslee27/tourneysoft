#!/usr/bin/env python3

import unittest
import signups

class TestSignups (unittest.TestCase):
    def test_SignupsStore0 (self):
        subj = signups.SignupsStore()
        self.assertIsNotNone(subj.gamelist)
        self.assertTrue(len(subj.gamelist) > 1)
        self.assertIsNotNone(subj.entrants)
        self.assertTrue(len(subj.entrants) == 0)

    def test_SignupsStore1 (self):
        subj = signups.SignupsStore()
        self.assertIsNotNone(subj.gamelist)
        self.assertTrue(len(subj.gamelist) > 1)
        undo = subj.do_add_entrant("Alice", [])
        self.assertIsNotNone(undo)
        self.assertTrue("do_remove_player" in undo[0])


if __name__ == "__main__":
    unittest.main()

