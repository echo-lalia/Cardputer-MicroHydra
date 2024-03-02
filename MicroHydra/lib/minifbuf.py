"""
THIS IS A MODIFIED VERSION OF "st7789py.py"
This version does NOT maintain full compatibility with the original.

MIT License (inherits full License in st7789py.py)
Copyright (c) 2024 Ethan Lacasse
Copyright (c) 2020-2023 Russ Hughes
Copyright (c) 2019 Ivan Belokobylskiy
"""

import time
import math
import framebuf, struct, array


# ST7789 commands
_ST7789_SWRESET = const(b"\x01")
_ST7789_SLPIN = const(b"\x10")
_ST7789_SLPOUT = const(b"\x11")
_ST7789_INVOFF = const(b"\x20")
_ST7789_INVON = const(b"\x21")
_ST7789_CASET = const(b"\x2a")
_ST7789_RASET = const(b"\x2b")
_ST7789_RAMWR = const(b"\x2c")
_ST7789_VSCRDEF = const(b"\x33")
_ST7789_MADCTL = const(b"\x36")
_ST7789_VSCSAD = const(b"\x37")

# MADCTL bits
_ST7789_MADCTL_BGR = const(0x08)

BGR = const(0x08)

# Color definitions
_BLACK = const(0x0000)
_WHITE = const(0xffff)

_ENCODE_POS = const(">HH")


_BIT7 = const(0x80)
_BIT6 = const(0x40)
_BIT5 = const(0x20)
_BIT4 = const(0x10)
_BIT3 = const(0x08)
_BIT2 = const(0x04)
_BIT1 = const(0x02)
_BIT0 = const(0x01)

# fmt: off

# Rotation tables
#   (madctl, width, height, xstart, ystart, needs_swap)[rotation % 4]

_DISPLAY_240x320 = (
    (0x00, 240, 320, 0, 0, False),
    (0x60, 320, 240, 0, 0, False),
    (0xc0, 240, 320, 0, 0, False),
    (0xa0, 320, 240, 0, 0, False))

_DISPLAY_240x240 = (
    (0x00, 240, 240,  0,  0, False),
    (0x60, 240, 240,  0,  0, False),
    (0xc0, 240, 240,  0, 80, False),
    (0xa0, 240, 240, 80,  0, False))

_DISPLAY_135x240 = (
    (0x00, 135, 240, 52, 40, False),
    (0x60, 240, 135, 40, 53, False),
    (0xc0, 135, 240, 53, 40, False),
    (0xa0, 240, 135, 40, 52, False))

_DISPLAY_128x128 = (
    (0x00, 128, 128, 2, 1, False),
    (0x60, 128, 128, 1, 2, False),
    (0xc0, 128, 128, 2, 1, False),
    (0xa0, 128, 128, 1, 2, False))

# Supported displays (physical width, physical height, rotation table)
_SUPPORTED_DISPLAYS = (
    (240, 320, _DISPLAY_240x320),
    (240, 240, _DISPLAY_240x240),
    (135, 240, _DISPLAY_135x240),
    (128, 128, _DISPLAY_128x128))

# init tuple format (b'command', b'data', delay_ms)
_ST7789_INIT_CMDS = (
    ( b'\x11', b'\x00', 120),               # Exit sleep mode
    ( b'\x13', b'\x00', 0),                 # Turn on the display
    ( b'\xb6', b'\x0a\x82', 0),             # Set display function control
    ( b'\x3a', b'\x55', 10),                # Set pixel format to 16 bits per pixel (RGB565)
    ( b'\xb2', b'\x0c\x0c\x00\x33\x33', 0), # Set porch control
    ( b'\xb7', b'\x35', 0),                 # Set gate control
    ( b'\xbb', b'\x28', 0),                 # Set VCOMS setting
    ( b'\xc0', b'\x0c', 0),                 # Set power control 1
    ( b'\xc2', b'\x01\xff', 0),             # Set power control 2
    ( b'\xc3', b'\x10', 0),                 # Set power control 3
    ( b'\xc4', b'\x20', 0),                 # Set power control 4
    ( b'\xc6', b'\x0f', 0),                 # Set VCOM control 1
    ( b'\xd0', b'\xa4\xa1', 0),             # Set power control A
                                            # Set gamma curve positive polarity
    ( b'\xe0', b'\xd0\x00\x02\x07\x0a\x28\x32\x44\x42\x06\x0e\x12\x14\x17', 0),
                                            # Set gamma curve negative polarity
    ( b'\xe1', b'\xd0\x00\x02\x07\x0a\x28\x31\x54\x47\x0e\x1c\x17\x1b\x1e', 0),
    ( b'\x21', b'\x00', 0),                 # Enable display inversion
    ( b'\x29', b'\x00', 120)                # Turn on the display
)

