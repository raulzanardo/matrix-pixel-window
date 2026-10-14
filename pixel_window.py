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
    """Render a cozy interior overlooking a city street at local time."""
    daytime = max(0.0, math.cos(2 * math.pi * (phase - 0.5)))
    night = 1.0 - daytime
    image = Image.new("RGB", (WIDTH, HEIGHT), (24, 25, 39))
    draw = ImageDraw.Draw(image)

    sky_top = blend((19, 26, 54), (185, 190, 180), daytime)
    sky_bottom = blend((57, 45, 69), (239, 181, 139), daytime)
    for y in range(8, 94):
        draw.line((7, y, 184, y), fill=blend(sky_top, sky_bottom, (y - 8) / 86))

    stars = (
        (20, 20), (38, 41), (56, 17), (75, 29), (106, 18), (132, 38),
        (165, 22), (177, 45), (88, 33), (148, 57), (43, 60),
    )
    for index, (x, y) in enumerate(stars):
        intensity = night * (0.65 + 0.35 * math.sin(elapsed * 2 + index))
        star = blend(sky_top, (255, 246, 194), intensity)
        draw.point((x, y), fill=star)
        if index % 4 == 0 and intensity > 0.55:
            draw.point((x + 1, y), fill=star)
            draw.point((x, y + 1), fill=star)

    cloud_color = blend((72, 73, 105), (247, 217, 187), daytime)
    for base_x, y, width in ((34, 37, 18), (119, 28, 24), (153, 49, 15)):
        x = 12 + int((base_x - 12 + elapsed * 2) % 164)
        draw.rectangle((x, y, x + width, y + 3), fill=cloud_color)
        draw.rectangle((x + 4, y - 2, x + width - 4, y + 3), fill=cloud_color)

    clock_seconds = phase * 86_400
    sun_progress = (clock_seconds - 6 * 3600) / (12 * 3600)
    sun_color = blend((247, 168, 119), (255, 222, 146), daytime)
    if 0 <= sun_progress <= 1:
        sun_x = round(28 + sun_progress * 136)
        sun_y = round(55 - 29 * math.sin(math.pi * sun_progress))
        draw.rectangle((sun_x - 4, sun_y - 4, sun_x + 4, sun_y + 4), fill=sun_color)
        draw.rectangle((sun_x - 6, sun_y - 2, sun_x + 6, sun_y + 2), fill=sun_color)

    moon_progress = ((clock_seconds - 18 * 3600) % 86_400) / (12 * 3600)
    moon_glow = blend(sky_top, (247, 239, 196), night)
    if night > 0.05:
        moon_x = round(28 + moon_progress * 136)
        moon_y = round(55 - 29 * math.sin(math.pi * moon_progress))
        draw.rectangle((moon_x - 4, moon_y - 5, moon_x + 4, moon_y + 5), fill=moon_glow)
        draw.rectangle((moon_x - 6, moon_y - 3, moon_x + 6, moon_y + 3), fill=moon_glow)
        for mask_y in range(moon_y - 6, moon_y + 5):
            mask_color = blend(sky_top, sky_bottom, (mask_y - 8) / 86)
            draw.line((moon_x - 1, mask_y, moon_x + 6, mask_y), fill=mask_color)

    # A hazy skyline sits at the vanishing point of the street.
    distant = blend((49, 49, 73), (190, 166, 147), daytime)
    for x, top, width in ((61, 49, 8), (71, 44, 10), (82, 51, 8),
                          (103, 47, 9), (114, 42, 10), (125, 51, 7)):
        draw.rectangle((x, top, x + width, 67), fill=distant)
        for wx in range(x + 2, x + width, 4):
            for wy in range(top + 4, 64, 6):
                draw.point((wx, wy), fill=blend(distant, (238, 194, 150), night * 0.6))

    # Warm, close-set apartment facades frame a narrow neighborhood street.
    left_wall = blend((53, 54, 65), (174, 155, 135), daytime)
    left_shadow = blend((38, 43, 54), (113, 103, 92), daytime)
    right_wall = blend((61, 51, 53), (191, 150, 121), daytime)
    brick = blend((70, 47, 46), (184, 112, 88), daytime)
    trim = blend((35, 39, 48), (97, 83, 71), daytime)
    draw.polygon(((8, 15), (49, 13), (78, 34), (78, 91), (8, 91)), fill=left_wall)
    draw.polygon(((8, 15), (49, 13), (53, 19), (8, 22)), fill=trim)
    draw.polygon(((49, 13), (78, 34), (73, 36), (45, 20)), fill=left_shadow)
    draw.polygon(((119, 36), (148, 14), (184, 11), (184, 91), (119, 91)), fill=right_wall)
    draw.polygon(((119, 36), (148, 14), (153, 17), (126, 40)), fill=trim)
    draw.polygon(((148, 14), (184, 11), (184, 19), (153, 21)), fill=brick)

    window_glass = blend((49, 65, 77), (107, 127, 128), daytime)
    window_frame = blend((43, 43, 47), (104, 83, 68), daytime)
    # Repeated windows and balcony rails give the facades a lived-in scale.
    for x, y, width, height in (
        (15, 29, 10, 13), (32, 27, 10, 13), (51, 31, 11, 14),
        (15, 49, 11, 15), (34, 48, 12, 15), (54, 53, 12, 15),
        (137, 30, 10, 13), (155, 27, 11, 14), (171, 25, 9, 14),
        (137, 49, 11, 15), (157, 48, 12, 15), (174, 47, 8, 15),
    ):
        draw.rectangle((x - 1, y - 1, x + width, y + height), fill=window_frame)
        draw.rectangle((x, y, x + width - 2, y + height - 2), fill=window_glass)
        draw.line((x + width // 2, y, x + width // 2, y + height - 2), fill=window_frame)
        draw.line((x, y + height // 2, x + width - 2, y + height // 2), fill=window_frame)
        draw.line((x - 2, y + height, x + width + 1, y + height), fill=trim)

    balcony = blend((56, 51, 53), (133, 116, 99), daytime)
    draw.rectangle((9, 45, 72, 47), fill=trim)
    for x in range(12, 72, 8):
        draw.rectangle((x, 38, x + 1, 47), fill=balcony)
    draw.rectangle((9, 66, 72, 68), fill=trim)
    for x in range(12, 72, 8):
        draw.rectangle((x, 60, x + 1, 68), fill=balcony)

    # Water tanks and rooftop antenna silhouettes.
    draw.rectangle((29, 6, 40, 15), fill=blend((45, 52, 61), (91, 96, 91), daytime))
    draw.rectangle((31, 4, 38, 6), fill=blend((70, 77, 83), (132, 130, 117), daytime))
    draw.rectangle((150, 7, 160, 15), fill=blend((53, 57, 61), (109, 108, 99), daytime))
    draw.line((24, 22, 24, 3), fill=trim)
    draw.line((21, 9, 27, 9), fill=trim)

    # Perspective street, sidewalks, and distant shopfronts.
    road = blend((54, 56, 61), (123, 118, 107), daytime)
    pavement = blend((79, 74, 72), (158, 145, 126), daytime)
    draw.polygon(((79, 57), (112, 57), (184, 94), (8, 94)), fill=road)
    draw.polygon(((71, 54), (80, 57), (8, 94), (8, 85)), fill=pavement)
    draw.polygon(((112, 57), (121, 54), (184, 85), (184, 94)), fill=pavement)
    draw.line((79, 57, 8, 94), fill=blend((102, 92, 82), (184, 164, 138), daytime))
    draw.line((112, 57, 184, 94), fill=blend((102, 92, 82), (184, 164, 138), daytime))
    for x, y in ((86, 65), (90, 75), (94, 87)):
        draw.rectangle((x, y, x + 2, y + 3), fill=(185, 151, 108))

    # Shop awnings, illuminated doorways and small signboards.
    shop_dark = blend((32, 39, 46), (87, 80, 68), daytime)
    for x, width, color in (
        (9, 24, (157, 104, 76)), (36, 21, (115, 143, 137)),
        (136, 22, (192, 153, 91)), (160, 24, (86, 123, 123)),
    ):
        draw.rectangle((x, 70, x + width, 91), fill=shop_dark)
        draw.rectangle((x - 1, 67, x + width + 1, 72), fill=blend(color, (255, 210, 145), night * 0.55))
        for stripe_x in range(x, x + width, 6):
            draw.rectangle((stripe_x, 67, stripe_x + 2, 72), fill=blend(color, (238, 204, 161), 0.35))
        draw.rectangle((x + 2, 75, x + width - 2, 90), fill=blend(color, (255, 193, 116), night * 0.55))
        draw.rectangle((x + 4, 77, x + width - 4, 88), fill=shop_dark)
        draw.rectangle((x + width // 2, 76, x + width // 2 + 1, 90), fill=blend(color, (205, 177, 130), 0.4))
        draw.line((x + 2, 91, x + width, 91), fill=pavement)

    # Sidewalk details: steps, crates, and street-side lights.
    for x, y in ((26, 87), (44, 84), (148, 87), (171, 85)):
        draw.rectangle((x, y, x + 5, y + 4), fill=trim)
        draw.line((x + 1, y + 1, x + 4, y + 1), fill=blend(trim, (181, 144, 100), 0.5))
    for lamp_x in (31, 160):
        draw.line((lamp_x, 65, lamp_x, 90), fill=trim)
        draw.line((lamp_x - 3, 65, lamp_x + 3, 65), fill=blend((134, 111, 81), (255, 216, 147), night))

    # The reference's wood frame, center stile, and raised blinds.
    frame = (42, 37, 39)
    frame_light = (107, 78, 61)
    draw.rectangle((0, 0, 191, 6), fill=(34, 33, 37))
    draw.rectangle((0, 7, 6, 95), fill=frame)
    draw.rectangle((185, 7, 191, 95), fill=frame)
    draw.rectangle((7, 7, 9, 94), fill=frame_light)
    draw.rectangle((182, 7, 184, 94), fill=frame_light)
    draw.rectangle((94, 7, 98, 95), fill=frame)
    draw.rectangle((94, 7, 95, 95), fill=frame_light)
    draw.rectangle((7, 93, 184, 99), fill=(55, 42, 37))
    draw.rectangle((7, 93, 184, 95), fill=(132, 91, 61))
    for blind_y in (8, 12, 16, 20):
        draw.rectangle((100, blind_y, 181, blind_y + 1), fill=(53, 55, 50))
        draw.rectangle((100, blind_y + 2, 181, blind_y + 2), fill=(173, 178, 150))
    draw.rectangle((100, 22, 181, 23), fill=(57, 56, 49))

    # Cozy desk in the foreground, with lamp, mug, books, and houseplants.
    desktop = blend((58, 43, 39), (120, 78, 52), 0.65)
    draw.rectangle((0, 100, 191, 108), fill=desktop)
    draw.line((0, 100, 191, 100), fill=(164, 111, 70))
    draw.rectangle((0, 109, 191, 127), fill=(39, 39, 44))
    draw.line((0, 110, 191, 110), fill=(94, 65, 49))
    for line_y in (114, 121):
        draw.line((0, line_y, 191, line_y), fill=(51, 48, 49))

    # Warm desk-lamp glow, then the shade, stem, and base.
    draw.rectangle((87, 91, 110, 105), fill=blend(desktop, (158, 91, 49), night * 0.38))
    draw.polygon(((91, 87), (106, 87), (111, 99), (87, 99)), fill=(205, 130, 68))
    draw.polygon(((94, 89), (104, 89), (108, 97), (90, 97)), fill=(255, 207, 123))
    draw.rectangle((98, 99, 100, 108), fill=(112, 72, 48))
    draw.rectangle((92, 107, 106, 109), fill=(75, 51, 42))
    draw.rectangle((90, 109, 108, 111), fill=(132, 80, 48))
    draw.rectangle((92, 108, 106, 108), fill=(220, 151, 78))

    # Mug and a little stack of papers on the left.
    draw.rectangle((72, 94, 81, 103), fill=(174, 164, 145))
    draw.rectangle((74, 92, 79, 94), fill=(210, 197, 173))
    draw.rectangle((81, 96, 84, 100), fill=(119, 111, 101))
    draw.rectangle((52, 104, 80, 107), fill=(100, 70, 57))
    draw.rectangle((55, 101, 77, 103), fill=(167, 138, 112))
    draw.rectangle((58, 99, 76, 100), fill=(91, 66, 56))

    # A potted plant and hanging vine on the left.
    leaf_dark = blend((28, 54, 48), (58, 91, 55), daytime * 0.55)
    for leaf in ((11, 88, 17, 82), (14, 91, 23, 84), (18, 89, 25, 78),
                 (21, 93, 29, 87), (7, 95, 14, 89), (12, 85, 9, 77)):
        draw.line(leaf, fill=leaf_dark, width=3)
    draw.rectangle((10, 94, 23, 103), fill=(90, 52, 43))
    draw.rectangle((8, 93, 25, 95), fill=(137, 83, 56))
    draw.line((19, 8, 19, 40), fill=trim)
    for leaf in ((19, 18, 14, 14), (19, 24, 25, 20), (19, 30, 13, 27),
                 (19, 37, 24, 33), (19, 43, 16, 40)):
        draw.line(leaf, fill=leaf_dark, width=2)
    draw.rectangle((12, 41, 24, 45), fill=(96, 59, 46))

    # A few books and a leafy plant complete the right edge of the desk.
    books = (
        (142, 91, 149, 106, (95, 63, 57)),
        (150, 87, 157, 106, (61, 75, 80)),
        (159, 89, 166, 106, (120, 72, 54)),
        (168, 85, 176, 106, (56, 63, 72)),
        (178, 92, 185, 106, (94, 72, 54)),
    )
    for x1, y1, x2, y2, color in books:
        draw.rectangle((x1, y1, x2, y2), fill=color)
        draw.line((x1 + 2, y1 + 3, x1 + 2, y2 - 2), fill=blend(color, (194, 157, 113), 0.5))
        draw.rectangle((x1 + 1, y2 - 3, x2 - 1, y2 - 2), fill=(176, 147, 110))
    for leaf in ((184, 101, 189, 94), (185, 104, 191, 98), (184, 108, 190, 106)):
        draw.line(leaf, fill=leaf_dark, width=3)
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
