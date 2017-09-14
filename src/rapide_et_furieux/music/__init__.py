import logging
import random

import pygame

from .. import assets
from .. import util


logger = logging.getLogger(__name__)


class MusicPlayer(object):
    def __init__(self, change_interval=90):
        self.change_interval = change_interval
        self.t = 0
        util.register_animator(self._change_track)

    def play_next(self):
        asset_music = random.sample(assets.MUSICS, 1)[0]
        logger.info("Playing: {}".format(asset_music))
        music = assets.get_resource(asset_music)

        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        pygame.mixer.music.load(music)
        pygame.mixer.music.set_volume(asset_music[2])
        pygame.mixer.music.play(-1)

    def _change_track(self, frame_interval):
        self.t += frame_interval
        if self.t < self.change_interval:
            return
        self.t = 0
        self.play_next()
