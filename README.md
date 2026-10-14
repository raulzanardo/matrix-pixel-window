# Pixel Window

A 192×128 pixel-art scene of a wooden window looking out over a city skyline,
apartment blocks, street lamps, and traffic. The sky follows the Raspberry Pi's
local clock: the sun crosses the sky from 06:00 to 18:00, and the moon and
twinkling stars appear at night.

## Run on the matrix

Install/build the Python bindings for
[rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix) on the
Raspberry Pi, then run:

```sh
sudo python3 pixel_window.py
```

The default `config.ini` configures three 64×64 panels in a chain and two
parallel rows, for an effective 192×128 display. Adjust brightness, GPIO
slowdown, panel type, and other hardware options in that file.

The scene uses the Pi's system time and local timezone, so configure the Pi's
clock and timezone correctly. Check them with:

```sh
timedatectl
```

## Save a preview

Save a still PNG showing the current local time, without connecting to the
matrix:

```sh
python3 pixel_window.py --preview window.png
```

The Python Pillow package is required to render or save the preview.
