class Kanji:
    def __init__(self,tft):
        self.tft = tft
        self.misc_font =  {'，': '0x102030000000000', '；': '0x4080c000c0c0000', '。': '0x205020000000000', '《': '0x5028140a14285000', '》': '0x50a1428140a0500', '【': '0x7030101010307000', '】': '0x706040404060700', '、': '0x201000000000000', '！': '0x800080808080800', '？': '0x800083040423c00', '：': '0xc0c000c0c0000', '（': '0x4020101010204000', '）': '0x102040404020100', '“': '0x6c244800', '”': '0x9121b00', '‘': '0x60204000', '’': '0x1020300', '…': '0x4900000000', '—': '0xff00000000', '·': '0x200000000', '～': '0x304906000000', '「': '0x8080808087800', '」': '0xf08080808080000', '『': '0x1c14141474447c00', '』': '0x1f11171414141c00', 'あ': '0x264d563c043e0400', 'い': '0x40a414121110000', 'う': '0x1c2040423c003c00', 'え': '0x621418103e003c00', 'お': '0x3645463c442f0400', 'か': '0xd1252542f040400', 'き': '0x3c02247e103e0800', 'く': '0x20100c020c102000', 'け': '0x81111117d111100', 'こ': '0x7c020400003c0000', 'さ': '0x3c0224207e101000', 'し': '0x3844040404040400', 'す': '0x8101814187f1000', 'せ': '0x780434247f242400', 'そ': '0x3008087e08103c00', 'た': '0x710a1202740f0400', 'ち': '0x38404438087e1000', 'つ': '0x384040433c0000', 'て': '0x60100808102e7000', 'と': '0x7c02041864040400', 'な': '0x18643922442f0400', 'に': '0x7905090101390100', 'ぬ': '0x6a654d563a121000', 'ね': '0x245566444f340400', 'の': '0x182245492a1c0000', 'は': '0x592539217d212100', 'ひ': '0x1c22222264271400', 'ふ': '0x4d52320808100800', 'へ': '0x60110a040000', 'ほ': '0x595539117d117d00', 'ま': '0x5e3e107e107e1000', 'み': '0x1823653e24080e00', 'む': '0x3c460506442f0400', 'め': '0x2a454d563a121000', 'も': '0x3844443e043e0800', 'や': '0x8080424473a1200', 'ゆ': '0x4083d494b3d0800', 'よ': '0x4c321c1070101000', 'ら': '0x3c40463a02100c00', 'り': '0xc10202222261a00', 'る': '0x3c4c423c08103c00', 'れ': '0x442526242f340400', 'ろ': '0x3c40423c08103c00', 'わ': '0x344546444f340400', 'を': '0x7814196e043e0800', 'ん': '0x314a0a0404080800', 'ア': '0x408081828407e00', 'イ': '0x1010161810204000', 'ウ': '0xc102040427e0800', 'エ': '0x7f0808083e0000', 'オ': '0x18131418107f1000', 'カ': '0x62444848487e0800', 'キ': '0x10107e08083e0800', 'ク': '0xc10204244780800', 'ケ': '0x4081011127e0200', 'コ': '0x7e404040407e0000', 'サ': '0xc102024247f2400', 'シ': '0xe10204442040200', 'ス': '0x432c1010203e0000', 'セ': '0x780424447f040400', 'ソ': '0xc10204044444200', 'タ': '0xc10205a44780800', 'チ': '0x408087f080e3000', 'ツ': '0xc10204a4a450000', 'テ': '0x40808087f003e00', 'ト': '0x404241c04040400', 'ナ': '0x20408087f080800', 'ニ': '0x7f0000003e0000', 'ヌ': '0x32418102c203e00', 'ネ': '0x84b2c08103e0800', 'ノ': '0x304081020202000', 'ハ': '0x4142422424140000', 'ヒ': '0x7c02021e62020200', 'フ': '0xc102040407e0000', 'ヘ': '0x4020110a040000', 'ホ': '0xc492a087f080800', 'マ': '0x10081420407f0000', 'ミ': '0x300e001804300e00', 'ム': '0x5f22120404080800', 'メ': '0x32428102e202000', 'モ': '0x7008087e08083c00', 'ヤ': '0x80808244f740400', 'ユ': '0x7f1010101e0000', 'ヨ': '0x7e40407c407e0000', 'ラ': '0xc1020407e003c00', 'リ': '0xc10202222222200', 'ル': '0x1132541414141000', 'レ': '0xc14244404040400', 'ロ': '0x7e424242427e0000', 'ワ': '0xc102040427e0000', 'ヲ': '0xc1020407c407e00', 'ン': '0xe10204040040200', 'a': '0x6556000', 'b': '0x3553110', 'c': '0x6116000', 'd': '0x6556440', 'e': '0x6352000', 'f': '0x2227260', 'g': '0x74757000', 'h': '0x5553110', 'i': '0x7223020', 'j': '0x12222020', 'k': '0x5535110', 'l': '0x7222230', 'm': '0x5575000', 'n': '0x5553000', 'o': '0x2552000', 'p': '0x13553000', 'q': '0x46556000', 'r': '0x1135000', 's': '0x3636000', 't': '0x6227200', 'u': '0x6555000', 'v': '0x2255000', 'w': '0x5755000', 'x': '0x5225000', 'y': '0x34655000', 'z': '0x7247000', 'A': '0x5575520', 'B': '0x3553530', 'C': '0x6111160', 'D': '0x3555530', 'E': '0x7113170', 'F': '0x1113170', 'G': '0x6551160', 'H': '0x5575550', 'I': '0x7222270', 'J': '0x2544440', 'K': '0x5553550', 'L': '0x7111110', 'M': '0x5557750', 'N': '0x5555530', 'O': '0x2555520', 'P': '0x1135530', 'Q': '0x42555520', 'R': '0x5535530', 'S': '0x3442160', 'T': '0x2222270', 'U': '0x7555550', 'V': '0x1355550', 'W': '0x5775550', 'X': '0x5522550', 'Y': '0x2222550', 'Z': '0x7122470', '0': '0x2555200', '1': '0x7223200', '2': '0x7124300', '3': '0x3424300', '4': '0x4756400', '5': '0x3431700', '6': '0x7571700', '7': '0x2224700', '8': '0x7575700', '9': '0x7475700', '~': '0x630', '!': '0x2022220', '@': '0x2564520', '#': '0x5755750', '$': '0x2763720', '%': '0x4124100', '^': '0x520', '&': '0xb5a5520', '*': '0x52720', '(': '0x42222240', ')': '0x12222210', '_': '0x70000000', '+': '0x2272200', '-': '0x70000', '=': '0x707000', '[': '0x62222260', ']': '0x32222230', '{': '0x42212240', '}': '0x12242210', '|': '0x22222220', ';': '0x1202000', "'": '0x120', ':': '0x202000', '"': '0x550', ',': '0x24000000', '.': '0x2000000', '/': '0x124000', '<': '0x4212400', '>': '0x1242100', '?': '0x2024520', ' ': '0x0'}
        self.font = open("/font/kanji_8x8.bin", "rb", buffering = 0)
        self.cache = {}
           
    def show_decode(self, cur, x, y, color, scale=2, height=8, width=8):
        """Display the decoded character on the screen."""
        for i in range(height):
            for j in range(width):
                if cur & 1:
                    self.tft.rect(x + j * scale, y + i * scale, scale, scale, color, True)
                cur >>= 1

    def putc(self, char, x, y, color, scale=2, custom_dictionary = None):
        """Render a single character on the screen."""
        if custom_dictionary != None and char in custom_dictionary:
            self.show_decode(custom_dictionary[char], x, y, color, scale)
            return
        
        if char in self.misc_font:
            self.show_decode(int(self.misc_font[char], 16), x, y, color, scale, width=4)
        elif char in self.cache:
            self.show_decode(int(self.cache[char]), x, y, color, scale)
        else:
            found = False
            codepoint = ord(char)
            
            if 0x4E00 <= codepoint <= 0x9FFF:
                # Calculate the offset in the binary file
                offset = (codepoint - 0x4E00) * 8
                self.font.seek(offset)
                
                # Read the 8 bytes and decode
                cur = int.from_bytes(self.font.read(8), 'big')
                self.cache[char] = cur
                found = True
            else:
                self.cache[char] = 0x7e424242427e0000
            
            if found:
                self.show_decode(self.cache[char], x, y, color, scale)
            else:
                self.show_decode(0x7e424242427e0000, x, y, color, scale)

            if len(self.cache) >= 200:
                del self.cache[list(self.cache.keys())[0]]

    def text(self, string, x, y, color, scale=2, instant_show=True, custom_dictionary = None):
        """Render a string of text on the screen."""
        cur_x = x
        for char in string:
            self.putc(char, cur_x, y, color, scale,custom_dictionary)
            if instant_show:
                self.tft.show()
            
            if char in self.misc_font:
                cur_x += 4 * scale
            else:
                cur_x += 8 * scale


