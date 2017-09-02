from .. import RelativeSprite
from ... import assets


import pygame


class Arrow(RelativeSprite):
    def __init__(self, resource):
        super().__init__(resource)


class Background(object):
    def __init__(self):
        pass

    def draw(self, screen):
        pygame.draw.rect(screen, (0, 0, 0),
                         ((0, 0), screen.get_size()))
