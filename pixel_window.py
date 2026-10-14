#!/usr/bin/env python3
"""Display an animated pixel-art view through a wooden window."""

import argparse
import configparser
import math
import time
from pathlib import Path

from PIL import Image, ImageDraw

WIDTH = 192
HEIGHT = 128


def blend(first, second, amount):
    amount = max(0.0, min(1.0, amount))
    return tuple(round(a + (b - a) * amount) for a, b in zip(first, second))


def draw_scene(phase, elapsed=0.0):
    """Render one frame. phase runs from midnight (0) through the day (0.5)."""
    daytime = max(0.0, math.cos(2 * math.pi * (phase - 0.5)))
    night = 1.0 - daytime
    image = Image.new("RGB", (WIDTH, HEIGHT), (9, 17, 48))
    draw = ImageDraw.Draw(image)

    sky_top = blend((8, 15, 44), (72, 157, 224), daytime)
    sky_bottom = blend((37, 40, 83), (174, 218, 239), daytime)
    for y in range(12, 101):
        draw.line((12, y, 179, y), fill=blend(sky_top, sky_bottom, (y - 12) / 89))

    # Stars fade out in daylight and twinkle gently after dark.
    stars = (
        (24, 23), (42, 42), (57, 18), (70, 31), (88, 21), (105, 43),
        (119, 17), (140, 29), (157, 20), (169, 45), (31, 61), (75, 57),
        (126, 55), (151, 63), (96, 68), (46, 34), (164, 34), (111, 28),
    )
    for index, (x, y) in enumerate(stars):
        intensity = night * (0.65 + 0.35 * math.sin(elapsed * 2 + index))
        star = blend(sky_top, (255, 246, 194), intensity)
        draw.point((x, y), fill=star)
        if index % 5 == 0 and intensity > 0.55:
            draw.point((x + 1, y), fill=star)
            draw.point((x, y + 1), fill=star)

    # A small sun follows an arc; the crescent moon occupies the opposite sky.
    sun_x = round(24 + (phase % 1.0) * 143)
    sun_y = round(53 - 30 * math.sin(math.pi * (phase % 1.0)))
    sun_color = blend((248, 161, 96), (255, 225, 112), daytime)
    if daytime > 0.05:
        draw.rectangle((sun_x - 5, sun_y - 5, sun_x + 5, sun_y + 5), fill=sun_color)
        draw.rectangle((sun_x - 3, sun_y - 7, sun_x + 3, sun_y + 7), fill=sun_color)

    moon_x = round(24 + ((phase + 0.5) % 1.0) * 143)
    moon_y = round(53 - 30 * math.sin(math.pi * ((phase + 0.5) % 1.0)))
    moon_glow = blend(sky_top, (247, 239, 196), night)
    if night > 0.05:
        draw.rectangle((moon_x - 4, moon_y - 5, moon_x + 4, moon_y + 5), fill=moon_glow)
        draw.rectangle((moon_x - 6, moon_y - 3, moon_x + 6, moon_y + 3), fill=moon_glow)
        for mask_y in range(moon_y - 6, moon_y + 5):
            mask_color = blend(sky_top, sky_bottom, (mask_y - 12) / 89)
            draw.line((moon_x - 1, mask_y, moon_x + 6, mask_y), fill=mask_color)

    # Distant hills, tree line, and grassy foreground.
    distant = blend((32, 47, 83), (101, 157, 129), daytime)
    nearer = blend((22, 39, 58), (57, 117, 82), daytime)
    ground = blend((24, 49, 49), (91, 151, 77), daytime)
    draw.polygon(
        [(12, 78), (34, 61), (51, 75), (73, 57), (97, 78),
         (122, 62), (143, 77), (162, 59), (179, 74), (179, 101), (12, 101)],
        fill=distant,
    )
    draw.polygon(
        [(12, 85), (31, 76), (49, 84), (66, 72), (86, 87), (111, 73),
         (132, 85), (153, 72), (179, 85), (179, 101), (12, 101)],
        fill=nearer,
    )
    draw.rectangle((12, 91, 179, 101), fill=ground)
    for x, y in ((20, 84), (45, 87), (82, 83), (119, 86), (151, 82), (171, 88)):
        draw.rectangle((x, y - 5, x + 3, 91), fill=blend((18, 34, 43), (43, 91, 57), daytime))
        draw.rectangle((x - 2, y - 9, x + 5, y - 5), fill=nearer)
    for x in range(17, 177, 13):
        draw.point((x, 94 + (x % 5)), fill=blend(ground, (174, 192, 101), daytime * 0.5))

    # A few blocky clouds drift across the sky.
    cloud_color = blend((61, 74, 113), (239, 247, 248), daytime)
    for base_x, y, width in ((37, 48, 19), (111, 39, 23)):
        x = 15 + int((base_x - 15 + elapsed * 5) % 150)
        if y < 75:
            draw.rectangle((x, y, x + width, y + 3), fill=cloud_color)
            draw.rectangle((x + 4, y - 2, x + width - 4, y + 3), fill=cloud_color)

    # Thick pixel-art frame and sill sit in front of the outdoor view.
    draw.rectangle((0, 0, 191, 8), fill=(49, 28, 20))
    draw.rectangle((0, 9, 8, 106), fill=(67, 37, 23))
    draw.rectangle((183, 9, 191, 106), fill=(67, 37, 23))
    draw.rectangle((9, 9, 11, 105), fill=(147, 91, 48))
    draw.rectangle((180, 9, 182, 105), fill=(147, 91, 48))
    draw.rectangle((0, 102, 191, 108), fill=(55, 31, 21))
    draw.rectangle((9, 103, 182, 105), fill=(157, 99, 53))
    draw.rectangle((0, 109, 191, 119), fill=(104, 61, 34))
    draw.rectangle((0, 120, 191, 127), fill=(57, 34, 25))
    draw.rectangle((0, 109, 191, 111), fill=(177, 119, 67))
    draw.rectangle((0, 117, 191, 119), fill=(76, 44, 29))
    # Center mullion divides the view into two panes.
    draw.rectangle((93, 10, 98, 101), fill=(80, 46, 29))
    draw.rectangle((93, 10, 94, 101), fill=(169, 109, 59))
    draw.rectangle((12, 54, 179, 57), fill=(80, 46, 29))
    draw.rectangle((12, 54, 179, 55), fill=(169, 109, 59))
    return image


