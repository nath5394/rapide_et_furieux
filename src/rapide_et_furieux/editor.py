#!/usr/bin/env python3

import pygame

from . import assets
from . import util
from .gfx import ui
from .gfx.tiles import Tile
from .gfx.tiles import TileSelector


CAPTION = "Rapide et Furieux - Level editor"

TILE_SELECTOR_LAYER = 100
TILE_SELECTOR_ARROWS_LAYER = 150
GRID_LAYER = 50


class Editor(object):
    def __init__(self, screen):
        tiles = [Tile(tile_rsc) for tile_rsc in assets.TILES]
        self.tiles = TileSelector(tiles, screen)

        self.arrow_up = ui.Arrow(assets.ARROW_UP)
        self.arrow_up.relative = (
            (self.tiles.size[0] / 2) - (self.arrow_up.size[0] / 2),
            0
        )
        self.arrow_down = ui.Arrow(assets.ARROW_DOWN)
        self.arrow_down.relative = (
            (self.tiles.size[0] / 2) - (self.arrow_down.size[0] / 2),
            screen.get_size()[1] - self.arrow_down.size[1]
        )

        tiles_offset = (
            self.tiles.size[1] - (self.tiles.size[1] % assets.TILE_SIZE[1])
        )
        self.controls = [
            (self.arrow_down, -tiles_offset),
            (self.arrow_up, tiles_offset),
        ]

        util.register_drawer(TILE_SELECTOR_LAYER, self.tiles)
        for control in [self.arrow_up, self.arrow_down]:
            util.register_drawer(TILE_SELECTOR_ARROWS_LAYER, control)
        util.register_drawer(GRID_LAYER, ui.Grid())
        util.register_event_listener(self.scroll_tileselector)

    def scroll_tileselector(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return
        position = pygame.mouse.get_pos()
        for (control, offset) in self.controls:
            if control.rect.collidepoint(position):
                self.tiles.relative = (
                    self.tiles.relative[0],
                    min(0, self.tiles.relative[1] + offset)
                )
                return


def main():
    print(CAPTION)

    print("Loading ...")
    pygame.init()
    screen = util.set_default_resolution()
    pygame.display.set_caption(CAPTION)

    Editor(screen)
    util.main_loop(screen)
