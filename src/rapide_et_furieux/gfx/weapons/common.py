import time

CATEGORY_GUNS = 0  # straight forward only
CATEGORY_GUIDED = 1  # guided
CATEGORY_COUNTER_MEASURES = 2  # backward only
NB_CATEGORIES = 3

CATEGORY_NAMES = {
    CATEGORY_GUNS: 'Guns',
    CATEGORY_GUIDED: 'Smart weapons',
    CATEGORY_COUNTER_MEASURES: 'Counter-measures',
}


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
