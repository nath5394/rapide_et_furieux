import itertools
import logging

import pygame

from .. import assets
from .. import util


logger = logging.getLogger(__name__)

g_channels = []
g_channel_idx = 0
g_screen_size = (0, 0)


def pre_init():
    pygame.mixer.pre_init(44100, -16, 1, 512)


def init(screen_size):
    global g_channels
    global g_screen_size

    nb = pygame.mixer.get_num_channels()
    g_channels = [pygame.mixer.Channel(idx) for idx in range(0, nb)]
    g_screen_size = screen_size


def play(sound, balance=(1.0, 1.0)):
    global g_channels
    global g_channel_idx

    sound = assets.get_resource(sound)

    for g_channel_idx in itertools.chain(
                range(g_channel_idx, len(g_channels)),
                range(0, g_channel_idx)
            ):
        if not g_channels[g_channel_idx].get_busy():
            break
    else:
        g_channel_idx += 1
        if g_channel_idx >= len(g_channels):
            g_channel_idx = 0
        g_channels[g_channel_idx].stop()

    channel = g_channels[g_channel_idx]

    channel.set_volume(*balance)
    channel.play(sound)


def play_from_screen(sound, relative_sprite):
    global g_screen_size

    w = g_screen_size[0]

    pos = relative_sprite.absolute
    size = relative_sprite.size
    pos = pos[0] + (size[0] / 2)

    balance_r = util.clamp(
        (pos + (w / 2)) / (2 * w),
        0.0, 1.0
    )
    balance_l = 1.0 - balance_r

    if balance_l != 0 and balance_r != 0:
        factor = min(
            1.0 / balance_l,
            1.0 / balance_r
        )
        balance_l *= factor
        balance_r *= factor

    play(sound, (balance_l, balance_r))