# fmt: on


def color565(red, green=None, blue=None):
    if isinstance(red, (tuple, list)):
        red, green, blue = red[:3]
    return (red & 0xF8) << 0x08 | (green & 0xFC) << 0x03 | blue >> 0x03

def swap_bytes(color):
    return ((color & 0xff) << 0x08) + (color >> 0x08)

class ST7789:
    def __init__(
        self,
        spi,
        width,
        height,
        reset=None,
        dc=None,
        cs=None,
        backlight=None,
        rotation=0,
        color_order=BGR,
        custom_framebufs=None,
    ):
        """
        Initialize display.
        """
        self.rotations = self._find_rotations(width, height)

        # trying to avoid extra object creation??
        self.fbufs = tuple(
            framebuf.FrameBuffer(buffer, buf_width, buf_height, framebuf.RGB565)
            for buffer, buf_x,buf_y,buf_width,buf_height
            in custom_framebufs
            )
        self.fbuf_pos = tuple((buf_x, buf_y) for buffer,buf_x,buf_y,buf_width,buf_height in custom_framebufs)
        self.fbuf_shape = tuple((buf_width, buf_height) for buffer,buf_x,buf_y,buf_width,buf_height in custom_framebufs)
        
        self.xstart = 0
        self.ystart = 0
        self.spi = spi
        self.reset = reset
        self.dc = dc
        self.cs = cs
        self.backlight = backlight
        self._rotation = rotation % 4
        self.color_order = color_order
        self.init_cmds = _ST7789_INIT_CMDS
        self.hard_reset()
        # yes, twice, once is not always enough
        self.init(self.init_cmds)
        self.init(self.init_cmds)
        self.rotation(self._rotation)
        self.needs_swap = True
        for i in range(len(self.fbufs)):
            #self.fill(0, buf_idx=i)
            self.show(buf_idx=i)

        if backlight is not None:
            backlight.value(1)

    def _find_rotations(self, width, height):
        for display in _SUPPORTED_DISPLAYS:
            if display[0] == width and display[1] == height:
                return display[2]
        return None

    def init(self, commands):
        for command, data, delay in commands:
            self._write(command, data)
            time.sleep_ms(delay)

    def _write(self, command=None, data=None):
        if self.cs:
            self.cs.off()
        if command is not None:
            self.dc.off()
            self.spi.write(command)
        if data is not None:
            self.dc.on()
            self.spi.write(data)
            if self.cs:
                self.cs.on()

    def hard_reset(self):
        if self.cs:
            self.cs.off()
        if self.reset:
            self.reset.on()
        time.sleep_ms(10)
        if self.reset:
            self.reset.off()
        time.sleep_ms(10)
        if self.reset:
            self.reset.on()
        time.sleep_ms(120)
        if self.cs:
            self.cs.on()

    def soft_reset(self):
        self._write(_ST7789_SWRESET)
        time.sleep_ms(150)

    def sleep_mode(self, value):
        if value:
            self._write(_ST7789_SLPIN)
        else:
            self._write(_ST7789_SLPOUT)

    def inversion_mode(self, value):
        if value:
            self._write(_ST7789_INVON)
        else:
            self._write(_ST7789_INVOFF)

    def rotation(self, rotation):
        rotation %= len(self.rotations)
        self._rotation = rotation
        (
            madctl,
            self.width,
            self.height,
            self.xstart,
            self.ystart,
            self.needs_swap,
        ) = self.rotations[rotation]

        if self.color_order == BGR:
            madctl |= _ST7789_MADCTL_BGR
        else:
            madctl &= ~_ST7789_MADCTL_BGR

        self._write(_ST7789_MADCTL, bytes([madctl]))

    def _set_window(self, x0, y0, x1, y1):
        if x0 <= x1 <= self.width and y0 <= y1 <= self.height:
            self._write(
                _ST7789_CASET,
                struct.pack(_ENCODE_POS, x0 + self.xstart, x1 + self.xstart),
            )
            self._write(
                _ST7789_RASET,
                struct.pack(_ENCODE_POS, y0 + self.ystart, y1 + self.ystart),
            )
            self._write(_ST7789_RAMWR)

    def vline(self, x, y, length, color, buf_idx=0):
        if self.needs_swap:
            color = swap_bytes(color)
        
        # convert global coordinate to fbuf-specific coordinate
        x -= self.fbuf_pos[buf_idx][0]
        y -= self.fbuf_pos[buf_idx][1]
        self.fbufs[buf_idx].vline(x, y, length, color)

    def hline(self, x, y, length, color, buf_idx=0):
        if self.needs_swap:
            color = swap_bytes(color)
        # convert global coordinate to fbuf-specific coordinate
        x -= self.fbuf_pos[buf_idx][0]
        y -= self.fbuf_pos[buf_idx][1]
        self.fbufs[buf_idx].hline(x, y, length, color)

    def pixel(self, x, y, color, buf_idx=0):
        if self.needs_swap:
            color = swap_bytes(color)
        # convert global coordinate to fbuf-specific coordinate
        x -= self.fbuf_pos[buf_idx][0]
        y -= self.fbuf_pos[buf_idx][1]
        self.fbufs[buf_idx].pixel(x,y,color)
        
        
    def show(self, buf_idx=0):
        self._set_window(
            self.fbuf_pos[buf_idx][0],
            self.fbuf_pos[buf_idx][1],
            self.fbuf_pos[buf_idx][0] + self.fbuf_shape[buf_idx][0] - 1,
            self.fbuf_pos[buf_idx][1] + self.fbuf_shape[buf_idx][1] - 1
            )
        self._write(None, self.fbufs[buf_idx])
        
        
    def blit_buffer(self, buffer, x, y, width, height, key=-1, palette=None, buf_idx=0):
        # convert global coordinate to fbuf-specific coordinate
        x -= self.fbuf_pos[buf_idx][0]
        y -= self.fbuf_pos[buf_idx][1]
        self.fbufs[buf_idx].blit(framebuf.FrameBuffer(buffer,width, height, framebuf.RGB565), x,y,key,palette)
        
    def blit_framebuf(self, fbuf, x, y, key=-1, palette=None, buf_idx=0):
        # convert global coordinate to fbuf-specific coordinate
        x -= self.fbuf_pos[buf_idx][0]
        y -= self.fbuf_pos[buf_idx][1]
        self.fbufs[buf_idx].blit(fbuf, x,y,key,palette)

    def rect(self, x, y, w, h, color, fill=False, buf_idx=0):
        if self.needs_swap:
            color = swap_bytes(color)
        # convert global coordinate to fbuf-specific coordinate
        x -= self.fbuf_pos[buf_idx][0]
        y -= self.fbuf_pos[buf_idx][1]
        self.fbufs[buf_idx].rect(x,y,w,h,color,fill)
        
    def ellipse(self, x, y, xr, yr, color, fill=False, buf_idx=0):
        if self.needs_swap:
            color = swap_bytes(color)
        # convert global coordinate to fbuf-specific coordinate
        x -= self.fbuf_pos[buf_idx][0]
        y -= self.fbuf_pos[buf_idx][1]
        self.fbufs[buf_idx].ellipse(x,y,xr,yr,color,fill)

    def fill(self, color, buf_idx=0):
        if self.needs_swap:
            color = swap_bytes(color)
        self.fbufs[buf_idx].fill(color)

    def line(self, x0, y0, x1, y1, color, buf_idx=0):
        x0 = x0 - self.fbuf_pos[buf_idx][0]
        y0 = y0 - self.fbuf_pos[buf_idx][1]
        x1 = x1 - self.fbuf_pos[buf_idx][0]
        y1 = y1 - self.fbuf_pos[buf_idx][1]
        self.fbufs[buf_idx].line(x0, y0, x1, y1, color)

    def vscrdef(self, tfa, vsa, bfa):
        self._write(_ST7789_VSCRDEF, struct.pack(">HHH", tfa, vsa, bfa))

    def vscsad(self, vssa):
        self._write(_ST7789_VSCSAD, struct.pack(">H", vssa))

    def scroll(self,xstep,ystep, buf_idx=0):
        self.fbufs[buf_idx].scroll(xstep,ystep)

    @micropython.viper
    @staticmethod
    def _pack8(glyphs, idx: uint, fg_color: uint, bg_color: uint):
        buffer = bytearray(128)
        bitmap = ptr16(buffer)
        glyph = ptr8(glyphs)

        for i in range(0, 64, 8):
            byte = glyph[idx]
            bitmap[i] = fg_color if byte & _BIT7 else bg_color
            bitmap[i + 1] = fg_color if byte & _BIT6 else bg_color
            bitmap[i + 2] = fg_color if byte & _BIT5 else bg_color
            bitmap[i + 3] = fg_color if byte & _BIT4 else bg_color
            bitmap[i + 4] = fg_color if byte & _BIT3 else bg_color
            bitmap[i + 5] = fg_color if byte & _BIT2 else bg_color
            bitmap[i + 6] = fg_color if byte & _BIT1 else bg_color
            bitmap[i + 7] = fg_color if byte & _BIT0 else bg_color
            idx += 1

        return buffer

    @micropython.viper
    @staticmethod
    def _pack16(glyphs, idx: uint, fg_color: uint, bg_color: uint):

        buffer = bytearray(256)
        bitmap = ptr16(buffer)
        glyph = ptr8(glyphs)

        for i in range(0, 128, 16):
            byte = glyph[idx]

            bitmap[i] = fg_color if byte & _BIT7 else bg_color
            bitmap[i + 1] = fg_color if byte & _BIT6 else bg_color
            bitmap[i + 2] = fg_color if byte & _BIT5 else bg_color
            bitmap[i + 3] = fg_color if byte & _BIT4 else bg_color
            bitmap[i + 4] = fg_color if byte & _BIT3 else bg_color
            bitmap[i + 5] = fg_color if byte & _BIT2 else bg_color
            bitmap[i + 6] = fg_color if byte & _BIT1 else bg_color
            bitmap[i + 7] = fg_color if byte & _BIT0 else bg_color
            idx += 1

            byte = glyph[idx]
            bitmap[i + 8] = fg_color if byte & _BIT7 else bg_color
            bitmap[i + 9] = fg_color if byte & _BIT6 else bg_color
            bitmap[i + 10] = fg_color if byte & _BIT5 else bg_color
            bitmap[i + 11] = fg_color if byte & _BIT4 else bg_color
            bitmap[i + 12] = fg_color if byte & _BIT3 else bg_color
            bitmap[i + 13] = fg_color if byte & _BIT2 else bg_color
            bitmap[i + 14] = fg_color if byte & _BIT1 else bg_color
            bitmap[i + 15] = fg_color if byte & _BIT0 else bg_color
            idx += 1

        return buffer

    def _text8(self, font, text, x0, y0, fg_color=_WHITE, buf_idx=0):
        
        if fg_color == 0:
            bg_color = 1
        else:
            bg_color = 0
            
        for char in text:
            ch = ord(char)
            if (
                font.FIRST <= ch < font.LAST
                and x0 + font.WIDTH <= self.width
                and y0 + font.HEIGHT <= self.height
            ):
                if font.HEIGHT == 8:
                    passes = 1
                    size = 8
                    each = 0
                else:
                    passes = 2
                    size = 16
                    each = 8

                for line in range(passes):
                    idx = (ch - font.FIRST) * size + (each * line)
                    buffer = self._pack8(font.FONT, idx, fg_color, bg_color)
                    self.blit_buffer(buffer, x0, y0 + 8 * line, 8, 8,key=bg_color, buf_idx=buf_idx)

                x0 += 8

    def _text16(self, font, text, x0, y0, fg_color=_WHITE, buf_idx=0):
        if fg_color == 0:
            bg_color = 1
        else:
            bg_color = 0
        for char in text:
            ch = ord(char)
            if (
                font.FIRST <= ch < font.LAST
                and x0 + font.WIDTH <= self.width
                and y0 + font.HEIGHT <= self.height
            ):
                each = 16
                if font.HEIGHT == 16:
                    passes = 2
                    size = 32
                else:
                    passes = 4
                    size = 64

                for line in range(passes):
                    idx = (ch - font.FIRST) * size + (each * line)
                    buffer = self._pack16(font.FONT, idx, fg_color, bg_color)
                    self.blit_buffer(buffer, x0, y0 + 8 * line, 16, 8,key=bg_color, buf_idx=buf_idx)
            x0 += 16

    def text(self, text, x, y, color=_WHITE, buf_idx=0):
        if self.needs_swap:
            color = swap_bytes(color)
        # convert global coordinate to fbuf-specific coordinate
        x -= self.fbuf_pos[buf_idx][0]
        y -= self.fbuf_pos[buf_idx][1]
        self.fbufs[buf_idx].text(text, x, y, color)

    def bitmap_text(self, font, text, x0, y0, color=_WHITE, buf_idx=0):
        if self.needs_swap:
            color=swap_bytes(color)

        if font.WIDTH == 8:
            self._text8(font, text, x0, y0, color, buf_idx=buf_idx)
        else:
            self._text16(font, text, x0, y0, color, buf_idx=buf_idx)

    def bitmap(self, bitmap, x, y, index=0, key=-1, buf_idx=0):
        width = bitmap.WIDTH
        height = bitmap.HEIGHT
        to_col = x + width - 1
        to_row = y + height - 1
        if self.width <= to_col or self.height <= to_row:
            return

        bitmap_size = height * width
        buffer_len = bitmap_size * 2
        bpp = bitmap.BPP
        bs_bit = bpp * bitmap_size * index  # if index > 0 else 0
        palette = bitmap.PALETTE
        
        #swap colors if needed:
        if self.needs_swap:
            for i in range(0,len(palette)):
                palette[i] = swap_bytes(palette[i])
        
        buffer = bytearray(buffer_len)

        for i in range(0, buffer_len, 2):
            color_index = 0
            for _ in range(bpp):
                color_index = (color_index << 1) | (
                    (bitmap.BITMAP[bs_bit >> 3] >> (7 - (bs_bit & 7))) & 1
                )
                bs_bit += 1

            color = palette[color_index]

            buffer[i] = color & 0xFF
            buffer[i + 1] = color >> 8
        
        self.blit_buffer(buffer,x,y,width,height,key=key,buf_idx=buf_idx)

    def bitmap_icons(self, bitmap_module, bitmap, color, x, y, invert_colors=False, buf_idx=0):
        width = bitmap_module.WIDTH
        height = bitmap_module.HEIGHT
        to_col = x + width - 1
        to_row = y + height - 1
        if self.width <= to_col or self.height <= to_row:
            return

        bitmap_size = height * width
        buffer_len = bitmap_size * 2
        bpp = bitmap_module.BPP
        bs_bit = 0
        needs_swap = self.needs_swap
        buffer = bytearray(buffer_len)
        
        if self.needs_swap:
            color = swap_bytes(color)
            
        #prevent bg color from being invisible
        if color == 0:
            palette = (65535, color)
        else:
            palette = (0, color)
        
        for i in range(0, buffer_len, 2):
            color_index = 0
            for _ in range(bpp):
                color_index = (color_index << 1) | (
                    (bitmap[bs_bit >> 3] >> (7 - (bs_bit & 7))) & 1
                )
                bs_bit += 1

            color = palette[color_index]

            buffer[i] = color & 0xFF
            buffer[i + 1] = color >> 8

        
        self.blit_buffer(buffer,x,y,width,height,key=palette[0], buf_idx=buf_idx)
                

    def write(self, font, string, x, y, fg=_WHITE, buf_idx=0):
        # convert global coordinate to fbuf-specific coordinate
        x -= self.fbuf_pos[buf_idx][0]
        y -= self.fbuf_pos[buf_idx][1]
        if self.needs_swap:
            fg = swap_bytes(fg)
        fbuf=self.fbufs[buf_idx]
        for character in string:
            try:
                char_index = font.MAP.index(character)
                offset = char_index * font.OFFSET_WIDTH
                bs_bit = font.OFFSETS[offset]
                
                if font.OFFSET_WIDTH > 2:
                    bs_bit = (bs_bit << 8) + font.OFFSETS[offset + 2]
                elif font.OFFSET_WIDTH > 1:
                    bs_bit = (bs_bit << 8) + font.OFFSETS[offset + 1]
                
                char_width = font.WIDTHS[char_index]
                buffer_needed = char_width * font.HEIGHT
                
                for i in range(0, buffer_needed):
                    px_x = x + ((i) % char_width)
                    px_y = y + ((i) // char_width)
                    if font.BITMAPS[bs_bit // 8] & 1 << (7 - (bs_bit % 8)) > 0:
                        fbuf.pixel(px_x,px_y,fg)
                    
                    bs_bit += 1

                x += char_width

            except ValueError:
                pass

    def write_width(self, font, string):
        width = 0
        for character in string:
            try:
                char_index = font.MAP.index(character)
                width += font.WIDTHS[char_index]
            except ValueError:
                pass

        return width
    
    def polygon(self,points,x,y,color,fill=False,buf_idx=0):
        if self.needs_swap:
            color = swap_bytes(color)
        # convert global coordinate to fbuf-specific coordinate
        x -= self.fbuf_pos[buf_idx][0]
        y -= self.fbuf_pos[buf_idx][1]
        self.fbufs[buf_idx].poly(x,y,points,color,fill)

