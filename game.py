#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════
# NEON DEFENDER — single-file arcade shooter
# All assets (sprites, sounds, icon) are generated procedurally.
# Controls: WASD/Arrows move, SPACE shoot, F11 fullscreen, F3 scanlines,
#           ESC pause/menu
# ═══════════════════════════════════════════════════════════════

# ═══════════════════════ SECTION 1: IMPORTS & CONFIG ═══════════════════════
import pygame
import numpy as np
import math
import random
import json
import os
import sys
from dataclasses import dataclass, field
from typing import List, Tuple

pygame.init()

SOUND_ENABLED = True
try:
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()
except pygame.error:
    # No usable audio device on this machine (e.g. WASAPI can't find an
    # endpoint on some VMs/RDP sessions). Keep the game fully playable
    # without sound instead of crashing.
    SOUND_ENABLED = False

WIDTH, HEIGHT = 1024, 640
FPS = 60

SAVE_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "NeonDefender")
SAVE_PATH = os.path.join(SAVE_DIR, "save.json")

BLACK = (5, 6, 12)
NEON_CYAN = (60, 220, 255)
NEON_PINK = (255, 60, 180)
NEON_YELLOW = (255, 230, 80)
NEON_GREEN = (90, 255, 130)
NEON_RED = (255, 70, 70)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def load_save():
    try:
        with open(SAVE_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {"highscore": 0}


def write_save(data):
    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
        with open(SAVE_PATH, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


# ═══════════════════ SECTION 2: PROCEDURAL ASSET GENERATION ═══════════════════

def _glow_circle(radius, color, falloff=2.2):
    """Radial-gradient soft circle used as a base for sprites/particles/light."""
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = radius
    for y in range(size):
        for x in range(0, size, 2):  # step 2 for perf, then blit doubled column
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy) / radius
            if d > 1:
                continue
            a = int(255 * (1 - d) ** falloff)
            pygame.draw.line(surf, (*color, a), (x, y), (x + 1, y))
    return surf


def generate_player_sprite() -> pygame.Surface:
    w, h = 48, 56
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    body = [(w // 2, 2), (w - 6, h - 14), (w // 2, h - 22), (6, h - 14)]
    pygame.draw.polygon(surf, (20, 40, 60), body)
    pygame.draw.polygon(surf, NEON_CYAN, body, 3)
    pygame.draw.polygon(surf, (*NEON_CYAN, 90), [(w // 2, 10), (w - 14, h - 20), (w // 2, h - 26), (14, h - 20)])
    pygame.draw.circle(surf, (*NEON_PINK, 200), (w // 2, h // 2 - 4), 5)
    engine = pygame.Surface((16, 20), pygame.SRCALPHA)
    pygame.draw.polygon(engine, (*NEON_YELLOW, 160), [(8, 0), (16, 20), (0, 20)])
    surf.blit(engine, (w // 2 - 8, h - 18), special_flags=pygame.BLEND_RGBA_ADD)
    return surf


def generate_enemy_sprite(kind: str) -> pygame.Surface:
    w, h = 40, 40
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    if kind == "drone":
        pygame.draw.circle(surf, (40, 10, 20), (w // 2, h // 2), 14)
        pygame.draw.circle(surf, NEON_RED, (w // 2, h // 2), 14, 3)
        for a in range(0, 360, 45):
            x = w // 2 + int(18 * math.cos(math.radians(a)))
            y = h // 2 + int(18 * math.sin(math.radians(a)))
            pygame.draw.line(surf, (*NEON_RED, 120), (w // 2, h // 2), (x, y), 2)
    elif kind == "fighter":
        pts = [(w // 2, h - 4), (4, 6), (w // 2, 16), (w - 4, 6)]
        pygame.draw.polygon(surf, (40, 15, 5), pts)
        pygame.draw.polygon(surf, NEON_YELLOW, pts, 3)
    else:  # tank
        pygame.draw.rect(surf, (30, 10, 30), (4, 4, w - 8, h - 8), border_radius=6)
        pygame.draw.rect(surf, NEON_PINK, (4, 4, w - 8, h - 8), 3, border_radius=6)
        pygame.draw.circle(surf, NEON_PINK, (w // 2, h // 2), 6)
    return surf


def generate_boss_sprite() -> pygame.Surface:
    w, h = 140, 100
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, (40, 5, 20), (0, 10, w, h - 20))
    pygame.draw.ellipse(surf, NEON_RED, (0, 10, w, h - 20), 4)
    for i in range(6):
        x = 14 + i * (w - 28) // 5
        pygame.draw.circle(surf, NEON_YELLOW, (x, h - 18), 6)
    pygame.draw.circle(surf, (*NEON_PINK, 220), (w // 2, h // 2), 14)
    return surf


def generate_nebula_layer(seed, tint, density) -> pygame.Surface:
    rng = random.Random(seed)
    surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for _ in range(density):
        x, y = rng.randint(0, WIDTH), rng.randint(0, HEIGHT)
        r = rng.randint(30, 140)
        a = rng.randint(6, 22)
        blob = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(blob, (*tint, a), (r, r), r)
        surf.blit(blob, (x - r, y - r), special_flags=pygame.BLEND_RGBA_ADD)
    for _ in range(density * 6):
        x, y = rng.randint(0, WIDTH), rng.randint(0, HEIGHT)
        s = rng.choice([1, 1, 1, 2])
        b = rng.randint(120, 255)
        surf.fill((b, b, b, b), (x, y, s, s))
    return surf


class _SilentSound:
    """Drop-in stand-in for pygame.mixer.Sound when no audio device exists."""
    def play(self, *a, **kw):
        pass

    def set_volume(self, *a, **kw):
        pass


def synthesize_sound(freq=440.0, duration=0.15, wave="sine", decay=6.0, noise_amt=0.0):
    if not SOUND_ENABLED:
        return _SilentSound()
    sr = 44100
    n = int(sr * duration)
    t = np.linspace(0, duration, n, False)
    if wave == "sine":
        tone = np.sin(freq * 2 * np.pi * t)
    elif wave == "square":
        tone = np.sign(np.sin(freq * 2 * np.pi * t))
    elif wave == "saw":
        tone = 2 * (t * freq - np.floor(0.5 + t * freq))
    else:  # noise
        tone = np.random.uniform(-1, 1, n)
    if noise_amt > 0:
        tone = tone * (1 - noise_amt) + np.random.uniform(-1, 1, n) * noise_amt
    env = np.exp(-decay * t / duration)
    data = tone * env
    audio = np.clip(data * 32767 * 0.5, -32768, 32767).astype(np.int16)
    # The actual mixer may have been opened in stereo even though we asked
    # for mono (driver-dependent on some Windows machines) — match whatever
    # channel count pygame actually gave us, or make_sound raises a
    # "must be 2-dimensional" ValueError.
    init = pygame.mixer.get_init()
    channels = init[2] if init else 1
    if channels and channels > 1:
        audio = np.repeat(audio.reshape(-1, 1), channels, axis=1)
    return pygame.sndarray.make_sound(np.ascontiguousarray(audio))


def generate_icon_ico(path: str):
    try:
        from PIL import Image
        img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        px = img.load()
        cx = cy = 128
        for y in range(256):
            for x in range(256):
                d = math.hypot(x - cx, y - cy) / 128
                if d < 1:
                    a = int(255 * (1 - d) ** 1.5)
                    px[x, y] = (60, 220, 255, a)
        img.save(path, sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
    except Exception:
        pass


class Assets:
    """Lazily-built, cached procedural asset bank."""
    def __init__(self):
        self.player = generate_player_sprite()
        self.enemies = {k: generate_enemy_sprite(k) for k in ("drone", "fighter", "tank")}
        self.boss = generate_boss_sprite()
        self.parallax = [
            generate_nebula_layer(1, (30, 20, 60), 6),
            generate_nebula_layer(2, (20, 60, 90), 10),
            generate_nebula_layer(3, (255, 255, 255), 40),
            generate_nebula_layer(4, (255, 255, 255), 60),
            generate_nebula_layer(5, (255, 90, 200), 4),
        ]
        self.glow_small = _glow_circle(10, NEON_CYAN)
        self.glow_med = _glow_circle(24, NEON_PINK)
        self.font_big = pygame.font.Font(None, 72)
        self.font_mid = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 22)
        self.sfx_shoot = synthesize_sound(880, 0.08, "square", decay=10)
        self.sfx_explosion = synthesize_sound(90, 0.4, "noise", decay=3, noise_amt=1.0)
        self.sfx_hit = synthesize_sound(220, 0.12, "saw", decay=8)
        self.sfx_pickup = synthesize_sound(660, 0.2, "sine", decay=4)
        self.sfx_boss = synthesize_sound(60, 0.6, "noise", decay=2, noise_amt=0.7)


# ═══════════════════ SECTION 3: GRAPHICS ENGINE (post-fx) ═══════════════════

class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.shake_time = 0.0
        self.shake_mag = 0.0
        self.scanlines_on = True
        self._scan_cache = self._build_scanlines()

    def _build_scanlines(self):
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for y in range(0, HEIGHT, 2):
            pygame.draw.line(s, (0, 0, 0, 40), (0, y), (WIDTH, y))
        return s

    def trigger_shake(self, magnitude, duration):
        self.shake_mag = max(self.shake_mag, magnitude)
        self.shake_time = max(self.shake_time, duration)

    def update(self, dt):
        if self.shake_time > 0:
            self.shake_time -= dt
        else:
            self.shake_mag *= 0.9

    def shake_offset(self):
        if self.shake_time <= 0 and self.shake_mag < 0.5:
            return (0, 0)
        return (random.uniform(-1, 1) * self.shake_mag, random.uniform(-1, 1) * self.shake_mag)

    def apply_bloom(self, surface, threshold=180, passes=3, downscale=4):
        w, h = surface.get_size()
        bright = surface.copy()
        arr = pygame.surfarray.pixels3d(bright)
        mask = arr.sum(axis=2) < threshold
        arr[mask] = 0
        del arr
        small = pygame.transform.smoothscale(bright, (max(1, w // downscale), max(1, h // downscale)))
        for _ in range(passes):
            small = pygame.transform.smoothscale(small, (max(1, small.get_width() // 2), max(1, small.get_height() // 2)))
            small = pygame.transform.smoothscale(small, (max(1, small.get_width() * 2), max(1, small.get_height() * 2)))
        bloom = pygame.transform.smoothscale(small, (w, h))
        surface.blit(bloom, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        return surface

    def apply_chromatic_aberration(self, surface, amount):
        if amount <= 0:
            return surface
        w, h = surface.get_size()
        r = pygame.Surface((w, h))
        arr = pygame.surfarray.array3d(surface)
        red = np.roll(arr[:, :, 0], amount, axis=0)
        green = arr[:, :, 1]
        blue = np.roll(arr[:, :, 2], -amount, axis=0)
        out = np.dstack([red, green, blue])
        pygame.surfarray.blit_array(r, out)
        return r

    def apply_vignette(self, surface, cache=[None]):
        if cache[0] is None:
            v = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            cx, cy = WIDTH / 2, HEIGHT / 2
            maxd = math.hypot(cx, cy)
            for y in range(0, HEIGHT, 3):
                for x in range(0, WIDTH, 3):
                    d = math.hypot(x - cx, y - cy) / maxd
                    a = int(clamp((d - 0.55) * 260, 0, 170))
                    if a:
                        pygame.draw.rect(v, (0, 0, 0, a), (x, y, 3, 3))
            cache[0] = v
        surface.blit(cache[0], (0, 0))
        return surface

    def apply_scanlines(self, surface):
        if self.scanlines_on:
            surface.blit(self._scan_cache, (0, 0))
        return surface

    def apply_grain(self, surface, amount=6):
        w, h = surface.get_size()
        noise = (np.random.randint(-amount, amount, (w, h)))
        arr = pygame.surfarray.pixels3d(surface)
        for c in range(3):
            arr[:, :, c] = np.clip(arr[:, :, c].astype(int) + noise, 0, 255)
        del arr
        return surface


# ═══════════════════ SECTION 4: PARTICLE SYSTEMS ═══════════════════

@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    color: Tuple[int, int, int]
    size: float
    gravity: float = 0.0
    shrink: bool = True

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.life -= dt
        return self.life > 0

    def draw(self, surf):
        t = clamp(self.life / self.max_life, 0, 1)
        a = int(255 * t)
        s = self.size * (t if self.shrink else 1)
        if s < 0.5:
            return
        p = pygame.Surface((int(s * 2) + 2, int(s * 2) + 2), pygame.SRCALPHA)
        half = p.get_size()[0] // 2
        pygame.draw.circle(p, (*self.color, a), (half, half), max(1, int(s)))
        surf.blit(p, (self.x - p.get_width() / 2, self.y - p.get_height() / 2), special_flags=pygame.BLEND_RGBA_ADD)


class ParticleSystem:
    """Container managing every particle emitter kind requested."""
    def __init__(self):
        self.particles: List[Particle] = []
        self.shockwaves: List[dict] = []
        self.lightning: List[dict] = []

    def explosion(self, x, y, color=NEON_YELLOW, n=40):
        for _ in range(n):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(40, 260)
            self.particles.append(Particle(x, y, math.cos(ang) * spd, math.sin(ang) * spd,
                                            random.uniform(0.3, 0.9), 0.9, color, random.uniform(2, 5)))
        for _ in range(n // 2):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(10, 60)
            self.particles.append(Particle(x, y, math.cos(ang) * spd, math.sin(ang) * spd,
                                            random.uniform(0.6, 1.4), 1.4, (90, 90, 90), random.uniform(4, 9), gravity=-10))
        self.shockwaves.append({"x": x, "y": y, "r": 4, "max_r": 90, "life": 0.4, "max_life": 0.4})

    def engine_trail(self, x, y, dir_vec):
        for _ in range(2):
            jitter = random.uniform(-0.3, 0.3)
            vx = -dir_vec[0] * random.uniform(60, 140) + random.uniform(-20, 20)
            vy = -dir_vec[1] * random.uniform(60, 140) + random.uniform(-20, 20)
            self.particles.append(Particle(x, y, vx, vy, 0.35, 0.35, random.choice([NEON_CYAN, NEON_PINK]), random.uniform(2, 4)))

    def bullet_trail(self, x, y, color):
        self.particles.append(Particle(x, y, 0, 0, 0.15, 0.15, color, 3, shrink=True))

    def blood(self, x, y, color=NEON_RED, n=14):
        for _ in range(n):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(30, 150)
            self.particles.append(Particle(x, y, math.cos(ang) * spd, math.sin(ang) * spd,
                                            random.uniform(0.2, 0.5), 0.5, color, random.uniform(1, 3)))

    def stardust(self):
        if random.random() < 0.5:
            x = random.uniform(0, WIDTH)
            self.particles.append(Particle(x, -4, random.uniform(-5, 5), random.uniform(20, 60),
                                            2.5, 2.5, (200, 220, 255), random.uniform(1, 2), shrink=False))

    def lightning_arc(self, x1, y1, x2, y2, color=NEON_CYAN):
        self.lightning.append({"a": (x1, y1), "b": (x2, y2), "life": 0.15, "max_life": 0.15, "color": color})

    def update(self, dt):
        self.particles = [p for p in self.particles if p.update(dt)]
        for s in self.shockwaves:
            s["life"] -= dt
            t = 1 - clamp(s["life"] / s["max_life"], 0, 1)
            s["r"] = 4 + t * s["max_r"]
        self.shockwaves = [s for s in self.shockwaves if s["life"] > 0]
        for l in self.lightning:
            l["life"] -= dt
        self.lightning = [l for l in self.lightning if l["life"] > 0]

    def draw(self, surf):
        for p in self.particles:
            p.draw(surf)
        for s in self.shockwaves:
            t = clamp(s["life"] / s["max_life"], 0, 1)
            a = int(180 * t)
            pygame.draw.circle(surf, (*NEON_CYAN, a), (int(s["x"]), int(s["y"])), int(s["r"]), 3)
        for l in self.lightning:
            pts = [l["a"]]
            x1, y1 = l["a"]
            x2, y2 = l["b"]
            steps = 6
            for i in range(1, steps):
                t = i / steps
                pts.append((x1 + (x2 - x1) * t + random.uniform(-8, 8),
                            y1 + (y2 - y1) * t + random.uniform(-8, 8)))
            pts.append(l["b"])
            pygame.draw.lines(surf, l["color"], False, pts, 2)


# ═══════════════════ SECTION 5: GAME ENTITIES ═══════════════════

class Bullet:
    def __init__(self, x, y, vx, vy, color, owner="player", dmg=1):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.color = color
        self.owner = owner
        self.dmg = dmg
        self.alive = True
        self.r = 4

    def update(self, dt, particles):
        self.x += self.vx * dt
        self.y += self.vy * dt
        particles.bullet_trail(self.x, self.y, self.color)
        if self.x < -20 or self.x > WIDTH + 20 or self.y < -20 or self.y > HEIGHT + 20:
            self.alive = False

    def draw(self, surf, assets):
        glow = assets.glow_small
        surf.blit(glow, (self.x - glow.get_width() / 2, self.y - glow.get_height() / 2),
                   special_flags=pygame.BLEND_RGBA_ADD)
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.r)


class Player:
    def __init__(self, assets):
        self.sprite = assets.player
        self.x, self.y = WIDTH / 2, HEIGHT - 100
        self.speed = 320
        self.cooldown = 0.0
        self.fire_rate = 0.16
        self.lives = 3
        self.invuln = 0.0
        self.shield = False
        self.triple = 0.0
        self.speed_boost = 0.0
        self.dir_vec = (0, -1)

    def rect(self):
        return pygame.Rect(self.x - 18, self.y - 22, 36, 44)

    def update(self, dt, keys, particles, assets):
        vx = vy = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            vx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            vx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            vy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            vy += 1
        norm = math.hypot(vx, vy) or 1
        spd = self.speed * (1.6 if self.speed_boost > 0 else 1.0)
        self.x = clamp(self.x + vx / norm * spd * dt, 24, WIDTH - 24)
        self.y = clamp(self.y + vy / norm * spd * dt, 24, HEIGHT - 24)
        if vx or vy:
            self.dir_vec = (vx / norm, vy / norm)
        particles.engine_trail(self.x, self.y + 20, (0, 1))
        self.cooldown -= dt
        self.invuln = max(0, self.invuln - dt)
        self.triple = max(0, self.triple - dt)
        self.speed_boost = max(0, self.speed_boost - dt)

    def try_shoot(self, bullets, assets):
        if self.cooldown > 0:
            return
        self.cooldown = self.fire_rate
        assets.sfx_shoot.play()
        if self.triple > 0:
            for ang in (-0.28, 0, 0.28):
                bullets.append(Bullet(self.x, self.y - 24, math.sin(ang) * 500, -math.cos(ang) * 500, NEON_CYAN))
        else:
            bullets.append(Bullet(self.x, self.y - 24, 0, -560, NEON_CYAN))

    def hit(self, particles, assets):
        if self.invuln > 0:
            return False
        if self.shield:
            self.shield = False
            self.invuln = 1.0
            assets.sfx_hit.play()
            return False
        self.lives -= 1
        self.invuln = 2.0
        particles.explosion(self.x, self.y, NEON_CYAN, 24)
        assets.sfx_hit.play()
        return True

    def draw(self, surf, assets):
        if self.invuln > 0 and int(self.invuln * 12) % 2 == 0:
            return
        surf.blit(self.sprite, (self.x - self.sprite.get_width() / 2, self.y - self.sprite.get_height() / 2))
        if self.shield:
            pygame.draw.circle(surf, (*NEON_CYAN, 120), (int(self.x), int(self.y)), 34, 2)


class Enemy:
    KINDS = {
        "drone": dict(hp=1, speed=90, score=10, fire=1.6),
        "fighter": dict(hp=2, speed=140, score=20, fire=1.1),
        "tank": dict(hp=5, speed=55, score=40, fire=2.2),
    }

    def __init__(self, kind, x, y, assets):
        self.kind = kind
        stats = self.KINDS[kind]
        self.hp = stats["hp"]
        self.speed = stats["speed"]
        self.score = stats["score"]
        self.fire_cd = random.uniform(0.5, stats["fire"])
        self.fire_rate = stats["fire"]
        self.sprite = assets.enemies[kind]
        self.x, self.y = x, y
        self.alive = True
        self.t = random.uniform(0, 10)

    def update(self, dt, bullets, target_x):
        self.t += dt
        self.y += self.speed * dt
        self.x += math.sin(self.t * 2) * 40 * dt
        self.fire_cd -= dt
        if self.fire_cd <= 0 and 0 < self.y < HEIGHT - 40:
            self.fire_cd = self.fire_rate
            dx, dy = target_x - self.x, HEIGHT - self.y
            n = math.hypot(dx, dy) or 1
            bullets.append(Bullet(self.x, self.y, dx / n * 220, dy / n * 220, NEON_RED, owner="enemy"))
        if self.y > HEIGHT + 40:
            self.alive = False

    def rect(self):
        return pygame.Rect(self.x - 16, self.y - 16, 32, 32)

    def draw(self, surf):
        surf.blit(self.sprite, (self.x - self.sprite.get_width() / 2, self.y - self.sprite.get_height() / 2))


class Boss:
    def __init__(self, assets, hp):
        self.sprite = assets.boss
        self.x, self.y = WIDTH / 2, -80
        self.hp = hp
        self.max_hp = hp
        self.t = 0
        self.fire_cd = 1.0
        self.alive = True
        self.entering = True

    def rect(self):
        return pygame.Rect(self.x - 60, self.y - 40, 120, 80)

    def update(self, dt, bullets, target_x):
        self.t += dt
        if self.entering:
            self.y += 60 * dt
            if self.y >= 80:
                self.entering = False
            return
        self.x = WIDTH / 2 + math.sin(self.t * 0.6) * (WIDTH / 2 - 100)
        self.fire_cd -= dt
        if self.fire_cd <= 0:
            self.fire_cd = 0.5
            for ang in (-0.5, -0.2, 0, 0.2, 0.5):
                bullets.append(Bullet(self.x, self.y + 30, math.sin(ang) * 260, math.cos(ang) * 260 + 60,
                                       NEON_YELLOW, owner="enemy"))

    def draw(self, surf, assets):
        surf.blit(self.sprite, (self.x - self.sprite.get_width() / 2, self.y - self.sprite.get_height() / 2))
        w = 200
        pygame.draw.rect(surf, (40, 40, 40), (WIDTH / 2 - w / 2, 20, w, 10))
        pygame.draw.rect(surf, NEON_RED, (WIDTH / 2 - w / 2, 20, w * clamp(self.hp / self.max_hp, 0, 1), 10))


class Bonus:
    KINDS = ["life", "speed", "shield", "triple", "slow"]
    COLORS = {"life": NEON_GREEN, "speed": NEON_CYAN, "shield": NEON_YELLOW, "triple": NEON_PINK, "slow": (180, 180, 255)}

    def __init__(self, x, y):
        self.kind = random.choice(self.KINDS)
        self.x, self.y = x, y
        self.alive = True
        self.t = 0

    def update(self, dt):
        self.y += 80 * dt
        self.t += dt
        if self.y > HEIGHT + 20:
            self.alive = False

    def rect(self):
        return pygame.Rect(self.x - 12, self.y - 12, 24, 24)

    def draw(self, surf):
        c = self.COLORS[self.kind]
        r = 10 + math.sin(self.t * 6) * 2
        pygame.draw.circle(surf, c, (int(self.x), int(self.y)), int(r))
        pygame.draw.circle(surf, (255, 255, 255), (int(self.x), int(self.y)), int(r), 2)


# ═══════════════════ SECTION 6: UI & MENUS ═══════════════════

class HUD:
    def draw(self, surf, assets, player, score, wave, combo, highscore):
        for i in range(player.lives):
            pygame.draw.circle(surf, NEON_CYAN, (24 + i * 26, 26), 9)
        txt = assets.font_mid.render(f"SCORE {score}", True, NEON_CYAN)
        surf.blit(txt, (WIDTH - txt.get_width() - 20, 14))
        hs = assets.font_small.render(f"BEST {highscore}", True, (150, 200, 220))
        surf.blit(hs, (WIDTH - hs.get_width() - 20, 46))
        wtxt = assets.font_small.render(f"WAVE {wave}", True, NEON_PINK)
        surf.blit(wtxt, (WIDTH / 2 - wtxt.get_width() / 2, 14))
        if combo > 1:
            ctxt = assets.font_mid.render(f"x{combo} COMBO", True, NEON_YELLOW)
            surf.blit(ctxt, (WIDTH / 2 - ctxt.get_width() / 2, 40))


class MainMenu:
    def __init__(self, assets):
        self.assets = assets
        self.t = 0

    def update(self, dt):
        self.t += dt

    def draw(self, surf, highscore):
        title = self.assets.font_big.render("NEON DEFENDER", True, NEON_CYAN)
        pulse = 1 + 0.03 * math.sin(self.t * 3)
        title = pygame.transform.smoothscale(title, (int(title.get_width() * pulse), int(title.get_height() * pulse)))
        surf.blit(title, (WIDTH / 2 - title.get_width() / 2, 140))
        sub = self.assets.font_mid.render("Press SPACE to start", True, (200, 220, 255))
        if int(self.t * 2) % 2 == 0:
            surf.blit(sub, (WIDTH / 2 - sub.get_width() / 2, 300))
        hs = self.assets.font_small.render(f"Best score: {highscore}", True, NEON_PINK)
        surf.blit(hs, (WIDTH / 2 - hs.get_width() / 2, 360))
        ctrl = self.assets.font_small.render("WASD/Arrows move  •  SPACE shoot  •  F11 fullscreen  •  F3 scanlines", True, (140, 160, 190))
        surf.blit(ctrl, (WIDTH / 2 - ctrl.get_width() / 2, HEIGHT - 40))


class GameOverScreen:
    def __init__(self, assets):
        self.assets = assets

    def draw(self, surf, score, highscore, new_record):
        t = self.assets.font_big.render("GAME OVER", True, NEON_RED)
        surf.blit(t, (WIDTH / 2 - t.get_width() / 2, 180))
        s = self.assets.font_mid.render(f"Score: {score}", True, (255, 255, 255))
        surf.blit(s, (WIDTH / 2 - s.get_width() / 2, 260))
        if new_record:
            r = self.assets.font_mid.render("NEW RECORD!", True, NEON_YELLOW)
            surf.blit(r, (WIDTH / 2 - r.get_width() / 2, 300))
        h = self.assets.font_small.render(f"Best: {highscore}", True, (180, 200, 220))
        surf.blit(h, (WIDTH / 2 - h.get_width() / 2, 340))
        c = self.assets.font_small.render("Press SPACE to return to menu", True, (200, 220, 255))
        surf.blit(c, (WIDTH / 2 - c.get_width() / 2, 400))


# ═══════════════════ SECTION 7: MAIN GAME LOOP ═══════════════════

class Game:
    STATE_MENU, STATE_PLAY, STATE_OVER = "menu", "play", "over"

    def __init__(self):
        self.fullscreen = False
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("NEON DEFENDER")
        self.clock = pygame.time.Clock()
        self.assets = Assets()
        self.renderer = Renderer(self.screen)
        self.hud = HUD()
        self.menu = MainMenu(self.assets)
        self.gameover = GameOverScreen(self.assets)
        self.save = load_save()
        self.parallax_offset = [0.0] * 5
        self.reset_run()
        self.state = self.STATE_MENU

    def reset_run(self):
        self.player = Player(self.assets)
        self.bullets: List[Bullet] = []
        self.enemies: List[Enemy] = []
        self.bonuses: List[Bonus] = []
        self.boss = None
        self.particles = ParticleSystem()
        self.score = 0
        self.combo = 0
        self.combo_timer = 0.0
        self.wave = 0
        self.spawn_timer = 0.0
        self.wave_enemies_left = 0
        self.slowmo = 0.0
        self.time_slow_factor = 1.0

    def start_wave(self):
        self.wave += 1
        if self.wave % 5 == 0:
            self.boss = Boss(self.assets, hp=20 + self.wave * 4)
            self.assets.sfx_boss.play()
        else:
            self.wave_enemies_left = 5 + self.wave * 2
            self.spawn_timer = 0

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        flags = pygame.FULLSCREEN | pygame.SCALED if self.fullscreen else 0
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)

    def spawn_enemy(self):
        kind = random.choices(["drone", "fighter", "tank"], weights=[5, 3, max(1, self.wave - 2)])[0]
        x = random.uniform(40, WIDTH - 40)
        self.enemies.append(Enemy(kind, x, -30, self.assets))

    def handle_bonus_pickup(self, bonus):
        self.assets.sfx_pickup.play()
        if bonus.kind == "life":
            self.player.lives = min(5, self.player.lives + 1)
        elif bonus.kind == "speed":
            self.player.speed_boost = 6.0
        elif bonus.kind == "shield":
            self.player.shield = True
        elif bonus.kind == "triple":
            self.player.triple = 8.0
        elif bonus.kind == "slow":
            self.slowmo = 4.0

    def update_play(self, dt, keys):
        real_dt = dt
        if self.slowmo > 0:
            dt *= 0.5
            self.slowmo -= real_dt
        self.player.update(dt, keys, self.particles, self.assets)
        if keys[pygame.K_SPACE]:
            self.player.try_shoot(self.bullets, self.assets)

        if self.boss is None and self.wave_enemies_left <= 0 and not self.enemies:
            self.start_wave()

        if self.boss is None and self.wave_enemies_left > 0:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                self.spawn_timer = max(0.25, 1.0 - self.wave * 0.03)
                self.spawn_enemy()
                self.wave_enemies_left -= 1

        for b in self.bullets:
            b.update(dt, self.particles)
        self.bullets = [b for b in self.bullets if b.alive]

        for e in self.enemies:
            e.update(dt, self.bullets, self.player.x)
        self.enemies = [e for e in self.enemies if e.alive]

        if self.boss:
            self.boss.update(dt, self.bullets, self.player.x)

        for bo in self.bonuses:
            bo.update(dt)
        self.bonuses = [b for b in self.bonuses if b.alive]

        self.particles.stardust()
        self.particles.update(real_dt)
        self.renderer.update(real_dt)
        self.combo_timer -= real_dt
        if self.combo_timer <= 0:
            self.combo = 0

        self._handle_collisions()

        if self.player.lives <= 0:
            self.end_run()

    def _handle_collisions(self):
        player_rect = self.player.rect()
        for b in self.bullets:
            if b.owner != "player":
                continue
            hit_something = False
            for e in self.enemies:
                if e.alive and e.rect().collidepoint(b.x, b.y):
                    e.hp -= 1
                    hit_something = True
                    self.particles.blood(b.x, b.y, NEON_RED, 8)
                    if e.hp <= 0:
                        e.alive = False
                        self.particles.explosion(e.x, e.y, NEON_YELLOW, 36)
                        self.renderer.trigger_shake(6, 0.15)
                        self.assets.sfx_explosion.play()
                        self.combo += 1
                        self.combo_timer = 2.0
                        self.score += e.score * max(1, self.combo)
                        if random.random() < 0.18:
                            self.bonuses.append(Bonus(e.x, e.y))
                    break
            if self.boss and self.boss.alive and not self.boss.entering and self.boss.rect().collidepoint(b.x, b.y):
                self.boss.hp -= 1
                hit_something = True
                self.particles.blood(b.x, b.y, NEON_PINK, 6)
                if self.boss.hp <= 0:
                    self.boss.alive = False
                    for _ in range(6):
                        self.particles.explosion(self.boss.x + random.uniform(-40, 40),
                                                   self.boss.y + random.uniform(-20, 20), NEON_YELLOW, 50)
                    self.renderer.trigger_shake(14, 0.5)
                    self.assets.sfx_explosion.play()
                    self.score += 500
                    self.boss = None
            if hit_something:
                b.alive = False

        for b in self.bullets:
            if b.owner == "enemy" and player_rect.collidepoint(b.x, b.y):
                b.alive = False
                if self.player.hit(self.particles, self.assets):
                    self.renderer.trigger_shake(10, 0.3)

        for e in self.enemies:
            if e.alive and e.rect().colliderect(player_rect):
                e.alive = False
                self.particles.explosion(e.x, e.y, NEON_RED, 20)
                if self.player.hit(self.particles, self.assets):
                    self.renderer.trigger_shake(10, 0.3)

        for bo in self.bonuses:
            if bo.alive and bo.rect().colliderect(player_rect):
                bo.alive = False
                self.handle_bonus_pickup(bo)

    def end_run(self):
        new_record = self.score > self.save.get("highscore", 0)
        if new_record:
            self.save["highscore"] = self.score
            write_save(self.save)
        self.state = self.STATE_OVER
        self._new_record = new_record

    def draw_parallax(self, surf, dt):
        speeds = [4, 10, 22, 34, 8]
        for i, layer in enumerate(self.assets.parallax):
            self.parallax_offset[i] = (self.parallax_offset[i] + speeds[i] * dt) % HEIGHT
            off = int(self.parallax_offset[i])
            surf.blit(layer, (0, off - HEIGHT))
            surf.blit(layer, (0, off))

    def draw_play(self, surf, dt):
        surf.fill(BLACK)
        self.draw_parallax(surf, dt)
        for bo in self.bonuses:
            bo.draw(surf)
        for e in self.enemies:
            e.draw(surf)
        if self.boss:
            self.boss.draw(surf, self.assets)
        for b in self.bullets:
            b.draw(surf, self.assets)
        self.particles.draw(surf)
        self.player.draw(surf, self.assets)
        self.hud.draw(surf, self.assets, self.player, self.score, self.wave, self.combo,
                      self.save.get("highscore", 0))

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 1 / 20)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        self.toggle_fullscreen()
                    elif event.key == pygame.K_F3:
                        self.renderer.scanlines_on = not self.renderer.scanlines_on
                    elif event.key == pygame.K_ESCAPE:
                        if self.state == self.STATE_PLAY:
                            self.state = self.STATE_MENU
                    elif event.key == pygame.K_SPACE:
                        if self.state == self.STATE_MENU:
                            self.reset_run()
                            self.state = self.STATE_PLAY
                        elif self.state == self.STATE_OVER:
                            self.state = self.STATE_MENU

            keys = pygame.key.get_pressed()

            frame = pygame.Surface((WIDTH, HEIGHT))
            if self.state == self.STATE_MENU:
                frame.fill(BLACK)
                self.draw_parallax(frame, dt)
                self.menu.update(dt)
                self.menu.draw(frame, self.save.get("highscore", 0))
            elif self.state == self.STATE_PLAY:
                self.update_play(dt, keys)
                self.draw_play(frame, dt)
            elif self.state == self.STATE_OVER:
                self.draw_parallax(frame, dt)
                self.gameover.draw(frame, self.score, self.save.get("highscore", 0),
                                    getattr(self, "_new_record", False))

            ca = int(clamp(self.renderer.shake_mag * 0.6, 0, 6))
            frame = self.renderer.apply_bloom(frame)
            if ca:
                frame = self.renderer.apply_chromatic_aberration(frame, ca)
            self.renderer.apply_vignette(frame)
            self.renderer.apply_scanlines(frame)
            self.renderer.apply_grain(frame, 4)

            ox, oy = self.renderer.shake_offset()
            self.screen.fill(BLACK)
            self.screen.blit(frame, (ox, oy))
            pygame.display.flip()

        write_save(self.save)
        pygame.quit()
        sys.exit()


def main():
    try:
        generate_icon_ico(os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico"))
    except Exception:
        pass
    Game().run()


if __name__ == "__main__":
    main()
