#Groggio -- A Platform Jumping Game

# Music Credits:
# Caketown: https://opengameart.org/content/caketown-cuteplayful
# One: https://opengameart.org/content/one
# Happy Tune: https://opengameart.org/content/happy-tune
# Enchanted Festival: https://opengameart.org/content/enchanted-festival
# Fight them Until we Can't: https://opengameart.org/content/fight-them-until-we-cant
# File I/O:

import pygame as pg
import random
from settings import *
from sprites import *
from os import path

pg.mixer.pre_init(44100, -16, 2, 2048)

pg.mixer.init()

class Game:
    def __init__(self):

        # initialize game window

        pg.init()
        #pg.mixer.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        self.running = True
        self.font_name = pg.font.match_font(FONT_NAME)
        self.load_data()

    def load_data(self):

        # load the high score:

        self.dir = path.dirname(__file__)
        img_dir = path.join(self.dir, 'img')
        with open(path.join(self.dir, HS_FILE), 'r+') as f:
            try:
                self.highscore = int(f.read())
            except:
                self.highscore = 0

        # load spritesheet image

        img_dir = path.join(self.dir, 'img')
        self.spritesheet = Spritesheet(path.join(img_dir, SPRITESHEET))

        # load clouds:

        self.cloud_images = []
        for i in range(1, 4):
            self.cloud_images.append(pg.image.load(path.join(img_dir, 'cloud{}.png'.format(i))).convert())

        # load sounds

        self.sound_dir = path.join(self.dir, 'sound')
        self.jump_sound = pg.mixer.Sound(path.join(self.sound_dir, 'Jump2.wav'))
        self.jump_sound.set_volume(.1)
        self.boost_sound = pg.mixer.Sound(path.join(self.sound_dir, 'Jump1.wav'))
        self.boost_sound.set_volume(.1)

    def new(self):

        #start a new Game

        self.score = 0
        self.all_sprites = pg.sprite.LayeredUpdates()
        self.all_sprites = pg.sprite.Group()
        self.platforms = pg.sprite.Group()
        self.powerup = pg.sprite.Group()
        self.mob = pg.sprite.Group()
        self.cloud = pg.sprite.Group()
        self.player = Player(self)
        for plat in PLATFORM_LIST:
            Platform(self, *plat)
        self.mob_timer = 0
        pg.mixer.music.load(path.join(self.sound_dir, 'one.ogg'))
        for i in range(3):
            c = Cloud(self)
            c.rect.y += 500
        self.run()

    def run(self):

        # Game Loop

        pg.mixer.music.play(loops=-1)
        self.playing = True
        while self.playing:
            self.clock.tick(FPS)
            self.events()
            self.update()
            self.draw()
        pg.mixer.music.fadeout(500)

    def update(self):

        # Game Loop -- Update

        self.all_sprites.update()

        # spawn a mob?

        now = pg.time.get_ticks()
        if now - self.mob_timer > 5000 + random.choice([-1000, -500, 0, 500, 1000]):
            self.mob_timer = now
            Mob(self)

        # hit mobs?

        mob_hits = pg.sprite.spritecollide(self.player, self.mob, False, pg.sprite.collide_mask)
        if mob_hits:
            self.playing = False

        # check if player hits a platform -- only if falling

        if self.player.vel.y > 0:
            hits = pg.sprite.spritecollide(self.player, self.platforms, False)
            if hits:
                lowest = hits[0]
                for hit in hits:
                    if hit.rect.bottom > lowest.rect.bottom:
                        lowest = hit
                if self.player.pos.x < lowest.rect.right +9 and \
                self.player.pos.x > lowest.rect.left - 9:
                    if self.player.pos.y < lowest.rect.centery:
                        self.player.pos.y = lowest.rect.top
                        self.player.vel.y = 0
                        self.player.jumping = False

        # If player reaches the top 1/4 of the screen

        if self.player.rect.top <= HEIGHT / 4:
            if random.randrange(100) < 13:
                Cloud(self)
            self.player.pos.y += max(abs(self.player.vel.y), 3)
            for cloud in self.cloud:
                cloud_variance = random.randrange(1, 4)
                cloud_variance = int(cloud_variance)
                cloud.rect.y += max(abs(self.player.vel.y / cloud_variance), 2)
            for mob in self.mob:
                mob.rect.y += max(abs(self.player.vel.y), 3)
            for plat in self.platforms:
                plat.rect.y += max(abs(self.player.vel.y), 3)
                if plat.rect.top >= HEIGHT:
                    plat.kill()
                    self.score += 10

        # If player hits powerup:

        pow_hits = pg.sprite.spritecollide(self.player, self.powerup, True)
        for pow in pow_hits:
            if pow.type == 'boost':
                self.boost_sound.play()
                self.player.vel.y = -BOOST_POWER
                self.jumping = False

        # Die!

        if self.player.rect.bottom > HEIGHT:
            for sprite in self.all_sprites:
                sprite.rect.y -= max(self.player.vel.y, 10)
                if sprite.rect.bottom < 0:
                    sprite.kill()
        if len(self.platforms) == 0:
            self.playing = False

        # Spawn new platfroms to keep same average number of platforms

        while len(self.platforms) < 6:
            width = random.randrange(50, 100)
            Platform(self, random.randrange(0, WIDTH-width),
                    random.randrange(-75, -30))


    def events(self):

        # Game Loop - events

        for event in pg.event.get():

            #check for closing window

            if event.type == pg.QUIT:
                if self.playing:
                    self.playing = False
                self.running = False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    self.player.jump()
                if event.key == pg.K_UP:
                    self.player.jump()
            if event.type == pg.KEYUP:
                if event.key == pg.K_SPACE:
                    self.player.jump_cut()
            if event.type == pg.KEYUP:
                if event.key == pg.K_UP:
                    self.player.jump_cut()

    def draw(self):

        # Game Loop -- draw

        self.screen.fill(BGCOLOR)
        self.all_sprites.draw(self.screen)
        self.screen.blit(self.player.image, self.player.rect)
        self.draw_text(str(self.score), 22, WHITE, WIDTH / 2, 15)

        # 'after' drawing everything, flip the display

        pg.display.flip()

    def show_start_screen(self):

        #game splash screen

        pg.mixer.music.load(path.join(self.sound_dir, 'Caketown.ogg'))
        pg.mixer.music.play(loops=-1)
        self.screen.fill(BGCOLOR)
        self.draw_text(TITLE, 48, WHITE, WIDTH / 2, HEIGHT / 4)
        self.draw_text("Arrows to move, Space to jump", 22, WHITE, WIDTH / 2, HEIGHT / 2)
        self.draw_text("Press a key to play", 22, WHITE, WIDTH / 2, HEIGHT * 3 / 4)
        self.draw_text("High Score: " + str(self.highscore), 22, WHITE, WIDTH / 2, 15)
        pg.display.flip()
        self.wait_for_key()


    def show_go_screen(self):

        # game over

        if not self.running:
            return
        pg.mixer.music.load(path.join(self.sound_dir, 'ef.ogg'))
        pg.mixer.music.play(loops=-1)
        self.screen.fill(BGCOLOR)
        self.draw_text("GAME OVER", 48, WHITE, WIDTH / 2, HEIGHT / 4)
        self.draw_text("Score: " + str(self.score), 22, WHITE, WIDTH / 2, HEIGHT / 2)
        self.draw_text("Press a key to play again :)", 22, WHITE, WIDTH / 2, HEIGHT * 3 / 4)
        if self.score > self.highscore:
            self.highscore = self.score
            self.draw_text("NEW HIGH SCORE!", 22, WHITE, WIDTH / 2, HEIGHT / 2 + 40)
            with open(path.join(self.dir, HS_FILE), 'w') as f:
                f.write(str(self.score))
        else:
            self.draw_text("High Score: " + str(self.highscore), 22, WHITE, WIDTH / 2, HEIGHT / 2 + 40)

        pg.display.flip()
        self.wait_for_key()

    def wait_for_key(self):
        waiting = True
        while waiting:
            self.clock.tick(FPS)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    waiting = False
                    self.running = False
                if event.type == pg.KEYUP:
                    waiting = False

    def draw_text(self, text, size, color, x, y):
        font = pg.font.Font(self.font_name, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.midtop = (x, y)
        self.screen.blit(text_surface, text_rect)

g = Game()
g.show_start_screen()
while g.running:
    g.new()
    g.show_go_screen()
pg. quit()
