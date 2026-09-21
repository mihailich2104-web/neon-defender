#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════
# NEON DEFENDER — single-file arcade shooter
# Ship textures are embedded as base64 PNG data (no external files).
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
import io
import base64
import socket
import threading
import queue
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

QUALITY_LEVELS = ["low", "medium", "high"]
LANGUAGES = ["ru", "en"]

SHOP_ITEMS = [
    {"id": "damage", "label_key": "shop_damage", "base_cost": 60, "growth": 1.55, "max": 8},
    {"id": "firerate", "label_key": "shop_firerate", "base_cost": 55, "growth": 1.55, "max": 6},
    {"id": "hp", "label_key": "shop_hp", "base_cost": 90, "growth": 1.65, "max": 5},
    {"id": "speed", "label_key": "shop_speed", "base_cost": 45, "growth": 1.45, "max": 8},
]


def shop_item_cost(item, level):
    return int(round(item["base_cost"] * (item["growth"] ** level)))


NET_PORT = 55677

TEXTS = {
    "ru": {
        "title": "NEON DEFENDER",
        "start_hint": "Пробел — начать игру",
        "settings_hint": "S — настройки",
        "best_score": "Рекорд: {0}",
        "controls_hint": "WASD/стрелки движение  •  ПРОБЕЛ стрельба  •  F11 полный экран  •  F3 линии сканирования",
        "score": "СЧЁТ {0}",
        "best": "РЕКОРД {0}",
        "wave": "ВОЛНА {0}",
        "combo": "x{0} КОМБО",
        "game_over": "ИГРА ОКОНЧЕНА",
        "your_score": "Счёт: {0}",
        "new_record": "НОВЫЙ РЕКОРД!",
        "best_label": "Рекорд: {0}",
        "return_hint": "Пробел — вернуться в меню",
        "settings_title": "НАСТРОЙКИ",
        "language_label": "Язык",
        "graphics_label": "Графика",
        "back_label": "Назад",
        "quality_names": {"low": "Низкая", "medium": "Средняя", "high": "Высокая"},
        "lang_names": {"ru": "Русский", "en": "English"},
        "settings_hint2": "←/→ изменить  •  ↑/↓ выбрать  •  ESC назад",
        "menu_play": "ИГРАТЬ",
        "menu_shop": "МАГАЗИН",
        "menu_multiplayer": "МУЛЬТИПЛЕЕР",
        "menu_settings": "НАСТРОЙКИ",
        "menu_quit": "ВЫХОД",
        "coins_label": "Монеты: {0}",
        "shop_title": "МАГАЗИН УЛУЧШЕНИЙ",
        "shop_damage": "Урон",
        "shop_firerate": "Скорострельность",
        "shop_hp": "Живучесть",
        "shop_speed": "Скорость",
        "shop_level": "Уровень {0}/{1}",
        "shop_buy": "Купить за {0}",
        "shop_maxed": "МАКСИМУМ",
        "shop_back": "Назад (ESC)",
        "mp_title": "МУЛЬТИПЛЕЕР",
        "mp_host": "СОЗДАТЬ СЕРВЕР",
        "mp_join": "ПОДКЛЮЧИТЬСЯ ПО КОДУ",
        "mp_back": "Назад (ESC)",
        "mp_your_code": "Код вашего сервера (для друга в той же сети):",
        "mp_waiting": "Ожидание подключения игрока...",
        "mp_connected": "Игрок подключился! Пробел — начать игру",
        "mp_enter_code": "Введите код (IP сервера) и нажмите Enter:",
        "mp_connecting": "Подключение...",
        "mp_failed": "Не удалось подключиться. Проверьте код и сеть. ESC — назад",
        "mp_lan_note": "Работает в одной Wi-Fi/локальной сети. Для игры через интернет хосту нужно",
        "mp_lan_note2": "настроить проброс порта {0} на роутере.",
        "mp_disconnected": "Соединение потеряно. ESC — назад",
    },
    "en": {
        "title": "NEON DEFENDER",
        "start_hint": "Press SPACE to start",
        "settings_hint": "S — settings",
        "best_score": "Best: {0}",
        "controls_hint": "WASD/Arrows move  •  SPACE shoot  •  F11 fullscreen  •  F3 scanlines",
        "score": "SCORE {0}",
        "best": "BEST {0}",
        "wave": "WAVE {0}",
        "combo": "x{0} COMBO",
        "game_over": "GAME OVER",
        "your_score": "Score: {0}",
        "new_record": "NEW RECORD!",
        "best_label": "Best: {0}",
        "return_hint": "Press SPACE to return to menu",
        "settings_title": "SETTINGS",
        "language_label": "Language",
        "graphics_label": "Graphics",
        "back_label": "Back",
        "quality_names": {"low": "Low", "medium": "Medium", "high": "High"},
        "lang_names": {"ru": "Русский", "en": "English"},
        "settings_hint2": "LEFT/RIGHT change  •  UP/DOWN select  •  ESC back",
        "menu_play": "PLAY",
        "menu_shop": "SHOP",
        "menu_multiplayer": "MULTIPLAYER",
        "menu_settings": "SETTINGS",
        "menu_quit": "QUIT",
        "coins_label": "Coins: {0}",
        "shop_title": "UPGRADE SHOP",
        "shop_damage": "Damage",
        "shop_firerate": "Fire Rate",
        "shop_hp": "Max HP",
        "shop_speed": "Speed",
        "shop_level": "Level {0}/{1}",
        "shop_buy": "Buy for {0}",
        "shop_maxed": "MAXED",
        "shop_back": "Back (ESC)",
        "mp_title": "MULTIPLAYER",
        "mp_host": "HOST SERVER",
        "mp_join": "JOIN BY CODE",
        "mp_back": "Back (ESC)",
        "mp_your_code": "Your server code (for a friend on the same network):",
        "mp_waiting": "Waiting for a player to connect...",
        "mp_connected": "Player connected! Press SPACE to start",
        "mp_enter_code": "Type the code (server IP) and press Enter:",
        "mp_connecting": "Connecting...",
        "mp_failed": "Could not connect. Check the code and network. ESC — back",
        "mp_lan_note": "Works on the same Wi-Fi/local network. For internet play the host",
        "mp_lan_note2": "must forward port {0} on their router.",
        "mp_disconnected": "Connection lost. ESC — back",
    },
}


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def load_save():
    default = {
        "highscore": 0,
        "lang": "ru",
        "graphics": "high",
        "coins": 0,
        "upgrades": {"damage": 0, "firerate": 0, "hp": 0, "speed": 0},
    }
    try:
        with open(SAVE_PATH, "r") as f:
            data = json.load(f)
        default.update(data)
    except Exception:
        pass
    if default.get("lang") not in LANGUAGES:
        default["lang"] = "ru"
    if not isinstance(default.get("upgrades"), dict):
        default["upgrades"] = {"damage": 0, "firerate": 0, "hp": 0, "speed": 0}
    for k in ("damage", "firerate", "hp", "speed"):
        default["upgrades"].setdefault(k, 0)
    if not isinstance(default.get("coins"), int):
        default["coins"] = 0
    # Always launch on low graphics, as requested — the player can still
    # bump it up in Settings for the current session, but every fresh
    # launch starts light on effects for maximum compatibility/perf.
    default["graphics"] = "low"
    return default


