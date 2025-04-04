import pygame
import random


SWITCH_TIME = 0.3
JUMP_TIME = 0.4

GAME_OVER_FILE_POS = (952, 27)
GAME_OVER_SIZE = (381, 21)

SCORE_FILE_POS = (952, 0)
SCORE_CHAR_SIZE = (18, 21)
SCORE_FILE_PADDING = 2

RESTART_BUTTON_FILE_POS = (0, 0)
RESTART_BUTTON_SIZE = (72, 64)

WORLD_SPEED = 400
JUMP_SPEED = 30


class Creature:
    def __init__(self, x, speed, height, screen_height):
        self.pos = [x, screen_height - height - 16] # road height

        self.speed = speed
        self.redundant = False

        self.file_rect = None
        self.scorable = True

    def update(self, delta_time):
        self.pos[0] -= delta_time * self.speed

        if self.pos[0] <= 0:
            self.redundant = True
        
    def draw(self, screen: pygame.Surface, atlas: pygame.Surface): ...


class Cactus(Creature):
    SMALL_SIZE = (34, 70)
    BIG_SIZE = (50, 100)
    ADDITIONAL_BIG_SIZE = (102, 100)

    SMALL_START = (444, 0)
    SMALL_COUNT = 6

    BIG_START = (650, 0)
    BIG_COUNT = 4

    ADDITIONAL_BIG_START = (848, 0)

    def __init__(self, x, screen_height):
        match random.randint(0, 2):
            case 0: # small
                self.file_start = Cactus.SMALL_START
                self.size = Cactus.SMALL_SIZE
                self.id = random.randint(0, Cactus.SMALL_COUNT - 1)

            case 1: # big
                self.file_start = Cactus.BIG_START
                self.size = Cactus.BIG_SIZE
                self.id = random.randint(0, Cactus.BIG_COUNT - 1)

            case 2: # additional big
                self.file_start = Cactus.ADDITIONAL_BIG_START
                self.size = Cactus.ADDITIONAL_BIG_SIZE
                self.id = 0
                

        super().__init__(x, WORLD_SPEED, self.size[1] * 0.9, screen_height)

    def update(self, delta_time):
        super().update(delta_time)

        x = self.file_start[0] + self.size[0] * self.id

        self.file_rect = pygame.Rect((x, self.file_start[1]), self.size)

    def draw(self, screen: pygame.Surface, atlas: pygame.Surface):
        if self.file_rect:
            screen.blit(atlas, self.pos, self.file_rect)


class Bird(Creature):
    FILE_START = (256, 0)

    def __init__(self, x, screen_height):
        self.size = (92, 80)

        super().__init__(x, WORLD_SPEED, self.size[1], screen_height)

        self.pos[1] -= 62
        
        self.current_frame = 0
        self.timer = 0.0

    def update(self, delta_time):
        if self.timer < SWITCH_TIME:
            self.timer += delta_time
        else:
            self.timer -= SWITCH_TIME

            self.current_frame += 1
            self.current_frame %= 2

        super().update(delta_time)

        x = Bird.FILE_START[0] + self.current_frame * (self.size[0] + 2)

        self.file_rect = pygame.Rect((x, Bird.FILE_START[1]), self.size)

    def draw(self, screen: pygame.Surface, atlas: pygame.Surface):
        screen.blit(atlas, self.pos, self.file_rect)


class Dino(Creature):
    NORMAL_FILE_START = (1512, 0)
    NORMAL_SIZE = (88, 94)

    CRAWLING_FILE_START = (1864, 34)
    CRAWLING_SIZE = (118, 60)

    def __init__(self, x, screen_height):
        super().__init__(x, 0, Dino.NORMAL_SIZE[1], screen_height)

        self.current_frame = 0
        self.timer = 0.0
        self.screen_height = screen_height

        self.velocity = 0.0
        self.jump_timer = 3.5 * JUMP_TIME

        self.jumping = False
        self.crawling = False

    def get_size(self, index=None):
        if self.crawling:
            return Dino.CRAWLING_SIZE[index] if index is not None else Dino.CRAWLING_SIZE
        
        return Dino.NORMAL_SIZE[index] if index is not None else Dino.NORMAL_SIZE
    
    def get_file_start(self, index=None):
        if self.crawling:
            return Dino.CRAWLING_FILE_START[index] if index is not None else Dino.CRAWLING_FILE_START
        
        return Dino.NORMAL_FILE_START[index] if index is not None else Dino.NORMAL_FILE_START

    def update(self, delta_time):
        if self.timer < SWITCH_TIME:
            self.timer += delta_time
        else:
            self.timer -= SWITCH_TIME

            self.current_frame += 1
            self.current_frame %= 2

        if self.crawling:
            self.velocity += JUMP_SPEED * delta_time
        else:
            if self.jump_timer < JUMP_TIME: # jumping
                self.velocity -= JUMP_SPEED * delta_time
                self.jump_timer += 0.016
            else:
                self.velocity += JUMP_SPEED * delta_time

        self.pos[1] += self.velocity
        
        bottom_border = self.screen_height - 16 - self.get_size(1)

        if self.pos[1] > bottom_border:
            self.pos[1] = bottom_border
            self.jumping = False
            self.velocity = 0.0

        super().update(delta_time)

        size = self.get_size()

        x = self.get_file_start(0) + self.current_frame * size[0]
        y = self.get_file_start(1)

        self.file_rect = pygame.Rect((x, y), size)

    def draw(self, screen: pygame.Surface, atlas: pygame.Surface):
        screen.blit(atlas, self.pos, self.file_rect)


