import logging

from .. import RelativeSprite


logger = logging.getLogger(__name__)


class RaceTrackObject(RelativeSprite):
    def __init__(self, resource, image=None):
        super().__init__(resource, image)

    def serialize(self):
        return self.resource

    @staticmethod
    def unserialize(self, data):
        return RaceTrackObject(data)

    def copy(self):
        return RaceTrackObject(self.resource, self.original)

    def add_to_racetrack(self, race_track, mouse_position):
        element = self.copy()
        abs_pos = race_track.absolute
        position = (
            mouse_position[0] - abs_pos[0],
            mouse_position[1] - abs_pos[1]
        )
        if position[0] < 0 or position[1] < 0:
            return
        element.parent = race_track
        element.relative = position
        logger.info("Adding static object: %s --> %s",
                    mouse_position, element.relative)
        race_track.add_object(element)

    def remove_from_racetrack(self, race_track, mouse_position):
        # TODO
        pass
