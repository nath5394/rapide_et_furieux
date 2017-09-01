#!/usr/bin/env python3

import pygame

from . import assets
from .gfx.tiles import Tile
from .gfx.tiles import TileSelector
from . import util


CAPTION = "Rapide et Furieux - Level editor"

TILE_SELECTOR_LAYER = 10
TILE_SELECTOR_ARROWS_LAYER = 15


def main():
    print(CAPTION)

    print("Loading ...")
    pygame.init()
    screen = util.set_default_resolution()
    pygame.display.set_caption(CAPTION)

    tiles = [Tile(tile_rsc) for tile_rsc in assets.TILES]
    tiles = TileSelector(tiles, screen)

    util.register_drawer(TILE_SELECTOR_LAYER, tiles)
    for control in tiles.controls:
        util.register_drawer(TILE_SELECTOR_ARROWS_LAYER, control)

    util.main_loop(screen)