class Game:
    def __init__(self):
        self.width = 1024
        self.height = 768

        pygame.init()

        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()

        pygame.display.set_caption('Dino')

        self.atlas = pygame.image.load('assets/dino.png').convert_alpha()

        self.restart()
        self.high_score = 0

    def restart(self):
        self.segments = [0, self.width]
        
        self.player = Dino(self.width * 0.1, self.height)
        self.obstacles = []

        self.road_rect = pygame.Rect(0, 110, self.width, 16)
        self.dead = False

        self.score = 0

    def draw_score(self):
        str_score = str(self.score)
        
        score_x = self.width - (SCORE_CHAR_SIZE[0] + SCORE_FILE_PADDING) * len(str_score) - SCORE_FILE_PADDING

        offset_x = 0

        for char in str_score:
            digit = int(char)

            file_offset_x = digit * (SCORE_CHAR_SIZE[0] + SCORE_FILE_PADDING)
            rect = pygame.Rect((SCORE_FILE_POS[0] + file_offset_x, SCORE_FILE_POS[1]), SCORE_CHAR_SIZE)

            self.screen.blit(self.atlas, (score_x + offset_x, 0), rect)
            offset_x += SCORE_CHAR_SIZE[0] + SCORE_FILE_PADDING

    def draw_road(self):
        for seg in self.segments:
            self.screen.blit(self.atlas, (seg, self.height - 16), self.road_rect)

    def draw_obstacles(self):
        for o in self.obstacles:
            o.draw(self.screen, self.atlas)

    def update_road(self, delta_time):
        for i in range(len(self.segments)):
            self.segments[i] -= delta_time * WORLD_SPEED

            if self.segments[i] + self.width <= 0:
                self.segments[i] += self.width * 2

    def update_obstacles(self, delta_time):
        redundant = []

        for i, o in enumerate(self.obstacles):
            o.update(delta_time)

            if o.redundant:
                redundant.append(i)

        for i in redundant:
            del self.obstacles[i]

        offset = 0

        while len(self.obstacles) < 2:
            Obj = Bird if random.randint(0, 1) == 0 else Cactus

            self.obstacles.append(Obj(self.width * 1.5 + offset, self.height))
            offset += self.width * 0.5

    def update_player(self, delta_time, space_pressed, down_arrow_pressed, down_arrow_released):
        if space_pressed and not self.player.jumping and not self.player.crawling:
            self.player.jumping = True
            self.player.jump_timer = 0.0

        if down_arrow_pressed:
            self.player.crawling = True
            self.player.pos[1] -= Dino.CRAWLING_SIZE[1] - Dino.NORMAL_SIZE[1]

        if down_arrow_released:
            self.player.crawling = False
            self.player.pos[1] += Dino.CRAWLING_SIZE[1] - Dino.NORMAL_SIZE[1]

        self.player.update(delta_time)

    def die(self):
        self.dead = True
        self.high_score = self.score

    def check_collisions(self):
        player_rect = pygame.Rect(self.player.pos, self.player.get_size())

        for o in self.obstacles:
            obj_rect = pygame.Rect(o.pos, o.size)

            if player_rect.colliderect(obj_rect):
                self.die()

            if o.scorable and self.player.pos[0] > o.pos[0]:
                self.score += 1
                o.scorable = False

    def update_dead_screen(self, space_pressed, left_released):
        if not hasattr(self, 'restart_button_pos'):
            return

        restart_rect = pygame.Rect(self.restart_button_pos, RESTART_BUTTON_SIZE)
        mouse = pygame.mouse.get_pos()

        if space_pressed or left_released and restart_rect.contains(pygame.Rect(mouse, (1, 1))):
            self.restart()

    def draw_dead_screen(self):
        x = (self.width - GAME_OVER_SIZE[0]) / 2
        y = self.height / 2

        self.screen.blit(self.atlas, (x, y), pygame.Rect(GAME_OVER_FILE_POS, GAME_OVER_SIZE))

        y += 2.5 * GAME_OVER_SIZE[1]
        x = (self.width - RESTART_BUTTON_SIZE[0]) / 2

        self.restart_button_pos = (x, y)

        self.screen.blit(self.atlas, self.restart_button_pos, pygame.Rect(RESTART_BUTTON_FILE_POS, RESTART_BUTTON_SIZE))

    def main_loop(self, space_pressed, down_arrow_pressed, down_arrow_released, left_released):
        if self.dead:
            self.update_dead_screen(space_pressed, left_released)
            self.draw_dead_screen()
            return

        delta_time = self.clock.tick(75) / 1000.0

        self.update_road(delta_time)
        self.update_obstacles(delta_time)
        self.update_player(delta_time, space_pressed, down_arrow_pressed, down_arrow_released)

        self.check_collisions()

        self.screen.fill((0, 0, 0))

        self.draw_road()
        self.draw_obstacles()
        self.player.draw(self.screen, self.atlas)

        self.draw_score()

    def run(self):
        running = True

        while running:
            space_pressed = False
            down_arrow_pressed = False
            down_arrow_released = False
            left_released = False

            for e in pygame.event.get():
                match e.type:
                    case pygame.QUIT:
                        running = False

                    case pygame.KEYDOWN:
                        match e.key:
                            case pygame.K_SPACE:
                                space_pressed = True
                            case pygame.K_DOWN:
                                down_arrow_pressed = True

                    case pygame.KEYUP:
                        if e.key == pygame.K_DOWN:
                            down_arrow_released = True

                    case pygame.MOUSEBUTTONUP:
                        if e.button == 1: # left click
                            left_released = True

            self.main_loop(space_pressed, down_arrow_pressed, down_arrow_released, left_released)

            pygame.display.flip()

        pygame.quit()


if __name__ == '__main__':
    game = Game()
    game.run()
