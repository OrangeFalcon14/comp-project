import sys

import pygame

from lib.utils import clamp, load_image, load_images, Animation
from lib.entities import Player
from lib.tilemap import Tilemap
import lib.constants as constants


class Game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption("ninja game")
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.display = pygame.Surface(
            (
                constants.RESOLUTION[0] / constants.SCALING_FACTOR,
                constants.RESOLUTION[1] / constants.SCALING_FACTOR,
            )
        )
        self.clock = pygame.time.Clock()

        self.movement = [False, False]

        self.assets = {
            "floor": load_images("tiles/blocks/floor"),
            "large_floor": load_images("tiles/blocks/large_floor"),
            "rocks": load_images("tiles/blocks/rocks"),
            "wall": load_images("tiles/blocks/wall"),
            "wall_with_pillar": load_images("tiles/blocks/wall_with_pillar"),
            "background": load_image("background.png"),
            "pillar1": load_images("tiles/pillars/pillar1"),
            "pillar2": load_images("tiles/pillars/pillar1"),
            "pillar_broken": load_images("tiles/pillars/broken"),
            "player/idle": Animation(load_images("entities/player/idle")),
            "player/run": Animation(load_images("entities/player/run")),
            "player/turn_around": Animation(load_images("entities/player/turn_around")),
            "player/jump": Animation(load_images("entities/player/jump")),
            "player/death": Animation(load_images("entities/player/death")),
            "player/fall": Animation(load_images("entities/player/fall")),
            "player/attack": Animation(load_images("entities/player/attack")),
            "player/attack_nomovement": Animation(
                load_images("entities/player/attack_nomovement")
            ),
        }

        self.player = Player(self, (200, 200), (15, 38))

        self.tilemap = Tilemap(self, tile_size=32)

        try:
            self.tilemap.load("data/maps/map.json")
        except FileNotFoundError:
            pass

        self.scroll = [0, 0]

    def run(self):
        while True:
            self.display.blit(
                pygame.transform.scale_by(self.assets["background"], 1),
                (0, 0),
            )

            self.scroll[0] += (
                self.player.rect().centerx
                - self.display.get_width() / 2
                - self.scroll[0]
            ) / 30
            self.scroll[1] += (
                self.player.rect().centery
                - self.display.get_height() / 2
                - self.scroll[1]
            ) / 30

            # self.scroll[0] = max(self.scroll[0], constants.HORIZONTAL_SCROLL_LIMIT)
            # self.scroll[1] = min(self.scroll[1], constants.VERTICAL_SCROLL_LIMIT)
            self.scroll[0] = clamp(
                self.scroll[0],
                constants.HORIZONTAL_SCROLL_LIMIT["min"],
                constants.HORIZONTAL_SCROLL_LIMIT["max"],
            )
            self.scroll[1] = clamp(
                self.scroll[1],
                constants.VERTICAL_SCROLL_LIMIT["min"],
                constants.VERTICAL_SCROLL_LIMIT["max"],
            )

            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.tilemap.render(self.display, offset=render_scroll)

            self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
            self.player.render(self.display, offset=render_scroll)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_w or event.key == pygame.K_SPACE:
                        self.player.velocity[1] = -3
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.movement[0] or self.movement[1]:
                            self.player.set_action("attack")
                        else:
                            self.player.set_action("attack_nomovement")
                    if event.button == 3:
                        self.player.set_action("death")

            self.screen.blit(
                pygame.transform.scale(self.display, self.screen.get_size()), (0, 0)
            )
            pygame.display.update()
            self.clock.tick(60)


if __name__ == "__main__":
    Game().run()
