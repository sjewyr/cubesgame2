import random
import sys
import pygame

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

pygame.font.init()


class Game:
    def __init__(self, screen: pygame.Surface):
        print("Отсоси мою жопу")
        self.screen = screen
        self.all_entities = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.player = Player()
        self.all_entities.add(self.player)
        self.enemies = pygame.sprite.Group()

    def tick(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == ADD_BULLET:
                playerx, playery = self.player.rect.center
                enemyx, enemyy = event.dict["pos"]
                dmg = event.dict["dmg"]
                vector = pygame.Vector2(x=playerx - enemyx, y=playery - enemyy)
                vector.normalize_ip()
                self.add_bullet(vector * 4, event.dict["pos"], dmg)
            if event.type == PLAYER_SHOOT:
                self.player_shoot(
                    self.player.old_direction.copy().normalize() * 7.5,
                    self.player.rect.center,
                )
            if event.type == ADD_ENEMY:
                self.add_enemy()
            if event.type == ENEMY_DIED:
                self.player.exp += 1
                if self.player.exp >= self.player.lvl * 10:
                    self.player.exp = 0
                    self.player.lvl += 1

            if event.type == PLAYER_DIED:
                return "Blin"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        for k, v in pygame.sprite.groupcollide(
            self.player_bullets, self.enemies, False, False
        ).items():
            v[0].get_shoot(self.player.dmg)
            k.kill()

        for k in pygame.sprite.spritecollide(self.player, self.bullets, False):
            self.player.get_shoot(k.dmg)
            k.kill()

        self.player.update()
        self.player_bullets.update()
        self.bullets.update()
        self.enemies.update()
        self.screen.fill((0, 0, 0))

        for entity in self.all_entities:
            self.screen.blit(entity.surf, entity.rect)

        my_font = pygame.font.SysFont("Comic Sans MS", 30)
        surf = my_font.render(
            f"{self.player.exp}/{self.player.lvl*10} ({self.player.lvl})",
            True,
            (255, 255, 255),
        )
        ratio = self.player.hp / self.player.mhp
        surf2 = my_font.render(
            f"{self.player.hp}/{self.player.mhp}",
            True,
            (255 * (1 - ratio), 255 * ratio, 0),
        )
        self.screen.blit(surf, (0, 0))
        self.screen.blit(surf2, (0, SCREEN_HEIGHT - 20))
        pygame.display.flip()

        clock.tick(60)

    def add_bullet(self, init_vel: tuple[int, int], pos: tuple[int, int], dmg):
        bullet = Bullet(init_vel, pos, dmg=dmg)
        self.all_entities.add(bullet)
        self.bullets.add(bullet)

    def add_enemy(self):
        enemy = Enemy(
            (random.randint(1, 5), random.randint(1, 5)),
            (10, 10),
            (0, 255, 0),
            (random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)),
        )
        self.enemies.add(enemy)
        self.all_entities.add(enemy)

    def player_shoot(self, init_vel: tuple[int, int], pos: tuple[int, int]):
        bullet = Bullet(init_vel, pos, color=(0, 0, 255), size=self.player.bullet_size)
        self.all_entities.add(bullet)
        self.player_bullets.add(bullet)


class BaseObj(pygame.sprite.Sprite):
    def __init__(
        self,
        init_vel: tuple[int, int],
        size: tuple[int, int],
        color: tuple[int, int, int],
        init_pos: tuple[int, int],
    ):
        self.surf = pygame.Surface(size)
        self.rect = self.surf.get_rect()
        self.rect.center = init_pos
        self.surf.fill(color)
        self.init_vel = init_vel
        super().__init__()


