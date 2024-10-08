"""Lines class for the Terminal."""
from lib.display import Display


txt_clrs = {
    '30': 0,
    '31': 11,
    '32': 12,
    '33': 14,
    '34': 13,
    '35': 4,
    '36': 5,
    '37': 9,
    '90': 3,
    '91': 11,
    '92': 12,
    '93': 8,
    '94': 13,
    '95': 14,
    '96': 6,
    '97': 10,
}
# bg colors are txt colors + 10


class _StyleStr:
    """Color/style and string, for the TermLine class."""

    # class level style helps us remember styling between strings/lines
    text_color = None
    bg_color = None
    bold = False
    underline = False

    def __init__(self, text):
        if text.startswith('\033[') and 'm' in text:
            # Get style attributes
            text = text[2:]
            style, text = text.split('m', 1)


            for styl in style.split(';'):

                # Style resetters:
                if styl == '0':  # Reset all
                    _StyleStr.text_color = None
                    _StyleStr.bg_color = None
                    _StyleStr.bold = False
                    _StyleStr.underline = False
                elif styl == '39':  # Default foreground color
                    _StyleStr.text_color = None
                elif styl == '49':  # Default background color
                    _StyleStr.bg_color = None

                elif styl == '1':  # Bold
                    _StyleStr.bold = True
                elif styl == '22':  # Normal intensity
                    _StyleStr.bold = False

                elif styl == '4':  # Underline
                    _StyleStr.underline = True
                elif styl == '24':  # Underline off
                    _StyleStr.underline = False

                # text color
                elif styl in txt_clrs:
                    _StyleStr.text_color = txt_clrs[styl]

                # BG color
                elif styl.isdigit() and str(int(styl) - 10) in txt_clrs:
                    _StyleStr.bg_color = txt_clrs[str(int(styl) - 10)]

        self.text = text
        self.txt_clr = _StyleStr.text_color
        self.bg_clr = _StyleStr.bg_color
        self.bld = _StyleStr.bold
        self.undrln = _StyleStr.underline
        self.width = Display.get_total_width(text)


    def draw(self, x, y, display):
        txt_clr = 7 if self.txt_clr is None else self.txt_clr
        bg_clr = 2 if self.bg_clr is None else self.bg_clr
        display.rect(x, y-1, self.width, 10, display.palette[bg_clr], fill=True)
        if self.bld:
            display.text(self.text, x+1, y, display.palette[txt_clr])
        if self.undrln:
            display.hline(x, y+9, self.width, display.palette[txt_clr])
        display.text(self.text, x, y, display.palette[txt_clr])


class TermLine:
    """Single line, with color support."""

    def __init__(self, text):
        """Create a line with the given text."""
        self.strings = self._get_strings(text)

    @staticmethod
    def _get_strings(string) -> list[_StyleStr]:
        """Get style strings from text."""
        strings = []
        current_str = ''
        while string:
            if string.startswith('\033[') \
            and current_str:
                strings.append(_StyleStr(current_str))
                current_str = ''
            current_str += string[0]
            string = string[1:]
        strings.append(_StyleStr(current_str))
        return strings

    def draw(self, x: int, y: int, display: Display):
        """Draw the line."""
        for string in self.strings:
            string.draw(x, y, display)
            x += string.width