def write_save(data):
    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
        with open(SAVE_PATH, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


# ═══════════════════ EMBEDDED SHIP TEXTURES (base64 PNG) ═══════════════════
# Real pixel-art ship textures, embedded directly so the whole game stays
# a single .py file with no external assets.

PLAYER_SHIP_B64 = "iVBORw0KGgoAAAANSUhEUgAAAFoAAABcCAYAAADu8aIfAAAyAklEQVR42u19aZRdVZn2s/c+w53HmpNKZa7MM0kgQMKMyChWRLEVcaAdWlHQVj8lFLTSijbdNgIiKG2LSkoBW5SZDEBIQuahMg81pOaqO99zzzl77/f7UYkf2vqt1nZAzbtWraq7qtY9+zz1nme/w/PuK/CXY4wAhrlzE8vqYulX+kcKf0FrB/9LWSgtXy4YQFfWRz/6tnTyFQJCRGAAGE7bH8ZWAZwA9oF4aN7PpzYOt8+fSl9rrHr0pJfz0x79B7IVy8EZQEuDgQ80hYIpEQhSIxcrPrRwocEA/Zfg1X8JQLMV66AAGGUlzwUDCUaoKIqsa2+vPunxp4H+X9PGcggG4FuN6S/UBeyZPoMG5xQ1efiDqciPlgOB1r8Ar37ze/S60YBDmWKCKTi3fUkBr4KAJsE4m7a2pcU/zdF/gE3wdkCdC5riFMsXD4FocyjEXrBCrIMbKqhV5LO/ePIdALD6TX4vb+rFtQOMAbRw6cIz84l03ZEly/2Jd9/LF3/ru6xy44dVRzQRVM3TLmxpaRF7T1PH72+riTQAzL/pYx+dettdZE2fKyaPrWfjamsxYdZMs+ZDH8fCmz9zXTQarW0F5KpVq/hpoH+fxXFOW7ZsMZXvR7TvM2GYLF8qo39wEBW3ojmINIHX1NQE3vSh05t9gfffd9/zUPpcn5vGyI7NXL62DknGUU6m/arr3y+GhjKskMt0ZLNDyx988MHOVatW8dbWVn3ao39HR6ivqZ7QPGmipYTAeKnwVtfBW6IGZivPrGuo5UFLsKWL5o13HGcMALS3t7PT1PG7oswYBQOBEkCIxWNoSCUQcn3ITBkB00YykaBkLArLMr1/+IcPdAPAjBkz6DTQv+O6iCjdNzDQxBmD9H0mNaFS8cGkRMBgUNJnnueS1mR88tYvrjzt0b9r/LxqFQBg0szFNw1nS/GRTFbbpmABywQTDJ4m+L6GYRgoux5y+SIfU994LYDQSY9+04Et3oyMsX79elq+fLnRcvXVP0gk4tFUKkGpujrGD+6H2LENCFjwYgkkr7wKpDUy2RymTZncWNcwru3rX7+7r6WlRbS3t9Npj/7/Z4OMiMB9v2n29InRuqoE1dekWSwaATiHYAwmY9AgBGwLC+bMZHXVKaqrTtOiec1JArGWlpbT1PE/4A0OANo0zzcsO1oqO0oqzYQhoMGgtYbUBEkEIoLve3Aclxjn7JEftN3IwE5vhv/DuF4DCF571RXvVL6EaRrctm2Ew2FYtgkFQCoNrUeB1lrDtCwupcRlF190wc033zyxpaVFv9myROPNtBgiAmNMr1p1jz1lyuSlnusiGg6xeCIBaQiAMXhKw2IExhiUlCClUFuTYoODI/q8c89p6OsfaGCMHV29ejU/7dG/xW6//XYGAJMbo7XS9zQBFI5GWD6bRbFQgmGa8AF4xEAgEOOouB6qUikIzlk+l6fNW7bMezNGHW8qoFecXM+xnu63O64X3rt3nyc4V0oTDENAKQViBMYIlinAhYBTLiESjaiRXN7LFgqso7P7wwCopaVFn6aO32L3tbfTqlWrjD3tR43Xdx5BJjPkNzdPqpy9ZFE8B0FD+QLzGYehCaVSBVWeh6ZxjRgYHGI/f2ENGx7KkFtxMG/evGrG2OBJz6bTHv2rSQpva2tT3d3dUxqbxn3SMAwsWTAnIEzTHs4W8MBDP6Ctu9vVTm6o1xRTPcMZ9cPHfqoPH++C7/vu7KkTutPpFBYsXDT1uuvevQAA3kw8bbzJqIw1NTVxx6N4uVjMclbj+64b2bZ9j3r72y4XZHtw924GBQTk2Do0vvcd2Lllh2ZM21LribnM0HAoHE0WvZokEbFTnH/ao99gJ2sU1N5+yCoUK1QqO5wxmLv3HdTz5s0S0ybW/luDKK4Y7Bq5qHSo+2Lese3CI/t33b5kyUIeCAZlyLa7NDMsp1xha55/djFjjNrbZ9JpoH81rGNtbW364x//x3GReOLuUrnCrnrL+SiXK9bkSZO5YN6LSxfdlP1Urnll7ZHu9w1sOn7dNz/82A1XfuCB2p/+/LkXG+rrVK5QNN92xWXCNA19xqIF1999993ntrW16JaWFnEa6JO2cuVKTkSoVMozUsmqC5Rf0Wcunh8zTDMYCweCP/7RYz/iY8desXDZeR/pdmrfFYw03NhywYp3J89669Vbtz59Q3dXp1WquIl5s2eYwWAQYxvH1SQSiWmrVt3OZsyYwU4DfdJmzJhBjDHKZJwDtmWoMfXVPJPN0NiGWtVx7MjRr31v7bKzr7u28WiJq7/7pzb57dUv+GywQ8296BL9Yu+cpetf2XR8evO08oHDR8rjxtZzp1TG/v1H3lSdFvFmoI3BwUF+xhlzJp6z7Ix7goHgtBlTJ6JSLun6+npj4bSGG//z8KQzxkxrnndo48uqvHev1X30hNi8Y49+69IJiZd39l4yoTb2rrecM/uDR493h2ZMGY9SIacnTWo6c0xDw+6v3H33YQBs3bp19Dft0WvXrhUrV65U48dPWLLi3HOu7DlxQlWnk0wTlGGa8tUte5qnjmOL1rc9YRw6noFoPgPmhJlA9VTc/8BPadk5C9yFM2u5HQiSEAKTJ0+URccZWDR/XtW8eXPexRjTt99++982dRARX7t2rX7qqSfOmjFl6g0nOjv8ZDLJuTCgAdc0TScYDosNbT8XfUc6UZLkDw3lkMkXUeK2kctV2HOrf2F19A7btmVKpaRnCGEYpl3T3dWlpjdPPev555+5XHCuiYj/zQK9du1a3traqpOR+JljxzRe5CuCUpprTcjmCkwIzrkwfEbKF8yF9jzNQeDgCJsG2dyHznRTIVsk0zJJ+j4JIRTnLONKxSZPmjQpZBh/p4n+7Pf6ptgMjWDYf23d+vy6n/zkYLqmGsIQ2HPgmG0IZvueb5B2bVIOSElNGtBSUT6fgxI2QJo5mQw3LVN39o7Ivv4BnkwlYxue/kXnM48/PuzqURHO2rVrT0cdqVRKDw8N2gfa2y3TFHjsiWdhGkIEgyGDuKHglzWYALmVBFQFDJoRM0EEQPleOGJWpC/tdFU6/NRzr7DhkbzVPTjoHu7o4kHLelMkLW+KFPzIoUOBxilT7eVvb6k7dqyLpk5uYtmRYRARpCcFAAFZArkFgpQMBChXgbQPaE+GwwkJgKXjEQRqkjh85DjmnbksVV9XHztw4FD0bz6OXrt2rV61ahUfzmTWlxz3KTMQjpaLeWabQldVV5FlWUgnIxlonWWkR3sv0gN5JbjlPIhZgBEM9Q8NhEBa27aF6lSCBQIG7EC4OhwOb84UCt9dtWoVX7t2rf6bBfpkQsGvv/76zTe8/6Yv//SpX7w2fdqkjvYDR7mUkrSSUJoDwhitdsoKIB2AFJiwAe0DJIkpTQAQtC3s2LMfM5qn5Ne/uuHAAw9956FPfvKTj/f29oo/d/LyZwV69erV4o477pB33XXHws9++lNf6usf7ErGE+1aKxica4BBQ4+CTASAQFoBBGglQZ4DQAOGAdu2kExEMJTJIRwKdJ040X1o7pzZNz/54x9d+OCDD/qrV68Wf6tAs5aWFiIiozpV9X+WLV183tIzFgRL5VK0VC6T73saAHylAK1GAQWBaQUmXUB6AMlfprdKKRQKZRhCoFAshBoaGmrOWLhgtinMf5w3b171xIkTOf6MLa4/G9Br1qwRjDH9lbvuuGHBvHnXbN/drpRWkL4ntQbjwhC/hIX0KNDSAblFwK8AygMpH9CymIiEim7FEwqAZVnwPamT8Xh3Z+cJbQVDF37sIx/+wqJFi/xvfetbxt8U0GvWrDHOO+88+ZPVP3rPlZdfdc/g4KAvOBeayDRNy4pFw9K2zIpWBIM4gWjUq7UCoADlwS/lR2lEq/BIvhg2TFMJBmilIJWCU3HrLctigwND7pJFC1Y+/4ufvvemm276s1HInwXoFStW0KpVq6ympqbltmlFyuWKHw6HXKUoWi6VIwzK9Vy3wk55NOMAneRnrUFagfQoZ0MYTiwWcXwpOWkNxhg0UZBzJE3LZK7r2p7r12Vypa81NzePb2lp+bNo8/7kjxIRCcYYnvrZz74Zj0RueOGlNZ33fvP+A4l0+gCkXn3JBed8fsvOPY2O64ELAW6aJ6kDgJKA74BxAQYP0B7ADTcSTVW0VJxxTpqIcSbQ3d15kzDPzstyTvf2D7xvyuTJN//7v/3bdxlj5xERY4z99QJ98rHVj7c9dndDdfq9PT09L7Y98Yv9Ipx+53DOvehEd2cwEAyUfV8miTAofR8A58wwAC0l3CyBiBFjIM4IvsMggoFcYTiutVJSaVMpBdPgQ/uPdC34xgPfbwlFIsTJ23nbrR/9Ziwau2HN8889xBg+iD9xh/xPSh3V1dUMAKZPmRxvqK8zhSH2bd25e65l2xsZ6Vs835/kVdyYbZonMtkCLDuAzs5jPvkV2wwnDTOaMs1IxDBjVYZIjDGNSMrg5d5ANlPstgIB7pQdFPIFmKZpeU75Yq9c3JXPDB3ds2fPe/bu3z8YDYfCwYB9Lv0ZkvI/5cbAH3nkEc4YU5pbrWWP6vfu3bdn5+69OhQOjQMTYdd1zQtXLAsODGWq0qlEJBAIGlMmT6jbuXvvs517dj2ry9467QVe0sXcWl0urVN9PS9QueOlB/71tqsHBkcWGIJDE1EkZA+/sGb9gGkHgsIwQlAq3djYuKd/OHf261t34uKLL/weEZUA8D9VQ4D/CbmZGGP+977z4BfyRXfaa5u3gYgY48wixlMEneKccddz/XGNY+vmzJ4R2tu+D5YVXPL9b7dOJmdbz8DBH/Q88/336X3rW/v6Nn3piNf/2NBTT9632LatG3fu2svqa6tp6uSJPBgKDwluHlFSLQRwgWUH8sqX3tHj3az98PH0gw88cA9jo6pTImJ/FRx9StXJGKMvfenOz8yaOau1qz+vqhOJ8rKl88Sd//x137YCO6XyX6g45beapm1Gw4wClkkVX/Jde/bqeXNnXb1tb8fVhYEB+CNlHB45BAJD7ZRmjJ84DR3HjytiEAYHhgZHEE+EA76sjEGZdMUpjuRy+fKyM+ebph3BU8+u0dOap163ccOGF5aeddbDra2t7E8xyfXHBvqXN/Cxj33klmuvvPIrQ4MD1NXVo1OJuDGcGWHJdHU+nkq/N5fNXBWJxH5cLhQDuZLD6stlyuVyOGP+bL5n7wG1ef9RCm3fqFOvvFBWlm2Vq2qtwlXvpFg4xM87e7HwfR9KE4RpoOI4tmUHp0QTVWFhGIxxY3JvT1+iqm4sSmWH9u8/qJYuXvjQpk0bnMWLz/zhqIL1Dwf2qdNa9Bs23D8a0CfDJ33FFVdEp0yZknrfu9/56Vw2K7UmHgoHTdd1OSPozPBACtJlTqU8XCyWc8ywkgNDJ9AsFeLxBCqVCpYumCPmn7kYx1FW6NaNiVA8jBOpOCZcexmEUhjKZIlxTul0NSyjC6FQqDIyMny0VCq124HAWU7ZyadTqTznHIZhsFAoxAaHhnXjmPpHn3ryya5Vq1btbm1tzRIRZ4z9r8Gm/xfO0B+ToxkRmUTEpkyZseyBe//1wIzmqbt27tkXhtYGZ4yXHUdJKRGwbSLSjhDiF1Yg+GQ4FGqSWgoiwqFjXVQslREKR7Cz/SDaDx5B0DbF0z7hh8pAlBGOd53Apm27EU8ktFN2tFIS2UIRZceRQgjGOU+ahrlDa4oEQyFPKYWBoSHNAJic8yNHj/u797b/4ob3/t2hK6644p2MMb169Wrr9wb4JE1uXTH/gq3nn7E5mUzGT6LN+B8BZDDG/O9+97v/8Mh37n+hXCrX+1KFlfStUCotn3t5U09jTZLOmDcL/cNZ2JYdq6qpW5BIVr0tGktEGGPUP5ShaDhIAcuE53kYN6YOkYAJz6lgIddY4FXgMoH62hpMmzIB5XJJWJZllB2Htu/YpXO5XDIajiyoqqo9J5GqXmFZgUqxlM801FbhsvOXues2bB5hoZBvmaYJxiNOoVD1pdbbHjxysP2TK1eu9Ijo93vS21sZAMzkCIUd54x4MXcJAKwAxB8M6JaWFnES5OqXX177vYmNY26PhUOBzMiI9jxfBGrqrOJj3+N7nnk6HkmlraBlKul5K951XUtftlD6jFNxbs4VCp/KZrOxcrkom6dO9AzTBBFRLBJGTXU1AKAOwFROIE0I2BY11NeBc6OstC7ZlsEZaSilPcGNGx1PfrRvcPCWhQsW/CAUiL89aFmYNGkijh88ZA8/eL/BDUHEOGWGh5RTLEacUvnz+9v33MkYkyfB/p0ikra20e8P79yPx9oPlZiv1wHAOkD/QTh69erV4h0rVyrGGH/u6Z/fO3XipJae7i709/VTKh7nJH3kn1gNf+dGLhwrTFwoz/eZbdsTLli+DMuWLDzRMzBkdR3vQGd3j3PJBeeySDjMimUH0pcMALhhgBhHCYBkDJ7W0FpDKQ3TMBzLMJVt2eGrr3wL275jx+CcObPq5syZeUZVPEKpqqoLCZiZzWXhKe1ETANiw5pIXoCotokFgiGRyWS0FQhWBULiC9956Nv1jLEPMMZOhX//o1i7ZdTTkLn6HbXVyaRR+t6jwMDAH4ajiYivXLlSNY4bN3Hf3j2PTp08qWXXzh2ykMtRIBoFAgEKmBz+z56Em8uDW7aCkr5SipfKZW2Y5gTTCnxhcGjkM739vZ+YN2dmw4qzzzQK+WJwaCgzmlUZBogADkKZMQxqwDYEOOdMawWnUolwwWNSacyeMU3NnjVz3LjxY6cLw764fsy4T6QSyZlEWglhAERBMB6Uwob3+E8QJR8iGkUoHOGFbFaPDPSrc5Yufs/mjRu+RkQJzjn9DkJJAgA1bsKsmVdebVcqlbkAsHz5cs7/lyCbjDF91dve9v4nfvLj14KWcV3H8eMqaJqGlUqx3L69dPzWjxNb/UPEkwm4xQJksaADgYAyTAOmZXHSWmcyGXmip2f3mMYme8mihRNv+/I9OQJK8XgcIE2CMwQsExWpYSiFJCcoIpiGAdMw4HseM02T2balb/n8HU5dXd2Uc5edddELL70wMjIyTESkGOeccQHOBfluhalcDoHqatDa53HkIzei48nHEait5a7r8v6+PqO+tuaWV19Zv0FrHW9ra1O/C2/bghW8QgFacwcAampqfj/1DhHxLVu2mIwx/4knnjjri//4mS+Hbaum89hxaZumCFbXYGDNGgzddSen9r3cPNEFb2QE1rtvlOFFSzNeyTEqrkeFfEGDSGdyOTSMaTh8/cqrJx06dJiSsWiAg0zGgHAkyo4e79bbd+7V+XJReQZTeU1quOyobTv2qEPHu7QwTN/3XI+R5pdduMIeHBjQc2fPOHvBvNmRQwcPnxgdeyGtlITvVnSguiYTvPkWt0DE7OOdUIcOofTzJ9H5wL2wg0FmhkI40dGhalLJ6Tu3bnr+ohUrlp3kbf4/GatjQpCwLBiGSAHAwMAAM34fPmaMKQD6+eefvb86nTorZFo1HZ2dKhqNGhSwcbjtMajvPQzb4IRwhLFioULXtKjwpZdboZ8+51VcxzYMQ0UjUWHaJi+WK7CE0HXplFkpO2zZ0oV2MBRAwBQYGRmmyROaeKQhiKEtr4IZBmBYSCTjiDdPhSCNYx1dQcE5iAj1Y8aY8VhEJ8JBPXn8uL07du+/zA4GuSF92JapUIAlAiHXXrTEN6US4e9/pyRy+XhQ+lT+8Q/Zwc4O1Nx4E0uOHSP6urv1mMaxZ9zWevt/fKpY+A/G2J0AsLqlRaxsa1O/JVchKaUBAEII9ntlhqc6Izs2b55lWOaHU8n43/f19qG7f0DHkklRLjvo+4/vwPmvJxCKR6GlRBkauOxKmnbj+wmuL4qZHNkTGimTzYlDR450jW9q3OBUHAQM4UlNzDZNqq+tZgBDIh6lVCrJhBB73Eox6yl/xJb+SNQkY5hRtFjM1gQMMxSwrVlSE1V8xZVWMA0Oz/d5JpuL+1q+2D88GM0OD9cnEolZgWCo4HuuZ0lpjH3LW3mn9HX5v36iVGcXt5LVkNu24EhnJ9X/w826Yf4i0d3doxKJxKQJ48bcsW3ThtqBTP9XLr30mq6TdXU62cx8I9DwfZ9834dmqPptQDP8WkbzxsILY0w++uijZw5lRn60cP68cVte3+ybQohwIsmdfBYnvnEPvNdeQbC6GrpYRJkLlrzlH1G75Myg4VbgE8loPGbncjn23IH9B+67/75LARwHgNu/8PlWzgU3TEMKkNHTO0DpVAKCYejuf/vmmtU//unycDLBZLDBhgsyjgwn3ZXvMxOx0Ff/5atf/nIkHGrqPtFD48bUMcs0NIHzc5adufnOL33p4FM//fmNxWLh1Xe+87q+qVMnryDSYzQXwh8c5E2XXpYsLjmTOr56F/P37IAViSJdGGHDX/8yD9/8GcQWLhH5fE4P9PepBWcs+mhH94lZn/jER25mjO04lQH/MjI5Gd8xYi7AtGkYxm/LDOk3hTKMMVq7dq342te+Nn/KhKbV48Y0jNu6ZYsfDATNYDLN+48c1odv/QSJHZthV1fBLxYxnKpC8nOr0LBoMfzhYXDDgONUjPrqdHrbrnZ6dcPrjzHGjt99993hlpbVIhFP5rVWYEoxQ5jYun23P25sPTZu2vjlzdvaL156zopJUyZNmz1tbNMlMxonXDxxzLj502fPm2OHYvf9x6M/uPWcpYv8/fsPs3KhCEMIKN9HTTqdYSI4t2FM44WN48ZdtGnTxm+vfXmjSCaSYccpmzBM+Pk8QsEwa77zLhiXXQHfNqCEhZDSrP/Lt+HoQ/dBxBI8lkya27du9+bPnrV8xTkr7t/88ssTzz777Kk0WtwmADgZRmMom01ksnmuper+bx69CuD/nkpFUpNTsIpWpaWlRd555536i1/8orXp8OHA2rVrp133tqs3ZrNZ1tXVTbYdMIxoBMfWvYTCfd9gQV8yHY6CssPkzFusm2/5LA+aFnPzeXDLgi8lDMOAZVm0bMkiNn1Kk71z5+u8qqpKtbWtVPPn/5NFJ+e7Pc/FyMgI05rINC27UnEnueXKzX554LuFAkKGYep8Po9YKjAvFIk/2dw8I+NLRUPZLMitgDOACQ5f+wa4UQHniriRmDJl4sSlS86E1sRs2wYXHIwbkL4HJhnGf/hmZJeejf47/w8sLgA7gvKTj6MnM4Saj9yCYDRmHTt6TI+pqz3DDgb2uZ7fW1U15qLJkxu7Gxsb1d69e/XkyZPt1za9Th1dfbu5weYuX778mXXr1pFBROwKxoJPLVz4yEsP3L9i287d7Pixoze3trY+CgDV6fS/3Pfud63s6+3jvlIUCNg6GAwKVyns//5/wF/9IyTDNpNBC+WhEYjLr9LT3/9BLrRmvu+DOAe0gvQBrRU8z0c8EkLQMAiArq2tJQAIBezKaNmLgwsBYtwzLcvU2ocvPen5ZbZ169YygPIp51jUeG6mUpEsn88YYAADA4uEobmA8nz4FZdISqakL7TWCJgWsy2LlRyHtCZUKi5sU5wc4NcwS3nEpzbDa/2K7rn3HkS6Oni0Kg352ivY330CYz5+K9JN4zmUJC0l//Z9/55MptKv3nzLre1tbW13AXj2ox/9+PVzZ8++dnzTGDhO5e8XxAL3rgNyBuOcAJTPj0aPOxWnOp1K4vkXO95/zz33vGXB3Fmz8rn89EJmxBrs78Nddz86KADHjMUGlo30jlTv2HKxHY1qp1TmXiSCmi/egeiCMwSTHiQRAsHASdInGELA8OXomRumAcMard309/czACiVymEwDs45SSlRqbguZ5x8X1uCC865wQDwhQsXiq0TJ2q0tRFXzOacw7bt0eMlQDj+xJPAOeegbsb0k2QoSWsN35dF0zIzo8mbIMsUzLYtGELAdX1oAjRpkJKobp7GI613wTmwFwP3/gssIwizu4uG7rqdvTpl5s4dPpF2vfA7Wt42ZfnZy/D+97xr1v+59ZP/9OK6l29qP3h40tQpE5v6+/tKvlPKf6VCJgAYq+dMHtPguJ9+tDa9/uVN22VjXQ3nQsw5dKRj0ZwZM6PpeBx5xyUrmeravuvA9ngscVXP0J7KnErPxgnVNRdnMsOE8RMRv/HvkZgzF7pUhGFZkEpj38FjKDsOcvkCEvEYCsUSpOvCMpOQJ/fqUx4djUZGfM/VquIw5TowAxa3A5aueF5MSt+U0vMYY7q6utrE0SSISJ5zwVvKhaERsm1bAmAkDJjFPLj0oIhI+T4BYCdPQRCgUaosuy7WvrYNAdsCGENVIkY1VSlWlYqDBIdTKMAMh2AvPRtlT6L43W/BkmAsm8fGNeubdsXrEqbnZy64tPxCzvMvqKmuTQMs3d07sEApzZXSevOuQ9nyYP+xJ7j7sDOh5kM8lx2OWaQ/dmmmv3bD9l2qXCxx0xADnT0D2eOdJ3RRKpU/fIg5zzxVGNc45nVuGDoUDvFwIhLh5RzUtFkY94U7MGHJYli+B3COvQePYs/+wzBME3YggFAkArfiku/5iMUi4Hz0gJM3WqXix0LhCGdCgHMOf3iIXKcCpbXJGUepWE4QUc0zzzzjYuuDPmOMDre3T/Fc3+7u7h1jWpZrZYdU7VlnIVhfD4NzVvG8AECSCwHLDti+VkFhCATM0fjW83xoTYjE4kwScOBIJw4cPo5gKACTc3DPxaS3Xo5EyztRsIMUIJ9S6apoIBzdEIknjuXXPOd1P/ljlhkalke6B3T/YDZjmVZfsVTmx/uHQjUjfVsTrntlloyEYVdUhdsMtYMDNxwoBx668rxlLYzxUCIW4cMlhxfa2vS4l56GdvKsUDvD8iqS+64r/IaxxeL4CYhf+y5kFNC7cy/AOTypcOBYN0xG/pwpBhgnBMOmaJowhZfLFexsPwTX9SEYY6tWreLFYpGvXr1adHV1Henr7+8IRqJj/UCApOuanEGkk8n9nu91xM3oZePHN89KJFL/5XgOfN8d73vy01J61tGjR8bYwaBnem7AGtdECIUx2D/QVVWdPhBPVi2PxhK65DiK5GjFJJWI0YI5M5ht2+jp6pTklTJ9fZloZ/+wYVi2YJwxLgxwxiCPdcJevBzRdA2N3Pt1Dqd0tFDRphFN1Q+/vqGGXl+PrUuWcyw6h2vSMQYUNcPQSGbk2bcGjGugpN+vlW80RixR0dpXFW/xBYfW/rS+9mMVOxTkvOJi1syp0L1HIPNZsFgsUOzsivuR+IFMd8c661NfJa+2ARs3biWTC5iWhWKpBIMzOu/cJSwQDBS/8773IEIUO5ErZN73rYe8VE1NfSwcRCaXx/HObv/h735bA3BOVRlbv/jF42csWrA5HAqpxrnzw64kFgmHZgZs61ipWDrPDEcO5n1vPmnGhB32LXjD+XymcvV738F9pxLRDeONgitlvrffaN+/77O3fOazobr6pk9ksxl4nhcuFoue45T9uppq03V9kGnln/nqPx/j3Z0TS1KJqde/t/est68c+7OfPQ/TMsA5h1IaAkdQM66J+2euwMjL6/u0JycWqHiizETA4WLs9MmTEJ07Dcc7jnNf+lZDVWrvp5977HvJxobrpSedak3ccGGDM0Kf79OKdOxL1W4FrtaH4LlhIQRgCFZmoOFQYuJ5VaH3OInUplk3rkw6ZWf5cE8PLjxnsQgFg2CMwTAEtJSwDAMjUnqLQoHi5aaZPATtslBgxDBEvTCFu+7VV/JdJ3pqv/7Pd8zmnItyydcbtuzSqx//r8j23e29l116cf1Zc6dT+74D+qylSz76kQ9kH/vO9/7zhzPDeOK8A3u2DBiWFaxPsRcbxi8NTm5YftF5y//JNATVJmMYGBjC2g0bi69v2x6ZMKFZxuORx03T5LZt7dOMWWvWvzzy3ne9I8uIml3G5LkhOze9KhXdXSjhcKmAZDyG66+9DIoUtNQwbQtO2cHu9oPUdM3bwecvbJ7w2obX006pkOyla8t9vQj6kikmIBj6ZTBYMrs7F/N08tljUlMajLmjcbQLAxZsAhupKFXxJReMcTMUhu86yAwOIjd5Opt2512YUiwmh4ZHLh0/YQIqrgvf92GZFhvNHgHfl6PH9SgN363wilTW910fac+3x5TLkXAiiW1btnw9Eo7d8JlPXPvBWdMnf5DAsG3nXiSretDV07N3+vSplyqlXh/JF615s6chYBlq+VlLr7nkisudfY88vHLk2CHeEAgwEU7hzjtbpXRdwRnI81xWVZXSpbLDzjpj/rUvrV1/0/xFZ5x/wTlL9OWXns8Z5+c/9+Ir0RfWvZbbtnPXqrGXXPAAZ9zyiESb46JeaTIYh+u68MplVHyJYDAAv+yAMYZZM5uZkhJ1CxfULJk3562CCAUp0f3lO4BSCQHHBQMsz62kwRm0UmQQY5IRbADcBmAwDkEMjq+44zjM97y6jq4e7Hz42yhJhUmfvw02GKxgiCAMJaWvSBMF7MAvBeKMnwzktAZngPJlMK90ohywIATzfCmdUqmEUCyRScTitT0DGRw63oPhkSyOdpwggKGutjY4ODjIbcuypJQYHM4w2w6IZCplgSjOCSLBiVUZDBYDiLQRj0ZZuqaWHTraCc91YVuWqK1OZhvHjFWhUDhRKJZT27bvTfzs6TWxslPR9XW1iYHhzMVK6WIxl7eKWqVTgiPnSVbR+qSYcvSoNzq5YTPGIDiHIQSIiAZHcooFgioaDKHpc7eBxjSi54Vn0XfgoM05R6ZQwrBPsAVDXHCnnlOJuwAkG9UgcwaYlgnf9+2JY2ow9+q3YfJV18CybFQcB6QVy+TygoEJIThTSoJxNppgaA3X80cjCiJIrbnBGL9EathAuOL7Uekr+L5vBkNBP2AaEIwQDAYwtr4GhmEoJgyrs7OzkzFcyAUv5vMFZHNZ8n0Jw7QQCtggRaQkwWKAHQjClz4K+Swyubw2LYvtad97x0svv3Y4nkiEpJQqEAjKZDKGxroqVKUS0KRJuq7vuR43DZMUcXuqZkgLDuNUhYidcpjR5AkYlQNrInDOWaFYFKViUWTzRYAxjF28FOMvuhip8U0agMdGtYGwOYPU5CsdcLkNgGkNBgL+X1Wv14pEEa1vgBGOgOnR4ykBoFAo6eOdPfrVzTv0S6+8rrtO9GoOIkYa0XAIRACBweDC6atUnN2lAja5nmdYtpJSKddxBAGRMQ21GNtQB8s0VCIaoXFjGsSY2pr0c889l7/3/vvXK+lLUgqOUwEXfJT/NYERMcFGHyTTNBCPxQAwcCJAa2ba9i/uueeekXgsVt3UNE5EI2EjHo3oCRPHq1Akwk9+SI4llVSclD/ouYOHnQJ2+R5ywiQBQBPBMDg8twLpe8hksnTo+An906df0oeOHFXSl+RWXIQCFjjjYIIjkEggGIs5yveZ4BwGRs/mUyBtioI2bNgACB4RtCJIqSCVFCCCVgoMpPVo0xUERsFAwBg3thYNDdUIBALoHxzGQ48+Ds+tyIaGOlx16fnMdV0RNs34mZ+/DZbgahmQDNnB+O59B4UPdmTH5o2f3Ne+a4Vl2QHHcafYQjyVqK3edux499VNTU1GorEx/Nz612nB7GkoFEtIJ+JghgHBOTgIAgTBGIQQ0Fqj4lQoEg3z9Zu2qmNHu/3ly5cbO7ZtfZpD39t95EDDjx577BpNlAgEzGemTZu1eig3RC9u2Py+889eKuff/OmZbqmoY5qYMqw6v+KwQqmM9S9t08VCiTzfwzuuuUzMnl7Lxo2pQTBgo6u7B8IQalS7oqGkZiDGtJTCMIwyA0UEEbQGiDEkABguXIAsRYyBc4ZIJIKAHVAEBtMylWUaQikN33PBOUdDbdXHbJPviNkhEY+F1Guvb64775zFqwN2wHh9y1Y1MDgswuGQtEyDNc+dyyzb5tL30ds/KKR0P/3cs89dVS4644VtpyOxZDIQCKaU9N7d8/r2JiHYwexIX8XzPN4Rr+mfPqkpVsjlhFdTRWHDYARAgUGxU2VGQsXzcODQESgl9cZNr4sd27a5vl+SqVS99/gTT1xQXT82nUxXL3Errj8yNHDppk3b53HBWTAY+ftLzjv7gbFTmw0mOJQvae/+A0wYprIMMQTpGm+9eHlaEYExep8meWhsXbUou64qFnPV0Uj4CduyIKUEGGAIQ3HG0pFIZIAbJvJqlIojjCsgAaOsiQcEhTljME0Tzz/3HHr6BhuEptKxjhMinxvZYZrmV6WUxElSw/jQz846/93lN2Z1P/zPR97CtJeyGBk7du268ZorrzivXC7h9a3bwbT6ked5WVfrwurVj1dVKv6loUgkXVM/tidZXVertUIuM5yKxmJXkZJusH78UG/v8a+nXP9rAP3rcLYQyRWKiNQxKCKtOefEBBRGi0hSKgwNZxCNhDS093XfL/XWNTR9GMQ+ZdpWuqqqdqiqtg6e55nhcLi5r/t4s1txsHv77l1Hlx/755deeuncQqHYMHVq8/jaujqTSONYR0eXyfEF6TkJ31P48l3feHzr1q2/8jEk37jnnmtHhkdsTymVzxc/l4jH5+WLxWL3wIC1ZqgPU0IWTCIM+TI5RBYzSprliaknpeZv1ULwzmef5WUrdK+qqVm3a8++0ODg4K5HHnlw928QlP/SVq5c+dwb9B0v9A/035vJ5tia9a94T/3syfcA8AGgpnZcl+A8rTX1M2ZASUkEoFIuQytfcsZtMHwCwFcL+ezDwVDgjlyxFCk7Fc1AggNZ6VaSyhTMkT40jUYJShOUInHTTe99+PXXN40wsPdzztOu55d8KUvFYqnKMAwyLNP1fR9aa5sx9rFPfvrTEQDXAdh3ww03rghFwtN27Npt3/XVu2/t6enp+m333NLSohljj596fekVV+yf2Dhp9mAmN6x37Tini+nPNTCmAkpJR8ofH/HJM1Z2DPYBuOah8bVDCkgv5RLNlaEdt373oSfeoAg1Zs6cSXv37mW33367Otkz/G+L2Lt3L2ttbe1ra2t7+691Z1hbWxv/5Gduy/leZQyUTEtSveVKhQEgZlhMEQSIiJvGCAD4Uor+weFyMp6Akr6rXDdUNo2YN2ky0+Eo/FRSKd/nUimUnQoDIHN92dEGBxcZX0mSWppS64BmgOd7zHW9klQqxDhjMAxnzpwzxuzZs/VhxhgeeeQ7Gx75NUHQqWOCWltb1cqVK/9/97wLwC4A+FZT9YQUFyzjwRhRKvuBE8Pv1XSymrUqlYqNKJWfI0x7r/RxUJLX0tIizi4UjJElS/zW1lZ56gKtra3/rZf4a4tgp87GWLlyJd7wT1HjGsZzQZq5vq8rIwOcBYKQSgJKI0hq9KRG5Xkn/14/89IrpfOXLaH5s6cF+7q6MZCqM8Z+4Z9QXZXCzl37eG93D0tX15AdsOmZta+w/NAQASAuXWESmCUEl7mheK6cJ8uymfS8knZLZAqD2b5rZPv7fa21ODXz+JEZM9iK228nxphu+83N1994z6tWreKpTZvMV6JRunITUdDbdXHbJg96HdKQffDI59EggddqiqHzZ28i1IB/SAuX55kdkVg/CskM/3qL/sKUeBk5yZE3ECIalOvZ9IYh+YmBK7lXYN5Xutup1BsaocjqDp2Bmrigu2XZLU/Oag+B4pNEOQzz0PtnHViXX0L6OuSmiUYJShOUInHTTe991TSDjs/hatOOaZDQXrcnihP3uEzaPQQk/cwo/kfAdSKq/sZNP4s9eYghN6bKPcWc WCd8DukiXQWNXHPXPQdTZwZ/tLXfh+lpOmzBlsA2y7Q5WSTI30v8eGMIzPttf5pUaDk0ZfvuULjaj+QmDT9QxgQRDQhVUkJRliuf7GxtddjWdZTUdPg8Apnz0sPecIkPPBBRXiAOP1RDGj9GDjkfKvygl09wk9+SI4ll5lPr9rS91TwAuOeBPjUYJODggBj40nQaREvREM+mt4Z0xWT8gip8kywwYa8CBelPyGPQQu+0xWT8gip8kywyDNxYXqPDaXvIc3sEgBY+cfQ+SB9l�3eO/mNXLtMxQPayg9O6Y0Gava087jDl9kNBZmRFYKVxMAfKvkPS+camrT/NYERMXAQXcGvr9WP2+sPR/snH/M7fHLr6WPZVVYHwQqmM9S9t08VtOUH4GK63Xa5L5sbq75AqYR43VExdLHVcXfWj+QmDT9KuO5mf0oe2Ogw3GgpzzZfEDgjlyxFCk7Fc1AQeLUIn7atfETnH/M7fHLr6WPZVVYHr4TGQcovfX+Mmj0WabLMeJiPOgeiutC4m5UOaxdDkprDtYTjOT8wQDA6QDA54hqYto/AwmzBdMjbUC50yam/r dchBULJ9tU9HHPJ+pWqqP9YYHAcVT/lLYaznCPWkrz9l9kNBFCk7Lnf7gsRfbgy4Wqqc120xC4Cp9vz6JQyyd8ApLhBYnk9VoxQcalViheFB6E6yGUxkXjEgZlh2qVwItSLxGUaxdM6knjExi/YYduN6h./5zER71/I3�lDxyQmS9vpKfP9FjKU2vcjhhKkCEKliGx6ejxnU1KTVNRHphCsZtukxN5GgJ1xnU144/22aXw4m/K7nc0qRD8u/64s9eYg1VBrhW7tfVVkZsxNgFjYuvI78qFWU8ikNTn468HZ0fIWGgGkdk3axnU1KTVNRHphCsZtukxN5GgJ1xAjibAU9Nraj28UNYF8M+3o43n7I3mi+JKsEXRKeIeeCWm9//ouqqbBhCimiv6RnlTe4EdkGB4tYtvcvjO5ZaJ/XY8OAOZtukxNi55cQPgdELgsIH8PXkuXtUi+DTGQtE"sRUZMi0xgi2PeGdRcMVwQDEDqtepQ4kRihv+o4OSnIXK6UaDk0ZfvuULjaj+QmDT9QxgQRDQhVUbbYEvwk3/�32MaZ43KEyznaMEKpXHw2U/HWlqvwf0SSUUN8MijExajqrU6s07WvUM9Q8wZeEsV3hs5qwJ+ywas8wZSz0YMTlQojBnu+ne6Km8Ap2hmfzaKG1i8gZV/4IH6FRkX+O59B4m1kTN7wQJea87CDdT5VAzjAf+9x4jG+xn3,+AkDQldQhnq/WSRPt657oFWiVYaeXlK6hVwIgcHUScziLz9A43Esqn2WhmfzaKG16OC7gqNGKcz8zfwzuuuUzMnl7Lxo2pQbzXxA7HVVPZU2qTrlUGxU2VGQsXzcODQESgl9cZNr4sd27vt/QlN9 W9klp9nu8tW0xRfLxo2pQbzXxA72oO7n/Ql}PgpX9EiR3TBMwsw4SOwokmsaxjBnu+neHNDudDmTTxcyeMDMf6t2+i5Awbz3IxDf4StuHrREuP/5zL1uyOx79cIpVQZqwg4vPOItYxIMEVY4g1Cc3C_lGvEdeHNDudDmTTxcyeLRgOcD5sJPmrKfR2czeVY4g1Cc3C_lGvEdeHNqodgACJiU6E0cohgXyOPBMDg8twLpe8hks UcKhQEgZlhMEQSIiJ2_w37sVAtD+snu8/Zs4IRGAFbl2Unv8GvMC427oGSbFkI9T+avQelfaujrlkWT5wUVTAFb1iqxZ9tguu9CyOPcKwIWDBZBknk1SIipJ3AsR0UNnUo4D/mcLNv1xEM8PN�M5Xxdn5jwAXMlG0OjpTkqhIDL9mKi6DcDiVYQdELg7cSPZvzM8P4Q+0a434RrY4sRcESZv9M57sOpTil2BfItMkydWsECms7We0VDZ/gyRxxzYPBiZ�j9QPSB/QxUBKYfZQPd7wT1HjntHs+z0/5n3kQNe6cO0yHRujRXairP�Y�zuPnWV29S5HP8/p9vz6JQyyd8ApLhBYnk9Vhlv2LW4(XIdDFcGAv+vIAKCsGpYNgmT431V3Pm3hSIi2HnItsnxkDtfIGfI8a0n6prnXH62C68gLkccKboMC427oGSbFkI9T+avQ0N+45I2Si.Bvplf394phVI�aJ/dX3fXvu7pjK1DrsXwcrVPrhljeM/tigR3kYgwMcsYGRxhYohKZIHyJE++vCgpAN2C3f7C5eAXxa61Ze3uFshohHaZ7HA+ mNW9feB3KzfD+HAAMrEKNCslLVfuhDAY3/4la25urJsCztw6XCp5+47V/_cfeB3KzfD+HAAMrEKNCRPt/9E8W5NIEkZFgzQuPaAZ3Pp25WzRqUtYkeVPZjBZvSlvAvHpZ5i+cXoGSgfPaXYp38qAMlkmHdQ/cfK/SaAY3YD/EazxElSw/jQz846/9ejDkCBbfKQ4k8W/YdESU7sg8+SRlkmHdQ/cfK/SaAY3YD/JzZwap+ndB2+cjKc4F+fIlwja+YON_8SQ3FpA7YERQ6dY/0/p5i7/Er3MjgzTxlfO)kVB0xfVL4Xhpsv7Eejw9AswMA3zLN9gzZTf85kKKfzpi0q1D9fGPbWCsGHCc4F+fIlwj9P/DMP/wZgdj9P/DM3+4hqukM94d�/roGqGPQNlGH56f0SSncVn68fo+swRkX+O59B0K8YPdtRLJz85Pj7uNVE0eoXieUEQCPancFxKF4vLEMdCvaj+678nUZHRm7zTIRO5xapBMyZSA5jvBgYIKoGDd2tjX�s7aWptRKFfpKgQGrjTegUVlY9EOP4etAlrUZGHIX75Ai5z1v/ODHqXKPIBf+JD+LSt5bl2qZUBl6giTcTk86Ljts3rxsPVm0Y�MwgG6NbwhSa15qk2UT4bVn4O4TBUpq8585EQ6Bw�va06dOYpRodNwhSIgRr56RJA7x5yEHjl6Easi7Eacl6FEyH+XkN4VsgZ7MZWye74SaiYJKnoQxt2B3A8l/4lx,QcMs/dI+fizS8WCtMfDA8K6ak9D�PQsNP9Sj2mfSh0DZUI02UBl6giTcTk86LjvpF+I9qhpNaxpcXoT9+Stn4OLKB8WC2MLpOPBE/4lx8jpku8/OFoJu0Mxk86xTrWO2uv�mc+8mWJGmaXa4sUfBV5csudDFc4QGV443zlzoRY22a/fSB+0nllA9wLApXB j6umUrMWAzI4RCPn5V0hwwyw9uD9XCv�9sp6SA5jvBgYIKoGDd2tjXPugcH7CRs
4q+Q7fatwGWk86UCM96B07sJHljjxPxR8vb8cwjdthN55hRTCEV+4h�KR8vAZ/FzM8rV/F8O+We6qRnddZtAVmxSDZ/kGjC4sRcESZv9M57sOpTil2BfItMkydWsECms7We0VDZ/gyRxxzYGWO�OVxU1NbOSpwYbN7W4wMMzzVp7SFt6li6h/tY9jBu0zm47lycyY2qKNI3ZN/e5/XY8OAO9RWruh+iQw8WxzYGbReHBnzSAO07kk5BrsXejHRtYDaeTn3H0UJuq7muGCRmppI8SlIC�W+q0nuKhsGow9fjzI7QIAkNHW0q1SPWkREKmx5jBnzimKfzlG1hf0MrgAhZ76JZZxXx+QUusWq)ezq+wCZNv9lqRSvX g+huBXwPXCSCvqZYRL8BPkgqOpRiXRD8u/64s9eYgwfeoAY_CZzNomKkMPa07G73CT+a43G55icsXRjEZxM2/64O2uOTil2BfItMTSsl2O kRE0j3dlQubOtH8zYCk0ZfvuULjaj+oMYRdowb1ESotnfKY3Rj35fYAQIgME7yWGLMwV7ac8UBl60r45jBnzimKfzlG1hfvDeeqz7K6jkWVZ0PcjnTI�b3g9DcLKGqz70aS0OV5dclHrZNUDdmuk/sQ�5s6dMIxMA8l/4lx,QcMs/dI+fPAGqWQSwOBRV6c80oOiHrdCSMnVuJEYt3OrEU4HiID/WJK29iB1tddZvce/Y3fJuZCyBr+y9TCyBr+y9Y22vvkpN/RjBOePDFcdWnuhfe637Etka6OrnBSN2Nk1rMPHrRfKzPxlMu0rKNIhijgC3Az/LlMvHkeDFTfxgUNxOuNclljtWrm6g6AsvDEDmD1mkv8KnLZ0PoohIKS7IEEQRwsdRo/I379ERrydIoCuaV8m1J3NZM+XH62C68gLkccKboMC427oGSbFkI9TnPsDNZkIt02wM5f1XzUux+a2KfItMX2+ZRn2tYAjeP7gqCoOwtLWdxPaUUVkKZDRNML4BmiptLH22+ZdaNhTVf3kjRtzLDbwxv/lw8pfr3U0qRtzLDbwxv/lPLQBOCgqA0NifCccRSq82cIqUM�ivd6vp6MVEq+9wi�KBpQMtPz8/6fCccRoHfGqYVq9sa++snFZumhHzIX/QX1+6h/Azme7TBTyDnWPiUhacDuNrwRzq+D21zqRsh/AzmuyDnWPiD5uU144/TXuC85eAX0BUAdugUNxOuNclljtWrm6gHCsuAhTa/SHDCoc2eNOGboOIfjzIedwEvxFSljPuscJSU0HBYBSfAzme7TBTyDnWPiY0H/EMzlKzXEHJC85gjW3H8qH5I2Si.Bvplf394phVI�ek5/yc1ZOmNW/YOMB+0+295w75uknMNKErasip3V6uR/CRkda�+TY9zAuo3zShQGh3GDI97lx7Sm�PQz24DbQF7TjcavRqlup5A0NifCccleJ/ef29YAvtCzxElB8T9DsLGzwk76XaLoAC7Y6RKk-w5BITAqEI/NkXgYez9sVG0IA97C�/uXq8ug7Cg�XnGaMH7FrM/j5o04BO4asx77x80dMXjzfmJG66YHTUH5RWKibfr5TO/o7M/NSUj77lzzEdvREkFRg"SCG9spWhMYUAMlB1RPgpFcC/IwNsTVTXHlA�AMlB1RPgpWEC6SMZrixj0tV375/L8aY+KjvUIgvtClycw/zJa3xLk9+OPrg3v7u9pZRwXtu/HzfKxeBZ9Hd7PdQssBxifYkib795wkH0BctdLl/qK6WyzHu7B�EwEeCrtPNoQ72vh+tNLjamSOzfKxeBZ9Hd7tK/ X8z7H0WtNQ6vo6Ps0zHu75R5I2ZQGZIr7i4EorqmncigJ2rKfzlG1aZEN5u75R5I2ZZcmP769Hd7tK/ X8z7H0WtNQ6vryL3XqYAD3fa6IG3Q�19YaHwkR8v3MKIvuf7Pp/U++sG3HJSpgNPsGDusB/iwci+qnMvdSiFSEX8t8Y7MC4t+9PvUpQb1NsPZntG3HJkcwkZJy45jmvujUmEC7p7wsDLBZeia0b1whTdJTOSX(shIfiS/TAPO1lklckpI4esMYSqSWOPxy50Iia0q/RY4RXjq1Aa9TJBoaVHHMgTpciWDW5Hu7J9hs0k3gRP9WQIeES2MOBGI2hiXAfBCD6Lq0G9lXYGl52VwgkRsNE5nJi90eQ6973pF7nWk2ne/Wm9O/vpXs4LuVMD7uwNmqUX�c3RZgT�de�Kdr)LSa/w6sRh/IF6zIfiSt9X+KANE5nJi90ee8BG+685CYClycpW'4A3SqpTUhaZbWvGR2rnafVEit08zELxHWyQwwci+qnMvdSiFSEX8t8Y7MC4t+9Pf/cOPvfJuZCyBr0n3G/0DByMARqXweCrHdueKAM9zEhWxp hfdqxQJfd7m/TAE3tEuxfiS/ghsFkHOlhHx9ycw/zJa3x4oyhWxpEavH6XGSy/(Mw8VrEHjljhr�c2yv+kc/m4Bm8/hXCQlRD9gskLARXCD+2z8VHfT/26mZstbc5aki+H/MsdU5Y�xktxNt7fr0Ojb4rereMETkISNckOpsq7Eap9zWm6shlj+DfFf0ZtfwAXMlG0OjpTkqhIDL9mKi6DcDiVYQdELg7cSPZvzM8P4Q+0a434RrY4sRcESZv9M56qSC8vp_HvwrSLz"xOTrbm8KpEvGuh+lTqQF9G xjgO+SyWQisp2L8pOs9naKEHez+tLApXB t7q5ZU0Ry86bPZe6A3UrfLNUtO0K/wPDcRj+GTf+0/2rht4/iBws+vjYB5rOjYP70UltF0x5GKvW0bx5SlCFvZZBhMvSvO8R4zfD573+DgzRNedhVPF9VXl596fekVV+yf2Dhp9mVHEwTaHpNezeTTVrw8hABVzCGENGpUm38aZUAu4NcUFw7UNzjrzXC8HAE5IdxHqG8676/r5xb2G5+PGC0LRLfk7UNzjrzXC8HNdSU4kQ831J3smbGP2iBZmkfkjGHmF4C9NBgRVDGjXjqixRH,B3UPU4etA1vD/L/2+deKm�AmuBrC8HWqTqG5Cxdt69q�kZilUHpcMH jInC2nE9zOPAo2rh7BWnVpR+wsvyXUvzn+rioS2s/1huM6e9kIjcZ6esv4DdeNYtaB21vhTPWMwUa5pYUd0VCKhn5jwAXMlG0OjpTkqZjENKjJCRVidNhqqYVq9sa++n/BMTz468fo+swRkX+O59B0K8YPdtRLJz85Pj7uNV1kH3hm88uXc05sgJ6gmMgTpciWDrCngqG5wWhgXjnvE4igIKOlkbC0rFeMoKSg2A9uhLaCLdhTmtRpkVqYWU3LhhclC+ZdDP85sbFGz5zIAC9QBNuTmRN0ee8V9286LzNcauhLa2fLMNhyCL/jS�21FcANezeTTPzP+OvfXQM1yqILihiXp+EDah7IhBMDYqlhKHcwj�V8ihfCaKQAdqCz4P6x7MHzhvkaMfQsQ+qCtJsaqK�dWst+HM6eXkhTaC+jGNtxohGik15sskDDKmKMOEoDNqIOjx0DMg5jRMl2Ftc5�0XyS7Jbmxc9e8Kp7wSA2RTJhLPHrRRR8CDOQTAYq40PpDy4VeJEqnhswSA2RTJhLPHKur3ZEiXzOR0VCKhK0ZfvA08zCGErLIkEaAjjbeXsvMDcxuHvseKkQIMiAa3x8L2ws2bhZe7eSGpsZNifXDsyfCCS5jXZKVkG6q+akVIuDv46KhN9QYO48I68IqDm/174MV�U8Qk15r0spwcx1Df3My3/qYTQIiWgXjy�xoY4vW7nKBpErMjmdnNjID5QWXCOrfcw/N8A8xtZntdLMMRGZiwr�c5akiOXputsG9spWG7TZ(L2wHlhx55S6t+td0VumqQuvtGQY52MOBGIXRGsuq2nIf//u33P/pwi2203ULdbQbrcV1a6cqc3nuF0twWP1KMOZj0xGOOiIR0IHeCJMt/jjTIxHTS+8rwr�BsPZhjwLQfRZ4KFtcjXvVf/xll5lIUoCI+SnY/ nNXMlq0An/c6kuh�21FcANez8IhfeD3xNHG6B2jzX5CocGs�/VpdkmqN280xWTau3FMTfuKx0MhLB+9N+xOvthIUBUxK+e0WYnOncG6Cdse6QtzXuC85esLgNPKWZsumi54E7UgZLy4TjsjtZRehCR0IYjRT+wqzpZ9N4T92pQKoRHdhYz�/r+y9Tr+MqEW269L8Ej4gV5V�xFRwUQr281DkpHSkwk6V8B9WmKWTkuCtTn/u�y7W/Rj7UC6R8Gfpv6V7dP4jsucy6xOlmgQC6pHuZ0DigHGBw/AX3uKJs3evAD,poOSx1J04BXlgTnUMKZOUAepTRdvUmZuFtjX8jO37KAbsSeXNmhB4dCmecwDca61Z7E4CcA7Y0u47qPkUAemgnDmd4CRVWuSnSqVh2P0j67rpRlxsHR5MMeW+CcAzZG+68xaspSkww0siB8M8Sots8QTcnHNK1WkX9Bpv6ucm3dxxp(vpUOtU62858djs47VOGPu0VHpaZ0+eEEGT+NWRMhwU6zBez8ypvz3uLCvIy0GygDurWA�4XMMnQtsCaZo8rfZ3n0cIEAcC7ggpLDnH�q2AVvy2poxkwi7EjhtJDzVUzg4T90eP68Iqm/r2A�/ZTK �j+6Vac6pgpzWCXiYkwi00iF2hgy2poeDOKs1pj5qIN27HEhH7iTq3WCiuDvsNa53 6zap1ghNhVu59BAkAhETMWPiD5uU9wiRb3gIKA4KFtcjhExL4W3I0rLIkEavTQtAazRwMMKX