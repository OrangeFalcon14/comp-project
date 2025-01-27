import sys

import pygame

from lib.constants import RESOLUTION, SCALING_FACTOR
from lib.utils import load_image, load_images
from lib.tilemap import Tilemap

RENDER_SCALE = 2.0
FILE_PATH = "data/maps/level1.json"
NON_RENDER_TILES = {
    "skeleton_spawner",
    "player_spawner",
    "skeleton_path_mirror",
}


class Editor:
    def __init__(self):
        pygame.init()
        pygame.font.init()

        self.font = pygame.font.SysFont("Hack Nerd Font Mono", 20)

        pygame.display.set_caption("editor")
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.display = pygame.Surface(
            (
                RESOLUTION[0] / SCALING_FACTOR,
                RESOLUTION[1] / SCALING_FACTOR,
            )
        )

        self.clock = pygame.time.Clock()

        self.assets = {
            "floor": load_images("tiles/blocks/floor"),
            "large_floor": load_images("tiles/blocks/large_floor"),
            "rocks": load_images("tiles/blocks/rocks"),
            "wall": load_images("tiles/blocks/wall"),
            "wall_with_pillar": load_images("tiles/blocks/wall_with_pillar"),
            "pillar1": load_images("tiles/pillars/pillar1"),
            "pillar2": load_images("tiles/pillars/pillar1"),
            "pillar_broken": load_images("tiles/pillars/broken"),
            "open_gate": load_images("tiles/gates/open"),
            "closed_gate": load_images("tiles/gates/closed"),
            "half_floor": load_images("tiles/blocks/half_floor"),
            "decorations": load_images("tiles/decorations"),
            "player_spawner": load_images("entities/player/idle/"),
            "skeleton_spawner": load_images("entities/skeleton/idle/"),
            "skeleton_path_mirror": pygame.Surface((10, 10)),
        }

        self.movement = [False, False, False, False]

        self.tilemap = Tilemap(self, tile_size=32)

        try:
            self.tilemap.load(FILE_PATH)
        except FileNotFoundError:
            pass

        self.scroll = [0, 0]

        self.tile_list = list(self.assets)
        self.tile_group = 0
        self.tile_variant = 0

        self.clicking = False
        self.right_clicking = False
        self.shift = False
        self.ongrid = True
        self.fast = False

    def run(self):
        while True:
            self.display.blit(
                pygame.transform.scale_by(load_image("background.png"), 1),
                (0, 0),
            )

            self.scroll[0] += (self.movement[1] - self.movement[0]) * (
                2 if not self.fast else 6
            )
            self.scroll[1] += (self.movement[3] - self.movement[2]) * (
                2 if not self.fast else 6
            )
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.tilemap.render(self.display, offset=render_scroll)

            try:
                current_tile_img = self.assets[self.tile_list[self.tile_group]][
                    self.tile_variant
                ].copy()
                current_tile_img.set_alpha(100)
            except TypeError:
                current_tile_img = pygame.Surface((0, 0))

            mpos = pygame.mouse.get_pos()
            mpos = (mpos[0] / RENDER_SCALE, mpos[1] / RENDER_SCALE)
            tile_pos = (
                int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size),
                int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size),
            )

            if self.ongrid:
                self.display.blit(
                    current_tile_img,
                    (
                        tile_pos[0] * self.tilemap.tile_size - self.scroll[0],
                        tile_pos[1] * self.tilemap.tile_size - self.scroll[1],
                    ),
                )
            else:
                self.display.blit(current_tile_img, mpos)

            if self.clicking and self.ongrid:
                self.tilemap.tilemap[str(tile_pos[0]) + ";" + str(tile_pos[1])] = {
                    "type": self.tile_list[self.tile_group],
                    "variant": self.tile_variant,
                    "pos": tile_pos,
                }

            if self.right_clicking:
                tile_loc = str(tile_pos[0]) + ";" + str(tile_pos[1])
                if tile_loc in self.tilemap.tilemap:
                    del self.tilemap.tilemap[tile_loc]
                for tile in self.tilemap.offgrid_tiles.copy():
                    if tile["type"] not in NON_RENDER_TILES:
                        tile_img = self.assets[tile["type"]][tile["variant"]]
                    else:
                        tile_img = pygame.Surface((0, 0))
                    tile_r = pygame.Rect(
                        tile["pos"][0] - self.scroll[0],
                        tile["pos"][1] - self.scroll[1],
                        tile_img.get_width(),
                        tile_img.get_height(),
                    )
                    if tile_r.collidepoint(mpos):
                        self.tilemap.offgrid_tiles.remove(tile)

            self.display.blit(current_tile_img, (5, 5))
            type_text = self.font.render(
                "Type:" + str(self.tile_list[self.tile_group]), False, (255, 255, 255)
            )
            variant_text = self.font.render(
                "Variant: " + str(self.tile_variant + 1), False, (255, 255, 255)
            )
            self.display.blit(variant_text, (40, 5))
            self.display.blit(type_text, (40, 25))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.clicking = True
                        if not self.ongrid:
                            self.tilemap.offgrid_tiles.append(
                                {
                                    "type": self.tile_list[self.tile_group],
                                    "variant": self.tile_variant,
                                    "pos": (
                                        mpos[0] + self.scroll[0],
                                        mpos[1] + self.scroll[1],
                                    ),
                                }
                            )
                    if event.button == 3:
                        self.right_clicking = True
                    if self.shift:
                        if event.button == 4:
                            self.tile_variant = (self.tile_variant - 1) % len(
                                self.assets[self.tile_list[self.tile_group]]
                            )
                        if event.button == 5:
                            self.tile_variant = (self.tile_variant + 1) % len(
                                self.assets[self.tile_list[self.tile_group]]
                            )
                    else:
                        if event.button == 4:
                            self.tile_group = (self.tile_group - 1) % len(
                                self.tile_list
                            )
                            self.tile_variant = 0
                        if event.button == 5:
                            self.tile_group = (self.tile_group + 1) % len(
                                self.tile_list
                            )
                            self.tile_variant = 0
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False
                    if event.button == 3:
                        self.right_clicking = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_w:
                        self.movement[2] = True
                    if event.key == pygame.K_s:
                        self.movement[3] = True
                    if event.key == pygame.K_g:
                        self.ongrid = not self.ongrid
                    if event.key == pygame.K_o:
                        self.tilemap.save(FILE_PATH)
                    if event.key == pygame.K_LSHIFT:
                        self.shift = True
                    if event.key == pygame.K_LALT:
                        self.fast = True
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                    if event.key == pygame.K_w:
                        self.movement[2] = False
                    if event.key == pygame.K_s:
                        self.movement[3] = False
                    if event.key == pygame.K_LSHIFT:
                        self.shift = False
                    if event.key == pygame.K_LALT:
                        self.fast = False

            self.screen.blit(
                pygame.transform.scale(self.display, self.screen.get_size()), (0, 0)
            )
            pygame.display.update()
            self.clock.tick(60)


Editor().run()
