from math import exp
import sys

import pygame

from lib.popup import PopupDialog
from lib.utils import clamp, load_image, load_images, Animation
from lib.entities import Player, Skeleton
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
            "open_gate": load_images("tiles/gates/open"),
            "closed_gate": load_images("tiles/gates/closed"),
            "decorations": load_images("tiles/decorations"),
            "half_floor": load_images("tiles/blocks/half_floor"),
            "hearts": load_images("assets/hearts"),
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
            "skeleton/attack": Animation(load_images("entities/skeleton/attack")),
            "skeleton/death": Animation(load_images("entities/skeleton/death")),
            "skeleton/hit": Animation(load_images("entities/skeleton/hit")),
            "skeleton/idle": Animation(load_images("entities/skeleton/idle")),
            "skeleton/walk": Animation(load_images("entities/skeleton/walk")),
        }

        self.player = Player(self, (2000, 150), (15, 30))

        self.skeletons = []
        self.player_collision_detectors = []

        self.tilemap = Tilemap(self, tile_size=32)

        try:
            self.tilemap.load("data/maps/level1.json")
        except FileNotFoundError:
            pass

        self.setup()

        self.scroll = [0, 0]
        self.heart_grow_animation_time = 0

        self.popups = [
            PopupDialog(
                self,
                "JUMPING",
                "Uh oh. Looks like the player is too weak to jump up that block. Try changing the JUMP_STRENGTH variable in lib/constants.py\n\n\nDont forget to relaunch the app after making changes\nPress Enter to continue",
            ),
            PopupDialog(
                self,
                "SPRINT",
                "Uh oh. Looks like the player can't sprint to get past that gap. Search for the part which handles input in game.py and look for the L_SHIFT key. Fix any errors that you find\n\n\nPress Enter to continue",
            ),
            PopupDialog(
                self,
                "SPRINT SPEED",
                "Uh oh. Looks like the player can't sprint fast enough to get past that gap. Try tweaking his sprint speed until he is able to. Increment by small amounts.\n\n\nPress Enter to continue",
            ),
            PopupDialog(
                self,
                "ATTACK",
                "Uh oh. Looks like the player can't attack the skeletons. Search for the part which handles mouse input in game.py. Fix any errors that you find\n\n\nPress Enter to continue",
            ),
        ]

        self.popup_index = -1

    def setup(self):
        self.player.pos = self.player.respawn_pos.copy()
        self.player.dead = False
        self.player.health = 60
        self.player.time_since_death = 0
        self.skeletons.clear()
        for tile in self.tilemap.offgrid_tiles:
            if tile["type"] == "player_spawner":
                self.player.pos = tile["pos"].copy()
                self.player.respawn_pos = tile["pos"].copy()
            elif tile["type"] == "skeleton_spawner":
                self.skeletons.append(Skeleton(self, tile["pos"], (15, 30)))
            elif tile["type"] == "player_collision_detector":
                self.player_collision_detectors.append(tile)

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

            for i in range(len(self.skeletons) - 1, -1, -1):
                skeleton = self.skeletons[i]
                skeleton.update(self.tilemap)
                if skeleton.time_since_death >= 15 * 5 - 2:
                    self.skeletons.pop(i)
                skeleton.render(self.display, offset=render_scroll)

            """Handle Input"""
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if self.popup_index == -1:
                    if event.type == pygame.KEYDOWN:
                        if not self.player.dead:
                            if event.key == pygame.K_a:
                                self.movement[0] = True
                            if event.key == pygame.K_d:
                                self.movement[1] = True

                        if event.key == pygame.K_w or event.key == pygame.K_SPACE:
                            if self.player.air_time < 5:
                                self.player.velocity[1] = -constants.JUMP_STRENGTH * (
                                    1
                                    if not self.player.sprinting
                                    else constants.SPRINT_JUMP_HEIGHT_MULTIPLIER
                                )

                        if event.key == pygame.K_LSHIFT:
                            if self.player.air_time < 5:
                                self.player.sprinting = False

                    if event.type == pygame.KEYUP:
                        if event.key == pygame.K_a:
                            self.movement[0] = False
                        if event.key == pygame.K_d:
                            self.movement[1] = False
                        if event.key == pygame.K_LSHIFT:
                            self.player.sprinting = False

                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1 and self.player.attack_cooldown == 0:
                            self.player.attack_cooldown = constants.ATTACK_COOLDOWN * 60
                            self.player.set_action("jump")

                            if self.player.pos[0] > 2330 and (
                                self.player.action != "attack"
                                and self.player.action != "attack_nomovement"
                            ):
                                print(self.player.action)
                                self.popup_index = 3
                            # else:
                            #     self.player.set_action("attack_nomovement")
                else:
                    self.movement = [0, 0]
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            self.player.has_hit_collider = False
                            self.player.time_since_collision = 0
                            self.popup_index = -1
            if self.player.dead and (
                self.player.time_since_death >= 10 * 5
                or self.player.pos[1] > self.display.get_size()[1]
            ):
                self.setup()

            self.screen.blit(
                pygame.transform.scale(self.display, self.screen.get_size()), (0, 0)
            )

            scale_factor = 1
            if self.heart_grow_animation_time > 0:
                scale_factor = 1 + exp(
                    -((self.heart_grow_animation_time - 50) ** 2) / 20
                )
                self.heart_grow_animation_time -= 1

            heart_img = pygame.transform.scale_by(
                self.assets["hearts"][self.player.health // 10], 5 * scale_factor
            )

            self.screen.blit(
                heart_img,
                (50, self.screen.get_height() - 40 - heart_img.height),
            )

            if self.popup_index != -1:
                self.screen.blit(self.popups[self.popup_index].get_popup(), (0, 0))
            pygame.display.update()
            self.clock.tick(60)


if __name__ == "__main__":
    Game().run()
