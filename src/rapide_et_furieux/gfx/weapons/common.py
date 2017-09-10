import time

import pygame

from ... import assets


CATEGORY_GUNS = 0  # straight forward only
CATEGORY_GUIDED = 1  # guided
CATEGORY_COUNTER_MEASURES = 2  # backward only
NB_CATEGORIES = 3

CATEGORY_NAMES = {
    CATEGORY_GUNS: 'Guns',
    CATEGORY_GUIDED: 'Smart weapons',
    CATEGORY_COUNTER_MEASURES: 'Counter-measures',
}


EXPLOSION_SIZES = [20, 64, 128]
EXPLOSION_SURFACES = {} # size --> list of list of surfaces


def load_explosions():
    global EXPLOSION_SURFACES

    EXPLOSION_SURFACES = {}
    for size in EXPLOSION_SIZES:
        EXPLOSION_SURFACES[size] = []
        for imgs in assets.EXPLOSIONS:
            # first image give us the reference size
            src_imgs = [assets.load_image(img) for img in imgs]
            src_size = src_imgs[0].get_size()
            ratio = max(
                src_size[0] / size,
                src_size[1] / size,
            )
            dst_size = (
                src_size[0] / ratio,
                src_size[1] / ratio,
            )

            dst_imgs = []
            for src_img in src_imgs:
                img = pygame.transform.scale(
                    src_img,
                    (
                        int(src_img.get_size()[0] / ratio),
                        int(src_img.get_size()[1] / ratio),
                    )
                )
                dst_img = pygame.Surface(dst_size, pygame.SRCALPHA)
                dst_img.blit(
                    img,
                    (
                        int((dst_size[0] - img.get_size()[0]) / 2),
                        int((dst_size[1] - img.get_size()[0]) / 2),
                    )
                )
                dst_imgs.append(dst_img)
            EXPLOSION_SURFACES[size].append(dst_imgs)


class Explosion(object):
    def __init__(self, race_track, position, size, time):
        pass


class Weapon(object):
    MIN_FIRE_INTERVAL = 0.5

    def __init__(self, generator, car):
        self.parent = generator
        self.car = car
        self.car.weapon = self
        self.last_shot = 0

    def deactivate(self):
        pass

    def fire(self):
        n = time.time()
        if n - self.last_shot <= self.MIN_FIRE_INTERVAL:
            return False
        self.last_shot = n
        return True
