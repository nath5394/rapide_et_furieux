import logging
import random

import pygame

from .. import assets
from .. import util


logger = logging.getLogger(__name__)


class MusicPlayer(object):
    def __init__(self, change_interval=40):
        self.min_change_interval = change_interval
        self.change_interval = 0
        self.t = 0
        self.playing = None
        util.register_animator(self._change_track)

    def play_next(self):
        asset_music = random.sample(assets.MUSICS, 1)[0]
        logger.info("Playing: {}".format(asset_music))
        self.playing = assets.get_resource(asset_music)
        self.change_interval = max(self.min_change_interval, asset_music[3])

        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        pygame.mixer.music.load(self.playing)
        pygame.mixer.music.set_volume(asset_music[2])
        pygame.mixer.music.play(-1)

    def stop(self):
        logger.info("Stopping music playback")
        self.t = 0
        util.unregister_animator(self._change_track)
        self.playing = None
        pygame.mixer.music.pause()
        pygame.mixer.music.stop()

    def _change_track(self, frame_interval):
        self.t += frame_interval
        if self.t < self.change_interval:
            return
        self.t = 0
        self.play_next()
