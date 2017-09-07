#!/usr/bin/env

import threading

import pygame

from . import Car


class Waypoint(object):
    def __init__(self, position, reachable):
        self.position = (int(position[0]), int(position[1]))
        self.reachable = reachable
        self.score = 0
        self.paths = []

    def __str__(self):
        return ("Waypoint: {} ({}|{})".format(
            self.position,
            self.reachable,
            self.score
        ))

    def __hash__(self):
        return hash(self.position)

    def __eq__(self, o):
        return self.position == o.position

    def serialize(self):
        return {
            'position': self.position,
            'score': self.score,
        }

    @staticmethod
    def unserialize(data):
        wpt = Waypoint(data['position'], True)
        wpt.score = data['score']
        return wpt


class Path(object):
    def __init__(self, a, b, score):
        self.a = a  # first waypoint
        self.b = b  # second waypoint
        self.score = score  # bigger is worst

    def compute_score_length(self):
        self.score = (
            ((self.a.position[0] - self.b.position[0]) ** 2) +
            ((self.a.position[1] - self.b.position[1]) ** 2)
        )

    def __str__(self):
        return ("Path({}): {} | {}".format(
            self.score,
            self.a,
            self.b
        ))

    def __hash__(self):
        return hash((self.a, self.b))

    def __eq__(self, o):
        return (self.a, self.b) == (o.a, o.b)

    def serialize(self):
        return {
            'a': self.a.position,
            'b': self.b.position,
            'score': self.score,
        }

    @staticmethod
    def unserialize(data, wpts):
        pt_a = wpts[tuple(data['a'])]
        pt_b = wpts[tuple(data['b'])]
        p = Path(pt_a, pt_b, data['score'])
        pt_a.paths.append(p)
        pt_b.paths.append(p)
        return p


class IACar(Car):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class WaypointManager(object):
    COLOR_UNREACHABLE = pygame.Color(200, 200, 200, 255)
    COLOR_REACHABLE = pygame.Color(0, 255, 0, 255)
    COLOR_PATH = pygame.Color(0, 255, 0, 255)

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
            screen.fill(
                self.COLOR_REACHABLE
                if pt.reachable else self.COLOR_UNREACHABLE,
                rect
            )
        for path in self.paths:
            pygame.draw.line(
                screen,
                self.COLOR_PATH,
                (
                    path.a.position[0] + parent_abs[0],
                    path.a.position[1] + parent_abs[1],
                ),
                (
                    path.b.position[0] + parent_abs[0],
                    path.b.position[1] + parent_abs[1],
                )
            )

    def draw(self, screen):
        with self.lock:
            self._draw(screen, self.parent.absolute)

    def serialize(self):
        waypoints = [
            wpt.serialize()
            for wpt in self.waypoints
            if wpt.reachable
        ]
        paths = [path.serialize() for path in self.paths]
        return {
            'waypoints': waypoints,
            'paths': paths,
        }

    @staticmethod
    def unserialize(data):
        wpts = {}
        for d in data['waypoints']:
            w = Waypoint.unserialize(d)
            wpts[w.position] = w
        paths = []
        for d in data['paths']:
            paths.append(Path.unserialize(d, wpts))
        return (wpts.values(), paths)
