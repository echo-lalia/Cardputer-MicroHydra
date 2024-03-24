import math, array
from lib import microhydra as mh

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CONSTANT ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_DISPLAY_WIDTH = const(240)
_DISPLAY_HEIGHT = const(135)

_DISPLAY_WIDTH_CENTER = const(_DISPLAY_WIDTH//2)
_DISPLAY_CENTER_LEFT = const(_DISPLAY_WIDTH_CENTER//2)
_DISPLAY_CENTER_RIGHT = const(_DISPLAY_WIDTH_CENTER+_DISPLAY_CENTER_LEFT)

# scrollbar
_SCROLLBAR_WIDTH = const(2)
_SCROLLBAR_X = const(_DISPLAY_WIDTH-_SCROLLBAR_WIDTH)
_SCROLLBAR_BUFFER_WIDTH = const(4)
_SCROLLBAR_BUFFER_X = const(_SCROLLBAR_X-_SCROLLBAR_BUFFER_WIDTH)

_FONT_HEIGHT = const(32) # big font height
_FONT_WIDTH = const(16) # big font width
_FONT_HEIGHT_HALF = const(_FONT_HEIGHT//2)
_FONT_WIDTH_HALF = const(_FONT_WIDTH//2)

_SMALL_FONT_HEIGHT = const(8) # small font height
_SMALL_FONT_HEIGHT_HALF = const(_SMALL_FONT_HEIGHT//2)
_SMALL_FONT_WIDTH = const(8) # small font width
_SMALL_FONT_WIDTH_HALF = const(_SMALL_FONT_WIDTH//2)


_PER_PAGE = const(_DISPLAY_HEIGHT//_FONT_HEIGHT)
_Y_PADDING = const( (_DISPLAY_HEIGHT - (_PER_PAGE*_FONT_HEIGHT)) // 2)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GLOBAL ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# global config will provide default stylings
DISPLAY = None
CONFIG = None
FONT = None

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ MENU ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class Menu:
    """
    args:
    - display_fbuf (ST7789): st7789fbuf ST7789 object
    - font (module): bitmap font module
    - sound (M5Sound): M5Sound M5Sound object
    - per_page (int): menu items per page
    - y_padding (int): y padding on first menu item
    """
    def __init__(self,
                 display_fbuf,
                 config = None,
                 font = None,
                 sound = None,
                 per_page:int = _PER_PAGE,
                 y_padding:int = _Y_PADDING
                 ):
        # init global font and config
        global FONT, CONFIG, DISPLAY
        
        if font:
            FONT = font
        else:
            from font import vga2_16x32
            FONT = vga2_16x32
            
        if config:
            CONFIG = config
        else:
            from lib import mhconfig
            CONFIG = mhconfig.Config()
        
        DISPLAY = display_fbuf
        self.items = []
        self.cursor_index = 0
        self.prev_cursor_index = 0
        self.setting_screen_index = 0
        self.per_page = per_page
        self.y_padding = y_padding
        self.in_submenu = False
        
        self.sound = sound
    
    def append(self, item):
        self.items.append(item)

    def display_menu(self):
        if self.cursor_index >= self.setting_screen_index + self.per_page:
            self.setting_screen_index += self.cursor_index - (self.setting_screen_index + (self.per_page - 1))

        elif self.cursor_index < self.setting_screen_index:
            self.setting_screen_index -= self.setting_screen_index - self.cursor_index
        
        DISPLAY.fill(CONFIG['bg_color'])
        
        visible_items = self.items[self.setting_screen_index:self.setting_screen_index+self.per_page]
        
        for i in range(self.setting_screen_index, self.setting_screen_index + self.per_page):
            y = self.y_padding + (i - self.setting_screen_index) * FONT.HEIGHT
            if i <= len(self.items) - 1:
                if i == self.cursor_index:
                    self.items[i].selected = 1
                    self.items[i].y_pos = y
                    self.items[i].draw()
                else:
                    self.items[i].selected = 0
                    self.items[i].y_pos = y
                    self.items[i].draw()
        self.update_scroll_bar()

    def update_scroll_bar(self):
        max_screen_index = len(self.items) - self.per_page
        scrollbar_height = _DISPLAY_HEIGHT // max_screen_index
        scrollbar_position = math.floor((_DISPLAY_HEIGHT - scrollbar_height) * (self.setting_screen_index / max_screen_index))
        
        DISPLAY.fill_rect(_SCROLLBAR_BUFFER_X, 0, _SCROLLBAR_BUFFER_WIDTH, _DISPLAY_HEIGHT, CONFIG.palette[1])
        DISPLAY.fill_rect(_SCROLLBAR_X, 0, _SCROLLBAR_WIDTH, _DISPLAY_HEIGHT, CONFIG.palette[0])
        DISPLAY.fill_rect(_SCROLLBAR_X, scrollbar_position, _SCROLLBAR_WIDTH, scrollbar_height, CONFIG.palette[3])

    def handle_input(self, key):
        if self.in_submenu:
            self.items[self.cursor_index].handle_input(key)
        
        elif key == 'UP' or key == ';':
            self.cursor_index = (self.cursor_index - 1) % len(self.items)
            
            self.display_menu()

        elif key == 'DOWN' or key == '.':
            self.cursor_index = (self.cursor_index + 1) % len(self.items)
            
            self.display_menu()
        
        elif key == 'GO' or key == 'ENT':
            return (self.items[self.cursor_index].handle_input("GO"))


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Menu Items: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# right text
_RIGHT_TEXT_Y = const((_FONT_HEIGHT-_SMALL_FONT_HEIGHT) // 2)
_RIGHT_TEXT_X_OFFSET = const(40)
_RIGHT_TEXT_X = const(_DISPLAY_WIDTH - _RIGHT_TEXT_X_OFFSET)
# left text
_LEFT_TEXT_SELECTED_X = const(-4)
_LEFT_TEXT_UNSELECTED_X = const(10)

class MenuItem:
    """
    Parent class for HydraMenu Menu Items.
    """
    def __init__(
        self,
        menu:Menu,
        text:str,
        value:bool|str|int,
        selected:bool=False,
        callback:callable|None=None
        ):
        self.menu = menu
        self.text = text
        self.value = value
        self.callback = callback
        
    def __repr__(self):
        return repr(self.value)
        
    def draw(self):
        draw_right_text(repr(self), self.y_pos, self.selected)
        draw_left_text(self.text, self.y_pos, self.selected)
        DISPLAY.hline(0, self.y_pos, _DISPLAY_WIDTH, CONFIG.palette[2])
        DISPLAY.hline(0, self.y_pos+_FONT_HEIGHT-1, _DISPLAY_WIDTH, CONFIG.palette[0])
    
    def handle_input(self, key):
        pass

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Bool Item ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class BoolItem(MenuItem):
    """Item for creating boolean options"""
    def __init__(
        self,
        menu:Menu,
        text:str,
        value:bool,
        selected:bool=False,
        callback:callable|None=None
        ):
        super().__init__(menu=menu, text=text, value=value, selected=selected, callback=callback)
        
    def handle_input(self, key):
        if (key == "GO" or key == "ENT"):
            self.value = not self.value
            
            self.draw()
            if self.callback != None:
                self.callback(self, self.value)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Do Item ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class DoItem(MenuItem):
    """Item for creating 'action' buttons"""
    def __init__(
        self,
        menu:Menu,
        text:str,
        value:None=None,
        selected:bool=False,
        callback:callable|None=None
        ):
        super().__init__(menu=menu, text=text, value=None, selected=selected, callback=callback)
        
    def draw(self):
        if self.selected:
            TEXT = f"< {self.text} >"
            DISPLAY.bitmap_text(FONT, TEXT, _DISPLAY_WIDTH_CENTER - get_text_center(TEXT, FONT), self.y_pos, CONFIG['ui_color'])
        else:
            DISPLAY.bitmap_text(FONT, self.text, _DISPLAY_WIDTH_CENTER - get_text_center(self.text, FONT), self.y_pos, CONFIG.palette[4])
        DISPLAY.hline(0, self.y_pos, _DISPLAY_WIDTH, CONFIG.palette[2])
        DISPLAY.hline(0, self.y_pos+_FONT_HEIGHT-1, _DISPLAY_WIDTH, CONFIG.palette[0])
        
    def handle_input(self, key):
        if self.callback:
            self.callback(self)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ RGB Item ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_SELECTION_ARROW_Y = const(94)
_RGB_HINT_Y = const(54)
_RGB_INPUT_Y = const(_RGB_HINT_Y+_SMALL_FONT_HEIGHT)

class RGBItem(MenuItem):
    """Item for creating RGB565 options"""
    def __init__(
        self,
        menu:Menu,
        text:str,
        value:int,
        selected:bool=False,
        callback:callable|None=None
        ):
        super().__init__(menu=menu, text=text, value=value, selected=selected, callback=callback)
        self.in_item = False
        self.cursor_index = 0
    
    def __repr__(self):
        return f"{self.value[0]},{self.value[1]},{self.value[2]}"
    
    def handle_input(self, key):
        _MAX_RANGE = const((32, 64, 32))
        
        self.menu.in_submenu = True
        if (key == 'RIGHT' or key == "/"):
            self.cursor_index = (self.cursor_index + 1) % 3
                
        elif (key == "LEFT" or key == ","):
            self.cursor_index = (self.cursor_index - 1) % 3
                
        elif (key == "UP" or key == ";"):
            self.value[self.cursor_index] += 1
            self.value[self.cursor_index] %= _MAX_RANGE[self.cursor_index]
                
        elif (key == "DOWN" or key == "."):
            self.value[self.cursor_index] -= 1
            self.value[self.cursor_index] %= _MAX_RANGE[self.cursor_index]
                
        elif (key == "GO" or key == "ENT") and self.in_item != False:
            self.menu.in_submenu = False
            self.in_item = False
            self.menu.display_menu()
            if self.callback != None:
                self.callback(self, mh.combine_color565(self.value[0],self.value[1],self.value[2]))
            return
            
        self.in_item = True
        self.draw_rgb_win()
        
    def draw_rgb_win(self):
        _RGB = const((63488, 2016, 31))
        _CENTERED_X = const((_DISPLAY_CENTER_LEFT, _DISPLAY_WIDTH_CENTER, _DISPLAY_CENTER_RIGHT))
        
        win = PopUpWin(self.text)
        win.draw()
        
        rgb_text = (f"R{math.floor(self.value[0]*8.225806)}",
                    f"G{math.floor(self.value[1]*4.04762)}",
                    f"B{math.floor(self.value[2]*8.225806)}")
        for i, item in enumerate(self.value):
            x = _CENTERED_X[i]
            if i == self.cursor_index:
                #DISPLAY.bitmap_text(FONT, str(item), x, y, 65535)
                draw_centered_text(str(item), x, _RGB_INPUT_Y, CONFIG.palette[6], font=FONT)
            else:
                #DISPLAY.bitmap_text(FONT, str(item), x, y, CONFIG.palette[5])
                draw_centered_text(str(item), x, _RGB_INPUT_Y, CONFIG.palette[5], font=FONT)
            draw_centered_text(str(rgb_text[i]), x, _RGB_HINT_Y, _RGB[i])
            
        # draw pointer
        draw_select_arrow(
            _CENTERED_X[self.cursor_index], _SELECTION_ARROW_Y,
            mh.combine_color565(self.value[0],self.value[1],self.value[2])
            )

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Int Item ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_INT_SELECTOR_Y = const(72)
_INT_ARROW_UP_Y = const(_INT_SELECTOR_Y-12)
_INT_ARROW_DOWN_Y = const(_INT_SELECTOR_Y+10+_FONT_HEIGHT)

class IntItem(MenuItem):
    """Item for creating Integer selection options"""
    def __init__(
        self,
        menu:Menu,
        text:str,
        value:int,
        selected:bool=False,
        callback:callable|None=None,
        min_int:int=0,
        max_int:int=10
        ):
        super().__init__(menu=menu, text=text, value=value, selected=selected, callback=callback)
        self.in_item = False
        self.min_int = min_int
        self.max_int = max_int
        
    def handle_input(self, key):
        self.menu.in_submenu = True
        
        if (key == "UP" or key == ";"):
            self.value += 1
            if self.value > self.max_int:
                self.value = self.min_int
                
        elif (key == "DOWN" or key == "."):
            self.value -= 1
            if self.value < self.min_int:
                self.value = self.max_int
                
        elif (key == "GO" or key == "ENT") and self.in_item:
            self.menu.in_submenu = False
            self.in_item = False
            self.menu.display_menu()
            if self.callback != None:
                self.callback(self, self.value)
            return
            
        self.in_item = True
        self.draw_win()

    def draw_win(self):
        win = PopUpWin(self.text)
        win.draw()
        draw_small_arrow(_DISPLAY_WIDTH_CENTER, _INT_ARROW_UP_Y, CONFIG.palette[3])
        draw_small_arrow(_DISPLAY_WIDTH_CENTER, _INT_ARROW_DOWN_Y, CONFIG.palette[3], direction=-1)
        
        draw_centered_text(str(self.value), _DISPLAY_WIDTH_CENTER, _INT_SELECTOR_Y, CONFIG['ui_color'], font=FONT)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Write Item ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class WriteItem(MenuItem):
    """Item for creating text entry options"""
    def __init__(
        self,
        menu:Menu,
        text:str,
        value:int,
        selected:bool=False,
        callback:callable|None=None,
        hide:bool=False
        ):
        super().__init__(menu=menu, text=text, value=value, selected=selected, callback=callback)
        self.in_item = False
        self.hide = hide
    
    def __repr__(self):
        if self.hide:
            if self.value:
                return '*****'
            else:
                return ''
        else:
            return repr(self.value)
    
    def draw_win(self):
        win = PopUpWin(self.text)
        win.draw()
        win.text(self.value)
        #draw_text_on_win(self.menu, self.value, 75)
        
    def handle_input(self, key):
        self.menu.in_submenu = True
        
        if (key == "GO" or key == "ENT") and self.in_item:
            self.menu.in_submenu = False
            self.in_item = False
            self.menu.display_menu()
            if self.callback != None:
                self.callback(self, self.value)
            return
        
        elif key == "SPC":
            self.value += " "
            
        elif len(key) == 1:
            self.value += key
            
        elif key == "BSPC":
            self.value = self.value[:-1]
            
        self.in_item = True
        self.draw_win()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Popup Window ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_WINDOW_PADDING = const(10)

_WINDOW_WIDTH = const(_DISPLAY_WIDTH-(_WINDOW_PADDING*2))
_WINDOW_HEIGHT = const(_DISPLAY_HEIGHT-(_WINDOW_PADDING*2))

_WINDOW_TITLE_Y = const(16)
_WINDOW_WRITE_Y = const(80)
_WINDOW_WRITE_Y_OVERFLOW = const(_WINDOW_WRITE_Y-_FONT_HEIGHT)

_MAX_TEXT_LEN = const(_WINDOW_WIDTH//_FONT_WIDTH)

class PopUpWin:
    def __init__(self, title: str = None):
        self.title = title
        
    def text(self, string:str):
        if len(string) > _MAX_TEXT_LEN:
            draw_centered_text(string[:len(string)-_MAX_TEXT_LEN], _DISPLAY_WIDTH_CENTER, _WINDOW_WRITE_Y_OVERFLOW, CONFIG['ui_color'], font=FONT)
            draw_centered_text(string[len(string)-_MAX_TEXT_LEN:], _DISPLAY_WIDTH_CENTER, _WINDOW_WRITE_Y, CONFIG['ui_color'], font=FONT)
        else:
            draw_centered_text(string, _DISPLAY_WIDTH_CENTER, _WINDOW_WRITE_Y, CONFIG['ui_color'], font=FONT)
    
    def draw(self):
        DISPLAY.fill_rect(_WINDOW_PADDING, _WINDOW_PADDING, _WINDOW_WIDTH, _WINDOW_HEIGHT, CONFIG['bg_color'])
        DISPLAY.rect(_WINDOW_PADDING, _WINDOW_PADDING, _WINDOW_WIDTH, _WINDOW_HEIGHT, CONFIG.palette[4])
        
        for i in range(6):
            DISPLAY.hline(_WINDOW_PADDING+i,
                          _WINDOW_PADDING+_WINDOW_HEIGHT+i,
                          _WINDOW_WIDTH, CONFIG.palette[0])
            DISPLAY.vline(_WINDOW_PADDING+_WINDOW_WIDTH+i,
                          _WINDOW_PADDING+i,
                          _WINDOW_HEIGHT, CONFIG.palette[0])

        if self.title:
            draw_centered_text(str(self.title + ":"), _DISPLAY_WIDTH_CENTER, _WINDOW_TITLE_Y, CONFIG.palette[4], font=FONT)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Shape Functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def draw_small_arrow(x, y, color, direction=1):
    for i in range(0,8):
        DISPLAY.hline(
            x = (x - i),
            y = y + (i*direction),
            length = 2 + (i*2),
            color = color)

def draw_select_arrow(x, y, color):
    x -= 16
    _ARROW_COORDS = array.array('h', (16,0, 17,0, 33,16, 33,24, 0,24, 0,16))
    DISPLAY.polygon(_ARROW_COORDS, x, y, color, fill=True)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Text Functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def draw_centered_text(text, x, y, color, font=None, bgcolor=0):
    # draw text centered on the x axis
    
    if font:
        x = x - (len(text) * _FONT_WIDTH_HALF)
        DISPLAY.bitmap_text(font, text, x, y, color)
    else:
        x = x - (len(text) * _SMALL_FONT_WIDTH_HALF)
        DISPLAY.text(text, x, y, color)

def get_text_center(text:str, font):
    center = int((len(text) * font.WIDTH) // 2)
    return (center)

def draw_left_text(text:str, y_pos:int, selected):
    if selected:
        DISPLAY.bitmap_text(FONT, text, _LEFT_TEXT_UNSELECTED_X, y_pos, CONFIG.palette[0])
        DISPLAY.bitmap_text(FONT, '>'+text, _LEFT_TEXT_SELECTED_X, y_pos, CONFIG.palette[5])
    else:
        DISPLAY.bitmap_text(FONT, text, _LEFT_TEXT_UNSELECTED_X, y_pos, CONFIG.palette[4])

def draw_right_text(text:str, y_pos:int, selected=False):
    DISPLAY.fill_rect(160, y_pos+_RIGHT_TEXT_Y, 80, _SMALL_FONT_HEIGHT, CONFIG['bg_color'])# clear word
    x = _RIGHT_TEXT_X - (len(text)*_SMALL_FONT_WIDTH_HALF)
    
    if len(text) * _SMALL_FONT_WIDTH_HALF > 80:
         x = ((_DISPLAY_WIDTH // 2) + _RIGHT_TEXT_X_OFFSET)
    if selected:
        DISPLAY.text((text), x, y_pos+_RIGHT_TEXT_Y, CONFIG.palette[4])
    else:
        DISPLAY.text((text), x, y_pos+_RIGHT_TEXT_Y, CONFIG.palette[3])

if __name__ == '__main__':
    # just for testing!
    from launcher import newSettings
