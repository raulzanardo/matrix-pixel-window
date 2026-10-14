#!/usr/bin/env python3
"""Display an animated pixel-art view through a wooden window."""

import argparse
import configparser
from datetime import datetime
import math
import time
from pathlib import Path

from PIL import Image, ImageDraw

WIDTH = 192
HEIGHT = 128


def blend(first, second, amount):
    amount = max(0.0, min(1.0, amount))
    return tuple(round(a + (b - a) * amount) for a, b in zip(first, second))


def local_clock_phase(now=None):
    now = now or datetime.now().astimezone()
    seconds = now.hour * 3600 + now.minute * 60 + now.second + now.microsecond / 1_000_000
    return seconds / 86_400


def draw_scene(phase, elapsed=0.0):
    """Render a full-screen city view for local time from midnight (0) to midnight (1)."""
    daytime = max(0.0, math.cos(2 * math.pi * (phase - 0.5)))
    night = 1.0 - daytime
    image = Image.new("RGB", (WIDTH, HEIGHT), (9, 17, 48))
    draw = ImageDraw.Draw(image)

    sky_top = blend((8, 15, 44), (72, 157, 224), daytime)
    sky_bottom = blend((37, 40, 83), (174, 218, 239), daytime)
    for y in range(0, 107):
        draw.line((0, y, 191, y), fill=blend(sky_top, sky_bottom, y / 106))

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

    # Blocky clouds drift across the sky behind the celestial bodies.
    cloud_color = blend((61, 74, 113), (239, 247, 248), daytime)
    for base_x, y, width in ((37, 48, 19), (111, 39, 23)):
        x = 15 + int((base_x - 15 + elapsed * 5) % 150)
        draw.rectangle((x, y, x + width, y + 3), fill=cloud_color)
        draw.rectangle((x + 4, y - 2, x + width - 4, y + 3), fill=cloud_color)

    clock_seconds = phase * 86_400
    sun_progress = (clock_seconds - 6 * 3600) / (12 * 3600)
    sun_color = blend((248, 161, 96), (255, 225, 112), daytime)
    if 0 <= sun_progress <= 1:
        sun_x = round(18 + sun_progress * 150)
        sun_y = round(58 - 34 * math.sin(math.pi * sun_progress))
        draw.rectangle((sun_x - 5, sun_y - 5, sun_x + 5, sun_y + 5), fill=sun_color)
        draw.rectangle((sun_x - 3, sun_y - 7, sun_x + 3, sun_y + 7), fill=sun_color)

    moon_progress = ((clock_seconds - 18 * 3600) % 86_400) / (12 * 3600)
    moon_glow = blend(sky_top, (247, 239, 196), night)
    if night > 0.05:
        moon_x = round(18 + moon_progress * 150)
        moon_y = round(58 - 34 * math.sin(math.pi * moon_progress))
        draw.rectangle((moon_x - 4, moon_y - 5, moon_x + 4, moon_y + 5), fill=moon_glow)
        draw.rectangle((moon_x - 6, moon_y - 3, moon_x + 6, moon_y + 3), fill=moon_glow)
        for mask_y in range(moon_y - 6, moon_y + 5):
            mask_color = blend(sky_top, sky_bottom, mask_y / 106)
            draw.line((moon_x - 1, mask_y, moon_x + 6, mask_y), fill=mask_color)

    # Layered apartment blocks and towers form the urban skyline.
    rear_color = blend((24, 34, 61), (112, 132, 147), daytime * 0.75)
    front_color = blend((17, 25, 43), (75, 87, 94), daytime * 0.8)
    roof_color = blend((43, 54, 76), (135, 145, 144), daytime * 0.7)
    rear_buildings = (
        (0, 13, 77), (14, 21, 71), (29, 17, 61), (44, 20, 75),
        (63, 19, 65), (81, 18, 53), (99, 19, 70), (118, 18, 60),
        (136, 20, 73), (156, 21, 63), (178, 14, 74),
    )
    for x, width, top in rear_buildings:
        draw.rectangle((x, top, x + width - 1, 105), fill=rear_color)
        draw.rectangle((x, top, x + width - 1, top + 1), fill=roof_color)
        for row, y in enumerate(range(top + 5, 91, 7)):
            for column, wx in enumerate(range(x + 3, x + width - 2, 6)):
                if (row + column) % 3 != 1:
                    window = blend((29, 43, 61), (244, 190, 103), night * 0.85)
                    draw.rectangle((wx, y, wx + 2, y + 3), fill=window)

    front_buildings = (
        (0, 11, 82), (12, 17, 78), (30, 18, 70), (49, 17, 81),
        (67, 20, 73), (88, 17, 63), (106, 19, 77), (126, 18, 68),
        (145, 19, 80), (165, 15, 72), (181, 11, 81),
    )
    for index, (x, width, top) in enumerate(front_buildings):
        draw.rectangle((x, top, x + width - 1, 106), fill=front_color)
        draw.rectangle((x, top, x + width - 1, top + 1), fill=roof_color)
        if index in (1, 4, 7):
            draw.rectangle((x + 4, top - 4, x + width - 5, top - 1), fill=roof_color)
            draw.rectangle((x + width // 2, top - 10, x + width // 2, top - 5), fill=roof_color)
        for row, y in enumerate(range(top + 5, 104, 7)):
            for column, wx in enumerate(range(x + 3, x + width - 2, 6)):
                glass = blend((33, 51, 68), (255, 192, 102), night * 0.9)
                if (index + row + column * 2) % 4:
                    draw.rectangle((wx, y, wx + 2, y + 3), fill=glass)

    # Rooftop water tanks, antennas, street lamps, road, and passing cars.
    draw.rectangle((37, 64, 44, 69), fill=roof_color)
    draw.rectangle((38, 62, 43, 64), fill=roof_color)
    draw.line((154, 66, 154, 57), fill=roof_color)
    draw.line((151, 61, 157, 61), fill=roof_color)
    road = blend((39, 47, 55), (94, 99, 96), daytime * 0.75)
    draw.rectangle((0, 107, 191, 127), fill=road)
    draw.rectangle((0, 106, 191, 108), fill=blend((75, 79, 79), (158, 157, 143), daytime))
    for lane_x in range(8, 190, 32):
        draw.rectangle((lane_x, 117, lane_x + 13, 118), fill=(177, 164, 115))
    for car_x, car_color in ((35, (166, 67, 55)), (137, (70, 105, 145))):
        draw.rectangle((car_x, 110, car_x + 15, 115), fill=car_color)
        draw.rectangle((car_x + 3, 107, car_x + 12, 110), fill=blend(car_color, (180, 209, 215), 0.55))
        draw.rectangle((car_x + 3, 116, car_x + 5, 117), fill=(15, 18, 23))
        draw.rectangle((car_x + 11, 116, car_x + 13, 117), fill=(15, 18, 23))
        draw.point((car_x + 15, 112), fill=(255, 205, 118))
    for lamp_x in (25, 169):
        draw.rectangle((lamp_x, 88, lamp_x + 1, 106), fill=roof_color)
        draw.rectangle((lamp_x - 2, 87, lamp_x + 3, 89), fill=blend((160, 133, 91), (255, 220, 138), night))
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


def run_matrix(settings, fps):
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
            phase = local_clock_phase()
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
        "--preview",
        type=Path,
        help="Save a still PNG preview at the current local time",
    )
    args = parser.parse_args()
    if args.fps <= 0:
        parser.error("--fps must be positive")

    if args.preview:
        draw_scene(local_clock_phase()).save(args.preview)
        print(f"Saved {WIDTH}x{HEIGHT} preview to {args.preview}")
    else:
        settings = load_matrix_settings(args.config)
        run_matrix(settings, args.fps)


if __name__ == "__main__":
    main()
