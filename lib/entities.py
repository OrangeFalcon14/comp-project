import pygame.transform
import pygame

from lib import constants, utils


class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {"up": False, "down": False, "right": False, "left": False}

        self.action = ""
        self.anim_offset = [0, -0]
        self.flip = False
        self.set_action("idle")

    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + "/" + self.action].copy()

    def update(self, tilemap, movement=(0, 0)):
        self.collisions = {"up": False, "down": False, "right": False, "left": False}

        frame_movement = (
            movement[0] + self.velocity[0],
            movement[1] + self.velocity[1],
        )

        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions["right"] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions["left"] = True
                self.pos[0] = entity_rect.x

        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions["down"] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions["up"] = True
                self.pos[1] = entity_rect.y

        if movement[0] > 0 or self.velocity[0] > 0:
            self.flip = False
        if movement[0] < 0 or self.velocity[0] < 0:
            self.flip = True

        self.velocity[1] = min(
            5, self.velocity[1] + (0.01 * constants.GRAVITY_CONSTANT)
        )

        if self.collisions["down"] or self.collisions["up"]:
            self.velocity[1] = 0

        self.animation.update()

    def render(self, surf, offset=(0, 0)):
        img = pygame.transform.scale_by(self.animation.img(), 1)

        surface = pygame.Surface(self.rect().size)
        surface.fill((255, 0, 0))
        surf.blit(
            pygame.transform.flip(img, self.flip, False),
            (
                self.pos[0]
                - img.width / 2
                + self.size[0] / 2
                - offset[0]
                + (self.anim_offset[0] * -1 if self.flip else 1),
                self.pos[1]
                - img.height
                + self.size[1]
                - offset[1]
                + self.anim_offset[1],
            ),
        )

        # surf.blit(
        #     surface,
        #     (self.pos[0] - offset[0], self.pos[1] - offset[1]),
        # )


class Skeleton(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, "skeleton", pos, size)
        self.velocity = [constants.ENEMY_SPEED, 0]
        self.animation.img_dur = 1
        self.health = constants.ENEMY_HEALTH
        self.time_since_damage = 0
        self.time_since_death = 0
        self.dead = False

    def get_mirror_rects(self):
        mirror_blocks = []
        for tile in self.game.tilemap.offgrid_tiles:
            if tile["type"] == "skeleton_path_mirror":
                rect = pygame.Rect(
                    tile["pos"][0],
                    tile["pos"][1],
                    10,
                    10,
                )
                mirror_blocks.append(rect)
        return mirror_blocks

    def update(self, tilemap):
        for block in self.get_mirror_rects():
            if self.rect().colliderect(block):
                self.velocity[0] = -self.velocity[0]

        self.time_since_damage += 1

        if self.dead:
            self.time_since_death += 1

        player = self.game.player

        if self.health <= 0:
            self.set_action("death")
            self.dead = True
            self.velocity = [0, 0]
            # self.time_since_death = 0
        elif self.time_since_damage > 8 * 5:
            self.set_action("walk")
        elif self.health >= 0:
            self.set_action("hit")

        if player.rect().colliderect(self.rect()) and not self.dead:
            if (
                player.action == "attack" or player.action == "attack_nomovement"
            ) and self.time_since_damage > 30:
                self.health -= 10
                self.time_since_damage = 0
                self.set_action("hit")

        super().update(tilemap, (0, 0))


class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, "player", pos, size)
        self.air_time = 0
        self.attack_time = 0
        self.attack_cooldown = 0
        self.turn_around_time = 0
        self.dead = False
        self.sprinting = False
        self.has_hit_wall = False
        self.respawn_pos = [0, 0]
        self.health = 60
        self.time_since_damage = 0
        self.time_since_death = 0
        self.time_since_collision = 0
        self.has_hit_collider = False

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        self.air_time += 1
        self.attack_cooldown = (
            0 if self.attack_cooldown == 0 else self.attack_cooldown - 1
        )
        if self.has_hit_collider:
            self.time_since_collision += 1

        if (
            self.health <= 0
            or self.air_time / 60 > 1.5
            and self.pos[1] > self.game.display.get_size()[1]
        ):
            self.dead = True
            self.time_since_death += 1
            self.set_action("death")

        if self.collisions["down"]:
            self.air_time = 0

        if self.dead:
            self.set_action("death")
        elif self.action == "turn_around":
            if self.turn_around_time < 5:
                self.turn_around_time += 1
            else:
                self.turn_around_time = 0
                self.set_action("idle")
        elif self.action == "attack" or self.action == "attack_nomovement":
            if self.attack_time < 20:
                self.attack_time += 1
                self.anim_offset[0] = 0
            else:
                self.attack_time = 0
                self.anim_offset[0] = 0
                self.set_action("idle")
        elif self.air_time > 4:
            if self.velocity[1] < 0:
                self.set_action("jump")
            else:
                self.set_action("jump")

        elif movement[0] != 0:
            self.set_action("run")
        else:
            self.set_action("idle")

        if self.action == "attack" and movement[0] == 0:
            self.set_action("attack_nomovement")

        if self.action in ["attack", "attack_nomovement"]:
            self.size = (74, 30)
            if self.flip:
                if self.attack_time <= 1:
                    self.pos[0] -= 50
                    self.anim_offset[0] = -50
                elif self.attack_time == 20:
                    self.size = (15, 30)
                    self.anim_offset[0] = 0
                    self.pos[0] += 50

        else:
            self.size = (15, 30)
            self.anim_offset[0] = 0

        self.time_since_damage += 1

        for skeleton in self.game.skeletons:
            rect = self.rect()
            if (
                rect.colliderect(skeleton.rect())
                and self.time_since_damage > 50
                and not self.attack_time > 0
                and not skeleton.dead
                and not skeleton.time_since_damage < 30
            ):
                self.health -= 10
                self.time_since_damage = 0
                self.game.heart_grow_animation_time = 60

        for tile in self.game.player_collision_detectors:
            rect = self.rect()
            tile_rect = pygame.Rect(tile["pos"][0], tile["pos"][1], 10, 10)
            if rect.colliderect(tile_rect):
                if (
                    tile["pos"][0] > 410
                    and tile["pos"][0] < 414
                    and constants.JUMP_STRENGTH < 2.5
                ):
                    self.has_hit_collider = True
                    if self.time_since_collision > 10:
                        self.game.popup_index = 0
                elif tile["pos"][0] > 759 and tile["pos"][0] < 805:
                    self.has_hit_collider = True
                    if self.time_since_collision > 60 * 0.25:
                        self.game.popup_index = 1
                elif (
                    tile["pos"][0] > 2082
                    and tile["pos"][0] < 2284
                    and constants.SPRINT_CONSTANT < 1.1
                ):
                    self.has_hit_collider = True
                    if self.time_since_collision > 60 * 0.25:
                        self.game.popup_index = 2

        if self.sprinting:
            if movement[0] > 0:
                self.velocity[0] = constants.SPRINT_CONSTANT - utils.clamp(
                    self.air_time * constants.DRAG_COEFFECIENT,
                    0,
                    constants.MAX_AIR_DRAG,
                )
            elif movement[0] < 0:
                self.velocity[0] = -constants.SPRINT_CONSTANT + utils.clamp(
                    self.air_time * constants.DRAG_COEFFECIENT,
                    0,
                    constants.MAX_AIR_DRAG,
                )
            else:
                self.velocity[0] = 0
        else:
            self.velocity[0] = 0
