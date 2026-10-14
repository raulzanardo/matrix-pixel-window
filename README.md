# Pixel Window

A 192×128 pixel-art scene of a wooden window looking out over hills and grass.
The sky transitions through a repeating day/night cycle: the sun moves across
the daytime sky, while a crescent moon and twinkling stars appear at night.

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

The full day/night cycle takes two minutes by default. For example:

```sh
sudo python3 pixel_window.py --cycle-seconds 300 --fps 15
```

## Save a preview

Save one frame as a PNG without connecting to the matrix:

```sh
python3 pixel_window.py --preview window.png --phase 0.35
```

`--phase` ranges from `0` (midnight) to just under `1` (the next midnight).
The Python Pillow package is required to render or save the preview.