class Player(BaseObj):
    def __init__(self):
        self.direction = pygame.Vector2(0, 0)
        self.old_direction = pygame.Vector2(1, 0)
        self.shoot_interval = 333
        self.dmg = 50
        self.exp = 0
        self.mhp = 1000
        self.hp = 1000
        self.lvl = 1
        self.bullet_size = 15
        self.last_shot_time = pygame.time.get_ticks()  # Время последнего выстрела
        super().__init__(
            init_vel=(0, 0),
            size=(10, 10),
            color=(200, 255, 200),
            init_pos=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),
        )

    def update(self):
        keys = pygame.key.get_pressed()
        self.direction = pygame.Vector2(0, 0)

        if keys[pygame.K_UP]:
            self.direction[1] -= 1
        if keys[pygame.K_DOWN]:
            self.direction[1] += 1
        if keys[pygame.K_LEFT]:
            self.direction[0] -= 1
        if keys[pygame.K_RIGHT]:
            self.direction[0] += 1

        if self.direction.length() != 0:
            self.old_direction = self.direction
            self.rect.move_ip(self.direction.normalize() * 5)

        # Ограничение движения в пределах экрана
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        if self.rect.top <= 0:
            self.rect.top = 0
        if self.rect.bottom >= SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

        # Стрельба при зажатом пробеле
        if keys[pygame.K_z]:
            self.shoot()

    def shoot(self):
        current_time = pygame.time.get_ticks()  # Текущее время
        if (
            current_time - self.last_shot_time >= self.shoot_interval
        ):  # Проверяем интервал
            self.last_shot_time = current_time  # Обновляем время последнего выстрела
            pygame.event.post(pygame.event.Event(PLAYER_SHOOT))

    def get_shoot(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            pygame.event.post(pygame.event.Event(PLAYER_DIED))


class Enemy(BaseObj):
    def __init__(self, init_vel, size, color, init_pos):
        super().__init__(init_vel, size, color, init_pos)
        self.hp = 100
        self.dmg = 50
        self.shoot_interval = random.randint(
            1000, 3000
        )  # Интервал между выстрелами (1-3 секунды)
        self.last_shot_time = pygame.time.get_ticks()  # Время последнего выстрела

    def shoot(self):
        pygame.event.post(
            pygame.event.Event(ADD_BULLET, pos=self.rect.center, dmg=self.dmg)
        )

    def get_shoot(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            self.kill()
            pygame.event.post(pygame.event.Event(ENEMY_DIED))

    def update(self):
        super().update()
        current_time = pygame.time.get_ticks()  # Текущее время
        if (
            current_time - self.last_shot_time >= self.shoot_interval
        ):  # Проверяем интервал
            self.shoot()
            self.last_shot_time = current_time  # Обновляем время последнего выстрела
            self.shoot_interval = random.randint(1000, 3000)  # Задаём новый интервал


class Bullet(BaseObj):
    def __init__(
        self,
        init_vel: tuple[int, int],
        pos: tuple[int, int],
        color=(255, 0, 0),
        size=10,
        dmg=10,
    ):
        super().__init__(
            init_vel=init_vel, size=(size, size), color=color, init_pos=pos
        )
        self.dmg = dmg

    def update(self):
        self.rect.move_ip(self.init_vel)

        if (
            self.rect.left < -20
            or self.rect.right > SCREEN_WIDTH + 20
            or self.rect.top <= -20
            or self.rect.bottom >= SCREEN_HEIGHT + 20
        ):
            self.kill()


clock = pygame.time.Clock()

pygame.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

ADD_BULLET = pygame.USEREVENT + 1
ADD_ENEMY = pygame.USEREVENT + 2
PLAYER_SHOOT = pygame.USEREVENT + 3
ENEMY_DIED = pygame.USEREVENT + 4
PLAYER_DIED = pygame.USEREVENT + 5


def main(screen: pygame.Surface):
    scr = Game(screen)
    pygame.time.set_timer(ADD_ENEMY, 1500)
    while True:
        if scr.tick() == "Blin":
            break

    scr.screen.fill((0, 0, 0))
    my_font = pygame.font.SysFont("Comic Sans MS", 30)
    surf = my_font.render(f"Game Over", True, (255, 255, 255))
    scr.screen.blit(surf, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()


if __name__ == "__main__":
    main(screen)
