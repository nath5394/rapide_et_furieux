import pygame

from .. import assets


class RelativeSprite(pygame.sprite.Sprite):
    def __init__(self, resource, image=None):
        super().__init__()
        self.parent = None
        self.relative = (0, 0)

        self.resource = resource

        if image is None:
            image = assets.get_resource(resource[:2])

        self.image = self.original = image
        self.size = self.image.get_size()

    def destroy(self):
        self.image = self.original = None

    def get_absolute(self, parent=None):
        if parent is None:
            parent_abs = (0, 0)
        else:
            parent_abs = parent.absolute
        return (
            parent_abs[0] + self.relative[0],
            parent_abs[1] + self.relative[1],
        )

    @property
    def absolute(self):
        return self.get_absolute(self.parent)

    @property
    def rect(self):
        absolute = self.absolute
        return pygame.Rect(
            (absolute[0], absolute[1]),
            self.size
        )

    def draw(self, screen, parent=None):
        absolute = self.get_absolute(
            parent if parent is not None else self.parent
        )
        screen.blit(self.image, absolute, ((0, 0), self.size))


class RelativeGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.parent = None
        self.relative = (0, 0)

    def get_absolute(self, parent=None):
        if parent is None:
            parent_abs = (0, 0)
        else:
            parent_abs = parent.absolute
        return (
            parent_abs[0] + self.relative[0],
            parent_abs[1] + self.relative[1],
        )

    @property
    def absolute(self):
        return self.get_absolute(self.parent)

    def draw(self, screen, parent=None):
        if parent is None:
            return super().draw(screen)
        for sprite in self.sprites():
            sprite.draw(screen, parent)
