import asyncio
import importlib.util
import os
from collections import defaultdict
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame


class GameSmokeTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location(
            "game_under_test", Path(__file__).resolve().parents[1] / "main.py"
        )
        self.game = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.game)
        self.game.clock = Mock()
        self.addCleanup(pygame.quit)

    def run_frame(self, events=(), pressed=()):
        keys = defaultdict(bool, {key: True for key in pressed})
        quit_event = pygame.event.Event(pygame.QUIT)
        with (
            patch.object(pygame.event, "get", return_value=[*events, quit_event]),
            patch.object(pygame.key, "get_pressed", return_value=keys),
            patch.object(pygame.display, "flip", wraps=pygame.display.flip) as flip,
            patch.object(pygame, "quit"),
            patch.object(self.game.sys, "exit"),
        ):
            asyncio.run(self.game.main())
        self.assertEqual(flip.call_count, 1, "Every mission stage must display its frame")
        return self.game

    def test_earth_first_frame(self):
        game = self.run_frame()
        self.assertEqual(game.state, "EARTH_READY")
        self.assertNotEqual(tuple(game.screen.get_at((400, 200)))[:3], game.BLACK_HAZARD)

    def test_every_mission_stage_renders(self):
        for stage in (
            "COSMO_WALKING", "COUNTDOWN", "SPACE_ARCADE",
            "LUNAR_LANDING", "ROVER_DEPLOY", "LUNAR_ROAMING",
        ):
            with self.subTest(stage=stage):
                self.game.state = stage
                self.game.countdown_timer = 90
                self.game.rocket_y = 100
                self.game.rover_x = 450
                self.game.rover_y = self.game.lunar_ground_y - self.game.rover_h + 2
                self.run_frame()

    def test_space_starts_mission(self):
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
        game = self.run_frame(events=[event])
        self.assertEqual(game.state, "COSMO_WALKING")
        self.assertGreater(game.cosmo_x, 130)

    def test_space_and_rover_steering(self):
        for stage, position in (("SPACE_ARCADE", "rocket_x"), ("LUNAR_ROAMING", "rover_x")):
            with self.subTest(stage=stage):
                self.game.state = stage
                setattr(self.game, position, 400)
                self.game.rover_y = self.game.lunar_ground_y - self.game.rover_h + 2
                self.run_frame(pressed=[pygame.K_LEFT])
                self.assertLess(getattr(self.game, position), 400)

    def test_landing_thrust(self):
        self.game.state = "LUNAR_LANDING"
        self.game.rocket_y = 100
        self.game.rocket_vy = 1.0
        game = self.run_frame(pressed=[pygame.K_SPACE])
        self.assertLess(game.rocket_vy, 1.0)
        self.assertLess(game.fuel, 100.0)

    def test_restart_returns_to_earth(self):
        self.game.state = "LUNAR_ROAMING"
        self.game.mission_distance = 100.0
        self.game.score = 30
        self.game.fuel = 10.0
        self.game.steam_particles.append({"alpha": 1})
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r)
        with patch.object(self.game.random, "random", return_value=1.0):
            game = self.run_frame(events=[event])
        self.assertEqual(game.state, "EARTH_READY")
        self.assertEqual(game.mission_distance, 0.0)
        self.assertEqual(game.score, 0)
        self.assertEqual(game.fuel, 100.0)
        self.assertEqual(game.steam_particles, [])


if __name__ == "__main__":
    unittest.main()
