"""Convert a single image to a module compatible with MicroHydra.

Convert an image file to a python module for use with the bitmap method. Use redirection to save the
output to a file. The image is converted to a bitmap using the number of bits per pixel you specify.
The bitmap is saved as a python module that can be imported and used with the bitmap method.



This script was originally written by Russ Hughes as part of the 'st7789py_mpy' repo.



MIT License

Copyright (c) 2020-2023 Russ Hughes

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import sys
import argparse
from PIL import Image


def rgb_to_color565(r: int, g: int, b: int) -> int:
    """Convert RGB color to the 16-bit color format (565).

    Args:
        r (int): Red component of the RGB color (0-255).
        g (int): Green component of the RGB color (0-255).
        b (int): Blue component of the RGB color (0-255).

    Returns:
        int: Converted color value in the 16-bit color format (565).
    """
    r = ((r * 31) // (255))
    g = ((g * 63) // (255))
    b = ((b * 31) // (255))
    return (r << 11) | (g << 5) | b


def convert_to_bitmap(image_file: str, bits_requested: int):
    """Convert image file to python module for use with bitmap method.

    Args:
        image_file (str): Name of file containing image to convert.
        bits_requested (int): The number of bits to use per pixel (1..8).
    """

    colors_requested = 1 << bits_requested
    img = Image.open(image_file).convert("RGB")
    img = img.convert("P", palette=Image.Palette.ADAPTIVE, colors=colors_requested)
    palette = img.getpalette()
    palette_colors = len(palette) // 3
    actual_colors = min(palette_colors, colors_requested)
    bits_required = actual_colors.bit_length()
    if bits_required < bits_requested:
        print(
            f"\nNOTE: Quantization reduced colors to {palette_colors} from the {bits_requested} "
            f"requested, reconverting using {bits_required} bit per pixel could save memory.\n",
            file=sys.stderr,
        )

    colors = [
        f"{rgb_to_color565(palette[color * 3], palette[color * 3 + 1], palette[color * 3 + 2]):04x}"
        for color in range(actual_colors)
    ]

    image_bitstring = "".join(
        "".join(
            "1" if (img.getpixel((x, y)) & (1 << bit - 1)) else "0"
            for bit in range(bits_required, 0, -1)
        )
        for y in range(img.height)
        for x in range(img.width)
    )

    bitmap_bits = len(image_bitstring)

    print(f"HEIGHT = {img.height}")
    print(f"WIDTH = {img.width}")
    print(f"COLORS = {actual_colors}")
    print(f"BITS = {bitmap_bits}")
    print(f"BPP = {bits_required}")
    print("PALETTE = [", end="")

    for i, rgb in enumerate(colors):
        if i > 0:
            print(",", end="")
        print(f"0x{rgb}", end="")

    print("]")

    print("_bitmap =\\\nb'", end="")

    for i in range(0, bitmap_bits, 8):
        if i and i % (16 * 8) == 0:
            print("'\\\nb'", end="")
        value = image_bitstring[i : i + 8]
        color = int(value, 2)
        print(f"\\x{color:02x}", end="")

    print("'\nBITMAP = memoryview(_bitmap)")


def main():
    """Convert image file to python module for use with bitmap method."""

    parser = argparse.ArgumentParser(
        description="Convert image file to python module for use with bitmap method.",
    )

    parser.add_argument("image_file", help="Name of file containing image to convert")

    parser.add_argument(
        "bits_per_pixel",
        type=int,
        choices=range(1, 9),
        default=1,
        metavar="bits_per_pixel",
        help="The number of bits to use per pixel (1..8)",
    )

    args = parser.parse_args()
    bits = args.bits_per_pixel
    convert_to_bitmap(args.image_file, bits)


if __name__ == "__main__":
    main()