def load_matrix_settings(config_path):
    config = configparser.ConfigParser()
    if not config.read(config_path):
        raise FileNotFoundError(f"Matrix config not found: {config_path}")
    if not config.has_section("Matrix"):
        raise ValueError(f"Missing [Matrix] section in {config_path}")
    settings = config["Matrix"]
    rows = settings.getint("rows")
    cols = settings.getint("cols")
    chain_length = settings.getint("chain_length")
    parallel = settings.getint("parallel")
    if (cols * chain_length, rows * parallel) != (WIDTH, HEIGHT):
        raise ValueError(
            f"Expected a {WIDTH}x{HEIGHT} matrix; config describes "
            f"{cols * chain_length}x{rows * parallel}"
        )
    return settings


def run_matrix(settings, fps, cycle_seconds):
    from rgbmatrix import RGBMatrix, RGBMatrixOptions

    options = RGBMatrixOptions()
    options.hardware_mapping = settings.get("hardware_mapping", "regular")
    options.rows = settings.getint("rows")
    options.cols = settings.getint("cols")
    options.chain_length = settings.getint("chain_length")
    options.parallel = settings.getint("parallel")
    options.brightness = settings.getint("brightness", fallback=50)
    options.gpio_slowdown = settings.getint("gpio_slowdown", fallback=1)
    options.limit_refresh_rate_hz = settings.getint("limit_refresh_rate_hz", fallback=0)
    panel_type = settings.get("led-panel-type", "").strip()
    if panel_type:
        options.panel_type = panel_type

    matrix = RGBMatrix(options=options)
    canvas = matrix.CreateFrameCanvas()
    start = time.monotonic()
    try:
        while True:
            elapsed = time.monotonic() - start
            phase = (elapsed / cycle_seconds) % 1.0
            canvas.SetImage(draw_scene(phase, elapsed))
            canvas = matrix.SwapOnVSync(canvas)
            time.sleep(1 / fps)
    except KeyboardInterrupt:
        matrix.Clear()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.ini", help="RGB matrix INI file")
    parser.add_argument("--fps", type=int, default=12, help="Animation frame rate")
    parser.add_argument(
        "--cycle-seconds",
        type=float,
        default=120,
        help="Duration of one complete day/night cycle",
    )
    parser.add_argument(
        "--preview",
        type=Path,
        help="Save a still PNG preview instead of starting the LED matrix",
    )
    parser.add_argument(
        "--phase",
        type=float,
        default=0.35,
        help="Preview time from 0 (midnight) to 1 (next midnight)",
    )
    args = parser.parse_args()
    if args.fps <= 0 or args.cycle_seconds <= 0:
        parser.error("--fps and --cycle-seconds must be positive")
    if not 0 <= args.phase < 1:
        parser.error("--phase must be in the range [0, 1)")

    if args.preview:
        draw_scene(args.phase).save(args.preview)
        print(f"Saved {WIDTH}x{HEIGHT} preview to {args.preview}")
    else:
        settings = load_matrix_settings(args.config)
        run_matrix(settings, args.fps, args.cycle_seconds)


if __name__ == "__main__":
    main()
