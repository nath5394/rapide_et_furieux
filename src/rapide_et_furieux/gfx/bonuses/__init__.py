#!/usr/bin/env python3

import random

from .. import assets
from .. import RelativeSprite


class Bonus(RelativeSprite):
    def __init__(self, parent):
        super().__init__(random.sample(assets.BONUSES, 1)[0])
        self.parent = parent

    def _get_position(self):
        return (
            self.relative[0] + (self.size[0] / 2),
            self.relative[1] + (self.size[1] / 2),
        )

    def _set_position(self, position):
        self.relative = (
            position[0] - (self.size[0] / 2),
            position[1] - (self.size[1] / 2),
        )

    position = property(_get_position, _set_position)

    def add_to_car(self, car):
        pass


class BonusGenerator(object):
    def __init__(self, race_track, game_settings, waypoint_mgmt):
        self.race_track = race_track
        self.game_settings = game_settings

        self.interval = game_settings['bonus_interval']
        self.remaining_time = self.interval

        self.wpts = [
            (wpt.score, wpt.position)
            for wpt in waypoint_mgmt.waypoints
        ]
        self.wpts.sort()
        self.wpt_sum = 0
        for wpt in self.wpts:
            self.wpt_sum += wpt[0]

    def add_bonus(self, frame_interval):
        self.remaining_time -= frame_interval
        if self.remaining_time > 0:
            return
        self.remaining_time = self.interval

        r = random.random() * self.wpt_sum
        for (score, position) in self.wpts:
            r -= score
            if r <= 0:
                break
        else:
            assert False

        bonus = Bonus(self.race_track)
        bonus.position = position
        self.race_track.add_bonus(bonus)
