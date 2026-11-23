#!/usr/bin/env python3
"""news-image-20261123: sum up the world news of Monday 23 November 2026
in one 1024x1024 PNG. Standard library only, no network, deterministic.

Draws a newspaper front page: a header naming the date, then six story
cards (climate, Europe, USA, Ukraine, markets, disaster), each with a
hand-drawn pictogram, a headline and a short factual summary. The image is
rendered with a hand-rolled 5x7 bitmap font and a hand-rolled PNG encoder.
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (245, 239, 227)
INK = (22, 35, 47)
NAVY = (18, 37, 64)
GOLD = (217, 164, 65)
CARD = (255, 255, 255)
CARD_LINE = (216, 207, 186)
MUTED = (90, 100, 112)
WHITE = (255, 255, 255)

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 cells, '#' = ink. Written from scratch for this
# entry; only capitals are needed because all text is upper-cased.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".....", "..#.."),
    ",": (".....", ".....", ".....", ".....", ".....", "..#..", ".#..."),
    ":": (".....", "..#..", ".....", ".....", ".....", "..#..", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "'": ("..#..", "..#..", ".....", ".....", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "...#.", "...#.", "..#..", "..#..", ".#...", "#...."),
    "%": ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "=": (".....", ".....", ".###.", ".....", ".###.", ".....", "....."),
    "*": (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
}

BLANK = (".....",) * 7


def text_width(s, scale):
    """Pixel width of s at the given scale (1px gap column per glyph)."""
    return len(s) * (5 * scale + scale) - scale


def wrap_text(s, max_chars):
    """Greedy word wrap; returns a list of lines, each <= max_chars."""
    words = s.split()
    lines, cur = [], ""
    for word in words:
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= max_chars:
            cur += " " + word
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def fill_rect(self, x0, y0, x1, y1, color):
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.w, x1)
        y1 = min(self.h, y1)
        for y in range(y0, y1):
            i = (y * self.w + x0) * 3
            self.px[i:i + (x1 - x0) * 3] = bytes(color) * (x1 - x0)

    def line(self, x0, y0, x1, y1, color, thick=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            for a in range(thick):
                for b in range(thick):
                    self.set(x0 + a, y0 + b, color)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def fill_circle(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, color)

    def circle_top(self, cx, cy, r, color):
        """Filled upper half of a circle (dome)."""
        for dy in range(-r, 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, color)

    def fill_poly(self, pts, color):
        """Scanline polygon fill for a list of (x, y) vertices."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[j]), y, int(xs[j + 1]) + 1, y + 1, color)

    def text(self, x, y, s, scale, color):
        s = s.upper()
        cx = x
        for ch in s:
            glyph = FONT.get(ch, BLANK)
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "#":
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       cx + (col + 1) * scale,
                                       y + (row + 1) * scale, color)
            cx += 6 * scale

    def text_center(self, y, s, scale, color):
        self.text((self.w - text_width(s, scale)) // 2, y, s, scale, color)


# ---------------------------------------------------------------- pictograms
def icon_globe(c, x, y, s):
    """COP31: a warming globe, cracked, under a hot sun."""
    cx, cy, r = x + s // 2, y + s // 2 + 6, 40
    c.fill_circle(cx, cy, r, (46, 125, 79))
    c.fill_circle(cx - 14, cy - 10, 12, (126, 199, 143))
    c.fill_circle(cx + 16, cy + 12, 10, (126, 199, 143))
    c.fill_rect(cx - r, cy + 16, cx + r, cy + 20, (18, 37, 64))
    c.line(cx - 26, cy - 26, cx - 8, cy - 6, (18, 37, 64), 3)
    c.line(cx - 8, cy - 6, cx + 6, cy - 18, (18, 37, 64), 3)
    c.line(cx + 6, cy - 18, cx + 24, cy + 2, (18, 37, 64), 3)
    c.fill_circle(x + s - 16, y + 10, 11, (217, 164, 65))
    for dx, dy in ((0, -18), (13, -13), (18, 0), (13, 13)):
        c.line(x + s - 16, y + 10, x + s - 16 + dx, y + 10 + dy, (217, 164, 65), 3)


def icon_rocket(c, x, y, s):
    """Poland: a cruise missile, flying left to right."""
    cy = y + s // 2
    c.fill_poly([(x + 8, cy - 12), (x + 8, cy + 12), (x + 52, cy)], (176, 58, 46))
    c.fill_rect(x + 52, cy - 12, x + 92, cy + 12, (200, 208, 216))
    c.fill_rect(x + 92, cy - 12, x + 100, cy + 12, (90, 100, 112))
    c.fill_circle(x + 70, cy, 7, (43, 94, 167))
    c.fill_poly([(x + 52, cy + 12), (x + 64, cy + 26), (x + 74, cy + 12)], (176, 58, 46))
    c.fill_poly([(x + 52, cy - 12), (x + 64, cy - 26), (x + 74, cy - 12)], (176, 58, 46))
    c.fill_poly([(x + 100, cy - 8), (x + 100, cy + 8), (x + 118, cy)], (217, 164, 65))
    c.line(x + 4, cy - 30, x + 30, cy - 30, (90, 100, 112), 2)
    c.line(x + 0, cy + 30, x + 26, cy + 30, (90, 100, 112), 2)


def icon_capitol(c, x, y, s):
    """USA: the Capitol dome above its columns."""
    cx = x + s // 2
    base = y + s - 18
    c.circle_top(cx, base - 34, 34, (43, 94, 167))
    c.fill_rect(cx - 3, base - 78, cx + 3, base - 66, (43, 94, 167))
    c.fill_poly([(cx + 3, base - 78), (cx + 16, base - 73), (cx + 3, base - 68)],
                (176, 58, 46))
    c.fill_rect(cx - 34, base - 34, cx + 34, base - 28, (43, 94, 167))
    for i in range(4):
        col_x = cx - 27 + i * 18
        c.fill_rect(col_x, base - 28, col_x + 8, base - 6, (90, 100, 112))
    c.fill_rect(cx - 40, base - 6, cx + 40, base, (43, 94, 167))


def icon_rescue(c, x, y, s):
    """Ukraine: rubble below, a rescue cross above it."""
    cx = x + s // 2
    c.fill_poly([(x + 12, y + s - 14), (x + 44, y + s - 44), (x + 76, y + s - 14)],
                (120, 128, 138))
    c.fill_poly([(x + 48, y + s - 14), (x + 82, y + s - 40), (x + 112, y + s - 14)],
                (90, 100, 112))
    c.fill_rect(cx - 26, y + 8, cx + 26, y + 60, WHITE)
    c.fill_rect(cx - 7, y + 16, cx + 7, y + 52, (176, 58, 46))
    c.fill_rect(cx - 18, y + 27, cx + 18, y + 41, (176, 58, 46))
    c.fill_circle(cx - 40, y + s - 30, 6, (22, 35, 47))
    c.fill_circle(cx + 38, y + s - 26, 6, (22, 35, 47))


def icon_chip(c, x, y, s):
    """Markets: a chip with a red falling arrow."""
    cx, cy = x + s // 2 - 8, y + s // 2 - 6
    c.fill_rect(cx - 34, cy - 34, cx + 34, cy + 34, (22, 35, 47))
    c.fill_rect(cx - 20, cy - 20, cx + 20, cy + 20, (108, 79, 161))
    c.fill_rect(cx - 8, cy - 8, cx + 8, cy + 8, (217, 164, 65))
    for i in range(3):
        px = cx - 22 + i * 22
        c.fill_rect(px, cy - 44, px + 6, cy - 34, (90, 100, 112))
        c.fill_rect(px, cy + 34, px + 6, cy + 44, (90, 100, 112))
        py = cy - 22 + i * 22
        c.fill_rect(cx - 44, py, cx - 34, py + 6, (90, 100, 112))
        c.fill_rect(cx + 34, py, cx + 44, py + 6, (90, 100, 112))
    ax, ay = x + s - 46, y + s - 44
    c.fill_poly([(ax, ay), (ax + 34, ay), (ax + 34, ay + 10), (ax + 24, ay + 10),
                 (ax + 24, ay + 34), (ax + 14, ay + 34), (ax + 14, ay + 10),
                 (ax, ay + 10)], (176, 58, 46))


def icon_quake(c, x, y, s):
    """Vanuatu: a seismograph trace over cracked ground."""
    cy = y + s // 2 - 8
    pts = [(x + 6, cy), (x + 22, cy), (x + 30, cy - 26), (x + 38, cy + 22),
           (x + 46, cy - 34), (x + 54, cy + 28), (x + 62, cy - 10),
           (x + 74, cy), (x + 118, cy)]
    for a, b in zip(pts, pts[1:]):
        c.line(a[0], a[1], b[0], b[1], (176, 58, 46), 3)
    gy = y + s - 22
    c.fill_rect(x + 6, gy, x + s - 6, gy + 5, (120, 100, 70))
    c.line(x + 30, gy + 4, x + 26, gy + 12, (22, 35, 47), 3)
    c.line(x + 26, gy + 12, x + 32, gy + 18, (22, 35, 47), 3)
    c.line(x + 84, gy + 4, x + 88, gy + 12, (22, 35, 47), 3)
    c.line(x + 88, gy + 12, x + 82, gy + 18, (22, 35, 47), 3)


ICONS = (icon_globe, icon_rocket, icon_capitol, icon_rescue, icon_chip, icon_quake)

# -------------------------------------------------------------------- stories
# Each story was first reported on Monday 23 November 2026 (BBC, Reuters,
# AP, UKMTO and wire coverage of that day).
STORIES = [
    ("CLIMATE", (46, 125, 79), "COP31 COLLAPSES",
     "Climate talks in Turkey end with no major deal as nations split over "
     "fossil fuels and finance."),
    ("EUROPE", (43, 94, 167), "RUSSIAN MISSILES IN POLAND",
     "Poland confirms three fallen objects were Russian cruise missiles. "
     "NATO to meet."),
    ("USA", (176, 58, 46), "DEMOCRATS WIN BIG",
     "Democrats take their largest House majority since 1992 after flipping "
     "a North Carolina seat."),
    ("UKRAINE", (201, 138, 27), "BOY, 7, PULLED ALIVE",
     "Rescuers pull a seven-year-old boy alive from rubble hours after a "
     "Russian strike near Kyiv."),
    ("MARKETS", (108, 79, 161), "NVIDIA CHIEF STEPS DOWN",
     "Nvidia CEO Huang Renxun steps down as Taiwan curbs short selling and "
     "Asian shares plunge."),
    ("DISASTER", (198, 93, 33), "QUAKE HITS VANUATU",
     "A magnitude 6.5 earthquake strikes the Vanuatu region in the Pacific."),
]


def tint(color):
    return tuple(235 + (c - 235) // 4 if c > 235 else 232 + c // 16
                 for c in color)


def draw_card(c, x, y, w, h, tag, accent, headline, body, icon_fn):
    c.fill_rect(x, y, x + w, y + h, CARD)
    c.fill_rect(x, y, x + w, y + h, CARD_LINE)  # placeholder, overdrawn below
    c.fill_rect(x + 1, y + 1, x + w - 1, y + h - 1, CARD)
    # tag strip
    c.fill_rect(x + 1, y + 1, x + w - 1, y + 37, accent)
    c.text(x + 14, y + 12, tag, 2, WHITE)
    # icon panel
    panel_w = 132
    c.fill_rect(x + 1, y + 37, x + 1 + panel_w, y + h - 1, tint(accent))
    icon_fn(c, x + 6, y + 37 + (h - 37 - 118) // 2, 118)
    # headline + body, vertically centred in the space below the tag strip
    tx = x + 1 + panel_w + 16
    tw = w - panel_w - 32
    head_lines = wrap_text(headline, tw // (6 * 3))[:3]
    body_lines = wrap_text(body, tw // (6 * 2))[:5]
    total_h = len(head_lines) * 28 + 12 + len(body_lines) * 19
    hy = y + 37 + (h - 37 - total_h) // 2
    for line in head_lines:
        c.text(tx, hy, line, 3, INK)
        hy += 28
    by = hy + 12
    for line in body_lines:
        c.text(tx, by, line, 2, MUTED)
        by += 19


def render():
    c = Canvas(W, H, PAPER)
    # header
    c.fill_rect(0, 0, W, 148, NAVY)
    c.fill_rect(0, 148, W, 152, GOLD)
    c.text_center(26, "MONDAY 23 NOVEMBER 2026", 4, WHITE)
    c.text_center(76, "THE WORLD IN ONE IMAGE", 3, GOLD)
    c.text_center(112, "TOP STORIES OF THE DAY", 2, (200, 208, 216))
    # six cards: 2 columns x 3 rows
    margin, gap = 14, 12
    cw = (W - 2 * margin - gap) // 2
    ch = 262
    for i, (tag, accent, headline, body) in enumerate(STORIES):
        col, row = i % 2, i // 2
        x = margin + col * (cw + gap)
        y = 164 + row * (ch + gap)
        draw_card(c, x, y, cw, ch, tag, accent, headline, body, ICONS[i])
    # footer
    c.text_center(994, "AS REPORTED ON 23 NOVEMBER 2026 - BBC - REUTERS - AP",
                  2, MUTED)
    return c.px


# ---------------------------------------------------------------- PNG encoder
def png_bytes(w, h, rgb):
    raw = b"".join(b"\x00" + bytes(rgb[y * w * 3:(y + 1) * w * 3])
                   for y in range(h))

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        return out + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 6))
            + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(W, H, render())
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
