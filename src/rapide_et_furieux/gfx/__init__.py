import pygame

from .. import assets


class RelativeSprite(pygame.sprite.Sprite):
    def __init__(self, resource, image=None):
        super().__init__()
        self.parent = None
        self.relative = (0, 0)

        self.resource = resource

        if image is None:
            image = assets.get_resource(resource)

        self.image = self.original = image
        self.size = self.image.get_size()

    def destroy(self):
        self.image = self.original = None

    @property
    def absolute(self):
        if self.parent is None:
            parent_abs = (0, 0)
        else:
            parent_abs = self.parent.absolute
        return (
            parent_abs[0] + self.relative[0],
            parent_abs[1] + self.relative[1],
        )

    @property
    def rect(self):
        absolute = self.absolute
        return pygame.Rect(
            (absolute[0], absolute[1]),
            self.size
        )

    def draw(self, screen):
        screen.blit(self.image, self.absolute,
                    ((0, 0), self.size))


class RelativeGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.parent = None
        self.relative = (0, 0)

    @property
    def absolute(self):
        if self.parent is None:
            parent_abs = (0, 0)
        else:
            parent_abs = self.parent.absolute
        return (
            parent_abs[0] + self.relative[0],
            parent_abs[1] + self.relative[1],
        )
