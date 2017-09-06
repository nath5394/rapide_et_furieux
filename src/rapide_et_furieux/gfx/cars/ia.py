#!/usr/bin/env

import threading

import pygame

from . import Car


class Waypoint(object):
    def __init__(self, position, reachable, score):
        self.position = position
        self.reachable = reachable
        self.score = score

    def __str__(self):
        return ("Waypoint: {} ({}|{})".format(
            self.position,
            self.reachable,
            self.score
        ))


class Path(object):
    def __init__(self, a, b, score):
        self.a = a  # first waypoint
        self.b = b  # second waypoint
        self.score = score

    def __str__(self):
        return ("Path({}): {} | {}".format(
            self.score,
            self.a,
            self.b
        ))


class IACar(Car):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class WaypointDrawer(object):
    COLOR_UNREACHABLE = (200, 200, 200)
    COLOR_REACHABLE = (0, 200, 0)

    def __init__(self):
        self.parent = None
        self.waypoints = set()
        self.paths = set()
        self.lock = threading.Lock()

    def set_waypoints(self, waypoints):
        with self.lock:
            self.waypoints = waypoints

    def set_paths(self, paths):
        with self.lock:
            self.paths = paths

    def _draw(self, screen, parent_abs):
        for pt in self.waypoints:
            rect = pygame.Rect(
                (pt.position[0] - 5 + parent_abs[0],
                 pt.position[1] - 5 + parent_abs[1]),
                (10, 10)
            )
            pygame.draw.rect(
                screen,
                self.COLOR_REACHABLE
                if pt.reachable else self.COLOR_UNREACHABLE,
                rect
            )

    def draw(self, screen):
        with self.lock:
            self._draw(screen, self.parent.absolute)
