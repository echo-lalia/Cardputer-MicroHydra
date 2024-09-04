"""
Builtin Settings app for MicroHydra.
This app provides a useful GUI for changing the values in /config.json
"""

from lib import userinput
from lib.hydra import config
from lib.hydra import menu as hydramenu
from lib.hydra.popup import UIOverlay
from lib.display import Display
from lib.hydra.i18n import I18n
from lib.sdcard import SDCard
import json
import os
import time
import machine

# make the animations smooth :)
machine.freq(240_000_000)

# this defines the translations passed to hydra.menu and hydra.popup
_TRANS = const("""[
  {"en": "language", "zh": "语言/Lang", "ja": "言語/Lang"},
  {"en": "volume", "zh": "音量", "ja": "音量"},
  {"en": "ui_color", "zh": "UI颜色", "ja": "UIの色"},
  {"en": "bg_color", "zh": "背景颜色", "ja": "背景色"},
  {"en": "wifi_ssid", "zh": "WiFi名称", "ja": "WiFi名前"},
  {"en": "wifi_pass", "zh": "WiFi密码", "ja": "WiFiパスワード"},
  {"en": "sync_clock", "zh": "同步时钟", "ja": "時計同期"},
  {"en": "24h_clock", "zh": "24小时制", "ja": "24時間制"},
  {"en": "timezone", "zh": "时区", "ja": "タイムゾーン"},
  {"en": "Confirm", "zh": "确认", "ja": "確認"}
]""")


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Globals: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

display = Display()
kb = userinput.UserInput()
config = config.Config()
I18N = I18n(_TRANS)
overlay = UIOverlay(i18n=I18N)

LANGS = ['en', 'zh', 'ja']
LANGS.sort()

# try mounting SDCard for settings import/export
try:
    sd = SDCard()
    sd.mount()
except:
    sd = None



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Functions: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def update_config(caller, value):
    global I18N

    config[caller.text] = value

    # regen palette and translations based on new vals
    config.generate_palette()
    I18N.__init__(_TRANS)

    print(f"config['{caller.text}'] = {value}")


def discard_conf(caller):
    print("Discard config.")
    display.fill(0)
    display.show()
    time.sleep_ms(10)
    machine.reset()


def save_conf(caller):
    config.save()
    print("Save config: ", config.config)
    display.fill(0)
    display.show()
    time.sleep_ms(10)
    machine.reset()


def export_config(caller):
    # try making hydra directory
    try:
        os.mkdir('sd/Hydra')
    except OSError: pass
    
    # try exporting config file
    try:
        with open("sd/Hydra/config.json", "w") as file:
            file.write(json.dumps(config.config))
            print(json.dumps(config.config))
        overlay.popup("Config exported to 'sd/Hydra/config.json'")
    except OSError as e:
        overlay.error(e)


def import_config(caller):
    global I18N, menu
    try:
        with open("sd/Hydra/config.json", "r") as file:
            config.config.update(json.loads(file.read()))
        
        # update config and lang
        config.generate_palette()
        I18N.__init__(_TRANS)

        overlay.popup("Config loaded from 'sd/Hydra/config.json'")
        # update menu
        menu.exit()
        build_menu()

    except Exception as e:
        overlay.error(e)


def import_export(caller):
    choice = overlay.popup_options(("Back...", "Export to SD", "Import from SD"), title="Import/Export config", depth=1)
    if choice == "Export to SD":
        export_config(caller)
    elif choice == "Import from SD":
        import_config(caller)



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Create the menu: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def build_menu():
    """Create and return a manu for the config."""
    global menu, I18N
    menu = hydramenu.Menu(
        esc_callback=discard_conf,
        i18n=I18N,
        )

    menu_def = [
        (hydramenu.ChoiceItem, 'language', {'choices':LANGS, 'instant_callback': update_config}),
        (hydramenu.IntItem, 'volume', {'min_int': 0, 'max_int': 10, 'instant_callback': update_config}),
        (hydramenu.RGBItem, 'ui_color', {'instant_callback': update_config}),
        (hydramenu.RGBItem, 'bg_color', {'instant_callback': update_config}),
        (hydramenu.WriteItem, 'wifi_ssid', {}),
        (hydramenu.WriteItem, 'wifi_pass', {'hide': True}),
        (hydramenu.BoolItem, 'sync_clock', {}),
        (hydramenu.BoolItem, '24h_clock', {}),
        (hydramenu.IntItem, 'timezone', {'min_int': -13, 'max_int': 13}),
    ]

    # build menu from def
    for i_class, name, kwargs in menu_def:
        menu.append(
            i_class(
                menu,
                name,
                config[name],
                callback=update_config,
                **kwargs
            ))

    menu.append(hydramenu.DoItem(menu, "Import/Export", callback=import_export))
    menu.append(hydramenu.DoItem(menu, "Confirm", callback=save_conf))

    return menu



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main body: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Thanks to HydraMenu, the settings app is now pretty small.
# So, not much point in overcomplicating things:

menu = build_menu()

# this loop lets us restart the new menu if it is stopped/recreated by the callbacks above
while True:
    menu.main()

