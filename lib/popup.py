import pygame

from lib import utils


class PopupDialog:
    def __init__(self, game, title: str, message: str):
        self.game = game
        self.title = title
        self.message = message
        self.display = pygame.Surface(self.game.screen.get_size(), pygame.SRCALPHA, 32)

        self.display = self.display.convert_alpha()

        pygame.font.init()
        self.font_name = "BreatheFire.ttf"
        self.heading_font = pygame.font.Font(f"data/fonts/{self.font_name}", 50)
        self.text_font = pygame.font.SysFont("Ubuntu Mono", 30)

        self.player_img = utils.load_image("entities/player/idle/00.png")
        self.player_img = pygame.transform.scale_by(self.player_img, 6)

        self.opaqueness = 150

    def get_popup(self):

        self.display.fill((30, 30, 30, self.opaqueness))

        title_text_surface = self.heading_font.render(
            self.title, False, (200, 200, 200)
        )
        self.display.blit(
            title_text_surface, (30, self.game.screen.get_size()[1] - 400)
        )

        message_text_surface = self.text_font.render(
            self.message, True, (200, 200, 200), wraplength=1000
        )
        self.display.blit(
            message_text_surface, (200, self.game.screen.get_size()[1] - 275)
        )

        self.display.blit(self.player_img, (-225, self.game.screen.get_size()[1] - 525))
        return self.display
