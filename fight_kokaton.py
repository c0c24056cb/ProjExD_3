import math
import os
import random
import sys
import time
import pygame as pg

WIDTH = 1100
HEIGHT = 650
NUM_OF_BOMBS = 5
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # カレントディレクトリ移動

def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate

#こうかとんクラス
class Bird:
    delta = {
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)
    imgs = {
        (+5, 0): img,
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),
        (-5, 0): img0,
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),
    }

    def __init__(self, xy: tuple[int, int]):
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5, 0)

    def change_img(self, num: int, screen: pg.Surface):
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if sum_mv != [0, 0]:
            self.dire = tuple(sum_mv)  # ← 移動したら向きを更新
            self.img = __class__.imgs[self.dire]
        screen.blit(self.img, self.rct)

#ビームクラス
class Beam:
    def __init__(self, bird:"Bird"):
        self.img = pg.image.load("fig/beam.png")
        self.rct = self.img.get_rect()
        self.rct.centery = bird.rct.centery
        self.rct.left = bird.rct.right
        self.vx, self.vy = +5, 0
        self.vx, self.vy = bird.dire  # ← 向きに応じた速度を取得
        self.vx *= 1
        self.vy *= 1
        img0 = pg.image.load("fig/beam.png")

        angle = math.degrees(math.atan2(-self.vy, self.vx))  # ← ビームの向きを計算
        self.img = pg.transform.rotozoom(img0, angle, 1.0)  # ← 回転したビーム画像
        self.rct = self.img.get_rect()

        # ← こうかとんの中心＋向きに応じたオフセットを計算
        offset_x = bird.rct.width * self.vx // 5
        offset_y = bird.rct.height * self.vy // 5
        self.rct.centerx = bird.rct.centerx + offset_x
        self.rct.centery = bird.rct.centery + offset_y

    def update(self, screen: pg.Surface):
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)

#爆弾クラス
class Bomb:
    def __init__(self, color: tuple[int, int, int], rad: int):
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)

#スコアクラス
class Score:
    def __init__(self):
        self.fonto = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        self.color = (0, 0, 255)
        self.score = 0
        self.img = self.fonto.render(f"Score: {self.score}", 0, self.color)
        self.rct = self.img.get_rect()
        self.rct.center = (100, HEIGHT - 50)

    def update(self, screen: pg.Surface):
        self.img = self.fonto.render(f"Score: {self.score}", 0, self.color)
        screen.blit(self.img, self.rct)

    def add_score(self, amount: int):
        self.score += amount

#爆発クラス
class Explosion:
    """爆発エフェクト用クラス"""
    def __init__(self, center: tuple[int, int]):
        img0 = pg.image.load("fig/explosion.gif")
        img1 = pg.transform.flip(img0, True, True)  # 上下左右反転画像も用意
        self.imgs = [img0, img1]
        self.rct = img0.get_rect()
        self.rct.center = center
        self.life = 10  # 爆発の寿命（フレーム数）

    def update(self, screen: pg.Surface):
        self.life -= 1
        screen.blit(self.imgs[self.life % 2], self.rct)  # フリップ画像を交互表示

#main関数
def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    beams: list[Beam] = []  # 複数ビーム用
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]
    explosions: list[Explosion] = []  # ← 爆発インスタンス用リストを追加！
    score = Score()
    clock = pg.time.Clock()
    tmr = 0

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.append(Beam(bird))

        screen.blit(bg_img, [0, 0])

        for bomb in bombs:
            if bird.rct.colliderect(bomb.rct):
                bird.change_img(8, screen)
                fonto = pg.font.Font(None, 80)
                txt = fonto.render("Game Over", True, (255, 0, 0))
                screen.blit(txt, [WIDTH//2-150, HEIGHT//2])
                pg.display.update()
                time.sleep(1)
                return

        # ビームと爆弾の衝突判定
        for beam in beams[:]:  # beams[:]でコピーを回す
            for j, bomb in enumerate(bombs):
                if bomb is not None and beam.rct.colliderect(bomb.rct):
                    beams.remove(beam)
                    explosions.append(Explosion(bomb.rct.center))  # ← 爆発インスタンス生成！
                    bombs[j] = None
                    bird.change_img(6, screen)
                    score.add_score(1)
                    break

        bombs = [b for b in bombs if b is not None]

        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)

        # ビームの更新と画面外削除
        new_beams = []
        for beam in beams:
            beam.update(screen)
            if check_bound(beam.rct) == (True, True):
                new_beams.append(beam)
        beams = new_beams

        for bomb in bombs:
            bomb.update(screen)

        # 爆発エフェクトの更新と寿命チェック
        new_explosions = []
        for exp in explosions:
            exp.update(screen)
            if exp.life > 0:
                new_explosions.append(exp)
        explosions = new_explosions

        score.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)

if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()

