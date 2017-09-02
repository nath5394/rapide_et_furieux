from .. import RelativeSprite


class RaceTrackObject(RelativeSprite):
    aligned_on_grid = False

    def __init__(self, resource, image=None):
        super().__init__(resource, image)

    def copy(self):
        return RaceTrackObject(self.resource, self.original)
