#!/usr/bin/env

import itertools
import heapq
import threading

import pygame

from . import Car
from ... import assets
from ... import util


class Waypoint(object):
    def __init__(self, position, reachable):
        self.position = (int(position[0]), int(position[1]))
        self.reachable = reachable
        self.score = 0
        self.paths = []
        self.checkpoint = None

    def __str__(self):
        return ("Waypoint: {} ({})".format(
            self.position,
            self.score
        ))

    def __repr__(self):
        return str(self)

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

    def __repr__(self):
        return str(self)

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
    COLOR_PATH = (0, 255, 0)

    def __init__(self, *args, waypoint_mgmt, **kwargs):
        super().__init__(*args, **kwargs)

        self.waypoints = waypoint_mgmt
        self.path = []

        util.register_animator(self.ia_move)

    def compute_controls(self, frame_interval):
        # TODO
        pass

    def ia_move(self, frame_interval):
        self.path = self.waypoints.compute_path(
            self.position, self.next_checkpoint
        )
        self.compute_controls(frame_interval)

    def draw(self, screen):
        super().draw(screen)
        if self.parent.debug:
            self.draw_ia_path(screen)

    def draw_ia_path(self, screen):
        parent_abs = self.parent.absolute
        path = [self.position] + self.path
        for (pa, pb) in zip(path, path[1:]):
            pygame.draw.line(
                screen,
                self.COLOR_PATH,
                (
                    pa[0] + parent_abs[0],
                    pa[1] + parent_abs[1],
                ),
                (
                    pb[0] + parent_abs[0],
                    pb[1] + parent_abs[1],
                ),
                3
            )


class WaypointManager(object):
    COLOR_UNREACHABLE = pygame.Color(200, 200, 200, 255)
    COLOR_REACHABLE = pygame.Color(0, 255, 0, 255)
    COLOR_PATH = pygame.Color(0, 255, 0, 255)

    def __init__(self):
        self.parent = None

        self.waypoints = set()
        self.paths = set()

        # closest points to each tile
        # (grid_x, grid_y) = set([waypoint_a, waypoint_b, ...])
        self.grid_waypoints = {}
        # checkpoint -> waypoint
        self.checkpoint_waypoints = {}

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
        paths = set()
        for d in data['paths']:
            paths.add(Path.unserialize(d, wpts))
        wm = WaypointManager()
        wm.waypoints = wpts.values()
        wm.paths = paths
        return wm

    def optimize(self, racetrack):
        # index checkpoints
        self.checkpoint_waypoints = {}
        for cp in racetrack.checkpoints:
            for wpt in self.waypoints:
                if wpt.position == cp.pt:
                    break
            else:
                raise Exception("No waypoint matching checkpoint {} !".format(
                    cp
                ))
            wpt.checkpoint = cp
            self.checkpoint_waypoints[cp] = wpt

        self.grid_waypoints = {}
        # for each tile, we want the closest possible waypoints
        # so:
        # - the waypoint in a given grid tile
        # - the waypoints in the adjacent tiles
        for wpt in self.waypoints:
            offsets = itertools.product(
                range(-1, 2, 1),
                range(-1, 2, 1),
            )
            for offset in offsets:
                pos = (
                    int((wpt.position[0] / assets.TILE_SIZE[0]) + offset[0]),
                    int((wpt.position[1] / assets.TILE_SIZE[1]) + offset[1]),
                )
                if pos not in self.grid_waypoints:
                    self.grid_waypoints[pos] = set()
                self.grid_waypoints[pos].add(wpt)

        # If there are no close waypoint (unlikely but possible):
        # - fallback on the waypoint closest to the center of the tile
        for tile_pos in racetrack.tiles.grid.keys():
            if tile_pos in self.grid_waypoints:
                continue
            center = (
                (tile_pos[0] * assets.TILE_SIZE[0]) + (assets.TILE_SIZE[0] / 2),
                (tile_pos[1] * assets.TILE_SIZE[1]) + (assets.TILE_SIZE[1] / 2),
            )
            closest = (0xFFFFFFFF, None)
            for wpt in self.waypoints:
                dist = util.distance_sq_pt_to_pt(center, wpt.position)
                if dist < closest[0]:
                    closest = (dist, wpt)
            assert(closest[1] is not None)
            self.grid_waypoints[tile_pos] = set()
            self.grid_waypoints[tile_pos].add(closest[1])

    def compute_path(self, origin, target):
        # turn the target checkpoint into a waypoint
        target = self.checkpoint_waypoints[target]

        #### simple A* algorithm to find the most likely best path

        unique = 0
        to_examine = self.grid_waypoints[
            int(origin[0] / assets.TILE_SIZE[0]),
            int(origin[1] / assets.TILE_SIZE[1]),
        ]
        to_examine = [
            (util.distance_sq_pt_to_pt(wpt.position, target.position),
             unique, wpt, None)
            for (unique, wpt) in enumerate(to_examine)
        ]
        heapq.heapify(to_examine)
        # visited: waypoint --> (best_source_origin, best_source_score)
        visited = {wpt[2]: (None, 0xFFFFFFFF) for wpt in to_examine}

        target_reached = False
        while not target_reached:
            try:
                (current_score, _, current, previous) = heapq.heappop(to_examine)
            except IndexError:
                raise Exception("[{}] Failed to find path for {} --> {} !"
                                .format(self, origin, target))

            for path in current.paths:
                if path.a is current:
                    next_pt = path.b
                else:
                    next_pt = path.a
                if next_pt is previous:
                    # don't go back
                    continue
                if next_pt is target:
                    target_reached = True

                if next_pt not in visited:
                    visited[next_pt] = (current, current_score)

                    score = util.distance_sq_pt_to_pt(
                        target.position, next_pt.position
                    )
                    unique += 1
                    heapq.heappush(
                        to_examine,
                        (score, unique, next_pt, current)
                    )
                else:
                    (best_source_origin, best_source_score) = visited[next_pt]
                    if current_score < best_source_score:
                        visited[next_pt] = (current, current_score)

        # rebuild the found path
        path = []
        current = target
        while current is not None and current is not origin:
            assert(current.position not in path)
            path.append(current.position)
            current = visited[current][0]
        path.reverse()
        return path
