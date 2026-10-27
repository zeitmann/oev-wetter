"""Hintergrundbilder fuer die Gesamtpraesentation zeichnen (Thema Wetter und oeV).

Erzeugt zwei PNG in docs/praesentation/design/:
  hintergrund_titel.png   Titelfolie: Schneewolken, Huegel, Zug und Bus auf der rechten Seite
  hintergrund_inhalt.png  Inhaltsfolien: dezente Wolke mit Schnee oben rechts,
                          Huegellinie mit kleinem Zug und Bus am unteren Rand
Die Farben sind bewusst blass, damit Text und Grafiken lesbar bleiben.
Verwendet von src/build_praesentation.py.

Quellen (APA 7):
Clark, A., & Contributors. (2026). Pillow documentation: ImageDraw module.
    https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html
"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter

from build_folien_paket_b import out_dir

# Folienformat 13.333 x 7.5 Zoll; gezeichnet wird doppelt so gross und dann verkleinert
# (Supersampling), damit die Kanten weich werden.
DPI = 150
SCALE = 2
W, H = int(13.333 * DPI * SCALE), int(7.5 * DPI * SCALE)


def px(inch):
    """Zoll in Pixel der Zeichenflaeche."""
    return int(inch * DPI * SCALE)


def sky(top, bottom):
    """Senkrechter Farbverlauf von top (oben) nach bottom (unten)."""
    img = Image.new('RGB', (W, H), bottom)
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        draw.line([(0, y), (W, y)], fill=color)
    return img


def cloud(draw, x, y, size, fill):
    """Wolke aus ueberlappenden Ellipsen; (x, y) = Mitte der Unterkante, size in Zoll."""
    s = px(size)
    parts = [(-.45, -.18, .32), (-.15, -.38, .42), (.22, -.30, .36), (.45, -.14, .26), (0, -.12, .40)]
    for dx, dy, r in parts:
        cx, cy, rr = x + dx * s, y + dy * s, r * s
        draw.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=fill)
    draw.rectangle([x - .45 * s, y - .14 * s, x + .45 * s, y], fill=fill)


def snowflake(draw, x, y, r, fill, width):
    """Schneeflocke mit sechs Armen und kleinen Seitenaesten."""
    for k in range(6):
        a = math.pi / 3 * k
        ex, ey = x + r * math.cos(a), y + r * math.sin(a)
        draw.line([(x, y), (ex, ey)], fill=fill, width=width)
        for side in (-1, 1):
            bx, by = x + .6 * r * math.cos(a), y + .6 * r * math.sin(a)
            b = a + side * math.pi / 4
            draw.line([(bx, by), (bx + .3 * r * math.cos(b), by + .3 * r * math.sin(b))],
                      fill=fill, width=width)


def snow(draw, box, count, rmin, rmax, fill, seed):
    """Flocken zufaellig (aber reproduzierbar) in einem Rechteck verteilen."""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    for _ in range(count):
        r = rnd.uniform(rmin, rmax)
        snowflake(draw, rnd.uniform(x0, x1), rnd.uniform(y0, y1), r, fill, max(2, int(r / 6)))


def hills(draw, base, amplitude, phase, fill, x0=0, x1=W):
    """Weiche Huegellinie (Summe zweier Sinuswellen) bis zum unteren Bildrand."""
    points = [(x0, H)]
    for x in list(range(x0, x1, 8)) + [x1]:
        y = base - amplitude * (math.sin(x / W * 5 + phase) * .6 + math.sin(x / W * 11 + phase * 2) * .4)
        points.append((x, y))
    points.append((x1, H))
    draw.polygon(points, fill=fill)


def train(draw, x, y, length, height, body, window, wheel):
    """Zug mit zwei Wagen und schraeger Front; (x, y) = links unten auf der Schiene."""
    car = length / 2
    for i in range(2):
        left = x + i * (car + height * .08)
        right = left + car
        if i == 1:  # Front des Triebwagens schraeg
            draw.polygon([(left, y - height), (right - height * .5, y - height), (right, y - height * .35),
                          (right, y), (left, y)], fill=body)
        else:
            draw.rounded_rectangle([left, y - height, right, y], radius=height * .15, fill=body)
        n = 4
        for k in range(n):
            wx = left + car * (.08 + k * .2)
            draw.rounded_rectangle([wx, y - height * .78, wx + car * .13, y - height * .45],
                                   radius=height * .05, fill=window)
        for wx in (left + car * .18, right - car * .22):
            r = height * .13
            draw.ellipse([wx - r, y - r * .6, wx + r, y + r * 1.4], fill=wheel)


def bus(draw, x, y, length, height, body, window, wheel):
    """Bus mit Fensterreihe und zwei Raedern; (x, y) = links unten auf der Strasse."""
    draw.rounded_rectangle([x, y - height, x + length, y - height * .12], radius=height * .2, fill=body)
    for k in range(5):
        wx = x + length * (.06 + k * .17)
        draw.rounded_rectangle([wx, y - height * .82, wx + length * .13, y - height * .5],
                               radius=height * .05, fill=window)
    for wx in (x + length * .2, x + length * .8):
        r = height * .16
        draw.ellipse([wx - r, y - r * 1.2, wx + r, y + r * .8], fill=wheel)


def finish(img, name):
    """Leicht weichzeichnen, auf Zielgroesse verkleinern und speichern."""
    folder = out_dir() / 'design'
    folder.mkdir(exist_ok=True)
    img = img.filter(ImageFilter.GaussianBlur(1)).resize((W // SCALE, H // SCALE), Image.LANCZOS)
    img.save(folder / name, optimize=True)
    return folder / name


def titel():
    """Titelfolie: links ruhig fuer den Text, rechts die Illustration."""
    img = sky((223, 236, 244), (250, 252, 253))
    draw = ImageDraw.Draw(img)
    # Wolken und Schneefall rechts oben
    cloud(draw, px(10.6), px(1.75), 2.6, (203, 220, 232))
    cloud(draw, px(12.4), px(1.15), 1.6, (214, 228, 238))
    cloud(draw, px(8.9), px(1.05), 1.2, (226, 236, 243))
    snow(draw, (px(8.3), px(1.9), W, px(5.2)), 60, px(.04), px(.09), (176, 200, 216), seed=4)
    # Huegel in zwei Ebenen, dazu Schiene und Strasse
    hills(draw, px(5.6), px(.35), 1.2, (214, 232, 232))
    hills(draw, px(6.1), px(.2), 2.4, (186, 215, 218))
    draw.rectangle([0, px(6.45), W, H], fill=(160, 198, 204))
    draw.line([(0, px(6.45)), (W, px(6.45))], fill=(23, 54, 74), width=px(.03))
    draw.rectangle([0, px(7.05), W, H], fill=(120, 140, 150))
    for x in range(px(.2), W, px(.5)):
        draw.line([(x, px(7.27)), (x + px(.25), px(7.27))], fill=(235, 240, 242), width=px(.03))
    train(draw, px(7.6), px(6.43), px(3.4), px(.62), (22, 125, 141), (226, 240, 243), (23, 54, 74))
    bus(draw, px(11.3), px(7.03), px(1.6), px(.55), (23, 54, 74), (210, 228, 236), (40, 40, 40))
    # Schnee auch vor den Fahrzeugen, wenige grosse Flocken
    snow(draw, (px(7.0), px(5.2), W, px(7.4)), 18, px(.05), px(.08), (255, 255, 255), seed=9)
    return finish(img, 'hintergrund_titel.png')


def inhalt():
    """Inhaltsfolien: Weiss mit sehr hellem Himmel oben, Deko nur in Ecken und am Rand."""
    img = sky((239, 245, 249), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    cloud(draw, px(12.55), px(.62), .9, (226, 236, 243))
    snow(draw, (px(12.0), px(.65), px(13.25), px(1.25)), 7, px(.03), px(.05), (200, 216, 228), seed=2)
    hills(draw, px(7.32), px(.06), .7, (236, 243, 245))
    train(draw, px(9.9), px(7.36), px(1.3), px(.2), (205, 223, 228), (245, 249, 250), (190, 205, 212))
    bus(draw, px(11.35), px(7.36), px(.6), px(.2), (205, 223, 228), (245, 249, 250), (190, 205, 212))
    return finish(img, 'hintergrund_inhalt.png')


def main():
    for path in (titel(), inhalt()):
        print(path.name)


if __name__ == '__main__':
    main()
