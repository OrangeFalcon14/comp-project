import json
import pygame

NEIGHBOR_OFFSETS = [
    (0, -2),
    (0, 2),
    (-1, 0),
    (-1, -1),
    (0, -1),
    (1, -1),
    (1, 0),
    (0, 0),
    (-1, 1),
    (0, 1),
    (1, 1),
]
PHYSICS_TILES = {"floor", "stone", "wall_with_pillar", "large_floor", "half_floor"}
HALF_TILES = {"half_floor"}
NON_RENDER_TILES = {
    "skeleton_spawner",
    "player_spawner",
    "skeleton_path_mirror",
    "player_collision_detector",
}


class Tilemap:
    def __init__(self, game, tile_size=32):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {}
        self.offgrid_tiles = []

    def save(self, path):
        f = open(path, "w")
        json.dump(
            {
                "tilemap": self.tilemap,
                "tile_size": self.tile_size,
                "offgrid": self.offgrid_tiles,
            },
            f,
        )
        f.close()

    def load(self, path):
        f = open(path, "r")
        map_data = json.load(f)
        f.close()

        self.tilemap = map_data["tilemap"]
        self.tile_size = map_data["tile_size"]
        self.offgrid_tiles = map_data["offgrid"]
        # print(self.offgrid_tiles)

    def tiles_around(self, pos):
        tiles = []
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in NEIGHBOR_OFFSETS:
            check_loc = (
                str(tile_loc[0] + offset[0]) + ";" + str(tile_loc[1] + offset[1])
            )
            if check_loc in self.tilemap:
                tiles.append(self.tilemap[check_loc])
        return tiles

    def physics_rects_around(self, pos):
        # pos = self.game.player.rect().center
        rects = []
        for tile in self.tiles_around(pos):
            if tile["type"] in PHYSICS_TILES:
                rects.append(
                    pygame.Rect(
                        tile["pos"][0] * self.tile_size,
                        tile["pos"][1] * self.tile_size,
                        self.tile_size,
                        (
                            self.tile_size * 1
                            if tile["type"] not in HALF_TILES
                            else self.tile_size * 0.5
                        ),
                    )
                )
        return rects

    def render(self, surf, offset=(0, 0)):
        for x in range(
            offset[0] // self.tile_size,
            (offset[0] + surf.get_width()) // self.tile_size + 1,
        ):
            for y in range(
                offset[1] // self.tile_size,
                (offset[1] + surf.get_height()) // self.tile_size + 1,
            ):
                loc = str(x) + ";" + str(y)
                if loc in self.tilemap:
                    tile = self.tilemap[loc]
                    if tile["type"] == "skeleton_path_mirror":
                        continue
                    surf.blit(
                        self.game.assets[tile["type"]][tile["variant"]],
                        (
                            tile["pos"][0] * self.tile_size - offset[0],
                            tile["pos"][1] * self.tile_size - offset[1],
                        ),
                    )

        for tile in self.offgrid_tiles:
            if tile["type"] in NON_RENDER_TILES:
                continue
            surf.blit(
                self.game.assets[tile["type"]][tile["variant"]],
                (tile["pos"][0] - offset[0], tile["pos"][1] - offset[1]),
            )
