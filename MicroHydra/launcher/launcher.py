"""

VERSION: 0.8

CHANGES:
    Created mhconfig.Config, mhoverlay.UI_Overlay, cleaned up launcher.py, endured the horrors

This program is designed to be used in conjunction with "main.py" apploader, to select and launch MPy apps.

The basic app loading logic works like this:
 - apploader reads reset cause and RTC.memory to determine which app to launch
 - apploader launches 'launcher.py' when hard reset, or when RTC.memory is blank
 - launcher scans app directories on flash and SDCard to find apps
 - launcher shows list of apps, allows user to select one
 - launcher stores path to app in RTC.memory, and soft-resets the device
 - apploader reads RTC.memory to find path of app to load
 - apploader clears the RTC.memory, and imports app at the given path
 - app at given path now has control of device.
 - pressing the reset button will relaunch the launcher program, and so will calling machine.reset() from the app. 

This approach was chosen to reduce the chance of conflicts or memory errors when switching apps.
Because MicroPython completely resets between apps, the only "wasted" ram from the app switching process will be from main.py

"""
#pre-allocate the buffers needed for our framebufs
#displaybytes = bytearray(240*145*2)




import machine, sys, network, gc, time, os, _thread
import ntptime
from launcher.icons import battery
from launcher.icons import icons
from lib import keyboard
from lib import beeper
from lib.mhconfig import Config
from font import vga2_16x32 as font
from lib import minifbuf as st7789
buf2 = bytearray(240*39*2)
buf1 = bytearray(240*38*2)
buf0 = bytearray(240*35*2)
buf3 = bytearray(240*23*2)
gc.collect()
beep = beeper.Beeper()
gc.collect()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Create Global Objects: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#first, create the ESP-idf based obs which are picky about memory and heap usage,
#then create objects in order from largest to smallest

sd = None #placeholder var for when SDCard can't be initialized
try:
    sd = machine.SDCard(slot=2, sck=machine.Pin(40), miso=machine.Pin(39), mosi=machine.Pin(14), cs=machine.Pin(12))
except OSError as e:
    print("SDCard couldn't be initialized, gave this error: ", e)
gc.collect()
nic = None
try:
    nic = network.WLAN(network.STA_IF)
except RuntimeError as e:
        print("Wifi WLAN object couldnt be created. Gave this error:",e)



gc.collect()
#init driver for the graphics immediately, (creates large framebuffer objects, trying to minimize memory fragmentation issues)
# buf1 = bytearray(240*77*2)
# buf0 = bytearray(240*35*2)
# buf2 = bytearray(240*23*2)

tft = st7789.ST7789(
    machine.SPI(1, baudrate=40000000, sck=machine.Pin(36), mosi=machine.Pin(35), miso=None),
    135,
    240,
    reset=machine.Pin(33, machine.Pin.OUT),
    cs=machine.Pin(37, machine.Pin.OUT),
    dc=machine.Pin(34, machine.Pin.OUT),
    backlight=machine.Pin(38, machine.Pin.OUT),
    rotation=1,
    color_order=st7789.BGR,
    custom_framebufs =((buf0, 0,0,240,35),(buf1, 0,35,240,38),(buf2, 0,73,240,39),(buf3, 0,112,240,23))
    ) # 	buf_idx: 0(status bar), 1(app icons), 2(app text), 3(scroll bar)

gc.collect()
kb = keyboard.KeyBoard()
gc.collect()
#init the ADC for the battery
batt = machine.ADC(10)
batt.atten(machine.ADC.ATTN_11DB)
gc.collect()
rtc = machine.RTC()
gc.collect()
config = Config()



#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ WIFI and RTC: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def wifi_sync_rtc(rtc, nic):
    # sync our clock if set in the config:
    if config['sync_clock'] and nic != None:
        # no point if there's no connection settings, or if clock already set
        if config['wifi_ssid'] != '' and rtc.datetime()[0] == 2000: 
            try:
                # create object to control network conenction
                #nic = network.WLAN(network.STA_IF)
                _MAX_WIFI_ATTEMPTS = const(100)
                _MAX_NTP_ATTEMPTS = const(10)

                gc.collect()
                
                if not nic.active(): # turn on wifi if it isn't already
                    nic.active(True)
                
                
                connection_attempts = 0
                while not nic.isconnected(): #wait for connection
                    try:
                        nic.connect(config['wifi_ssid'], config['wifi_pass'])
                    except OSError as e:
                        print("wifi_sync_rtc had this error when connecting:",e)
                        gc.collect()
                        time.sleep(1)
                    connection_attempts += 1
                    if connection_attempts >= _MAX_WIFI_ATTEMPTS:
                        break
                    time.sleep_ms(10)
                    
                #once connected, try syncing clock with ntp server
                if nic.isconnected():
                    ntp_attempts = 0
                    while rtc.datetime()[0] == 2000 and ntp_attempts < _MAX_NTP_ATTEMPTS: #while clock is on default value/haven't passed max attempts
                        #ntptime.settime()
                        try:
                            ntptime.settime()
                        except OSError as e:
                            print("ntptime had this error when connecting:", e)
                            pass # ntptime.settime() throws OSErrors sometimes, even if it works
                        time.sleep(1)
                        ntp_attempts += 1
                else:
                    print("wifi_sync_rtc couldn't connect to wifi")
                
                #shut off wifi
                nic.disconnect()
                nic.active(False) 

                if rtc.datetime()[0] == 2000:
                    print('RTC failed to sync.')
                else:
                    #apply our timezone offset
                    time_list = list(rtc.datetime())
                    time_list[4] = time_list[4] + config['timezone']
                    rtc.datetime(tuple(time_list))
                    print(f'RTC successfully synced to {rtc.datetime()}.')
                gc.collect()
            except RuntimeError as e:
                    if nic.active():
                        try:
                            nic.active(True)
                        except:
                            print("couldn't deactivate nic")
                    print("Wifi WLAN object couldnt be created. Gave this error:",e)

_thread.start_new_thread(wifi_sync_rtc, (rtc, nic))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Finding Apps ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def scan_apps(sd):
    # first we need a list of apps located on the flash or SDCard
    gc.collect()
    main_directory = os.listdir("/")
    
    # if the sd card is not mounted, we need to mount it.
    if "sd" not in main_directory:
        if "sd" == None:
            try:
                sd = machine.SDCard(slot=2, sck=machine.Pin(40), miso=machine.Pin(39), mosi=machine.Pin(14), cs=machine.Pin(12))
            except OSError as e:
                print(e)
                print("SDCard couldn't be initialized.")
                try:
                    sd.deinit()
                except:
                    print("Couldn't deinitialize SDCard")
        
        if sd != None: # error above can lead to none type here
            try:
                os.mount(sd, '/sd')
            except OSError as e:
                print(e)
                print("Could not mount SDCard.")
            except NameError as e:
                print(e)
                print("SDCard not mounted")
            
        main_directory = os.listdir("/")

    sd_directory = []
    if "sd" in main_directory:
        sd_directory = os.listdir("/sd")

    # if the apps folder does not exist, create it.
    if "apps" not in main_directory:
        os.mkdir("/apps")
        main_directory = os.listdir("/")
        
    # do the same for the sdcard apps directory
    if "apps" not in sd_directory and "sd" in main_directory:
        os.mkdir("/sd/apps")
        sd_directory = os.listdir("/sd")

    # if everything above worked, sdcard should be mounted (if available), and both app directories should exist. now look inside to find our apps:
    main_app_list = os.listdir("/apps")
    sd_app_list = []

    if "sd" in main_directory:
        try:
            sd_app_list = os.listdir("/sd/apps")
        except OSError as e:
            print(e)
            print("SDCard mounted but cant be opened; assuming it's been removed. Unmounting /sd.")
            os.umount('/sd')

    # now lets collect some separate app names and locations
    app_names = []
    app_paths = {}

    for entry in main_app_list:
        if entry.endswith(".py"):
            this_name = entry[:-3]
            
            # the purpose of this check is to prevent dealing with duplicated apps.
            # if multiple apps share the same name, then we will simply use the app found most recently. 
            if this_name not in app_names:
                app_names.append( this_name ) # for pretty display
            
            app_paths[f"{this_name}"] = f"/apps/{entry}"

        elif entry.endswith(".mpy"):
            this_name = entry[:-4]
            if this_name not in app_names:
                app_names.append( this_name )
            app_paths[f"{this_name}"] = f"/apps/{entry}"
            
            
    for entry in sd_app_list:
        if entry.endswith(".py"): #repeat for sdcard
            this_name = entry[:-3]
            
            if this_name not in app_names:
                app_names.append( this_name )
            
            app_paths[f"{this_name}"] = f"/sd/apps/{entry}"
            
        elif entry.endswith(".mpy"):
            this_name = entry[:-4]
            if this_name not in app_names:
                app_names.append( this_name )
            app_paths[f"{this_name}"] = f"/sd/apps/{entry}"
            
    #sort alphabetically without uppercase/lowercase discrimination:
    app_names.sort(key=lambda element: element.lower())
    
    #add an appname to refresh the app list
    app_names.append("Reload Apps")
    #add an appname to control the beeps
    app_names.append("UI Sound")
    #add an appname to open settings app
    app_names.append("Settings")
    app_paths["Settings"] = "/launcher/settings.py"
    
    gc.collect()
    return app_names, app_paths, sd




#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Function Definitions: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def launch_app(app_path):
    #print(f'launching {app_path}')
    rtc = machine.RTC()
    rtc.memory(app_path)
    print(f"Launching '{app_path}...'")
    # reset clock speed to default.
    machine.freq(160_000_000)
    time.sleep_ms(10)
    machine.reset()
    



def center_text_x(text, char_width = 16):
    """
        Calculate the x coordinate to draw a text string, to make it horizontally centered. (plus the text width)
    """
    str_width = len(text) * char_width
    # display is 240 px wide
    start_coord = 120 - (str_width // 2)
    
    return start_coord

def ease_out_cubic(x):
    return 1 - ((1 - x) ** 3)

def ease_in_out_cubic(x):
    if x < 0.5:
        return 4 * x * x * x
    else:
        return 1 - ((-2 * x + 2) ** 3) / 2

def ease_in_out_quart(x):
    if x < 0.5:
        return 8 * x * x * x * x
    else:
        return 1 - ((-2 * x + 2) ** 4) / 2

def time_24_to_12(hour_24,minute):
    ampm = 'am'
    if hour_24 >= 12:
        ampm = 'pm'
        
    hour_12 = hour_24 % 12
    if hour_12 == 0:
        hour_12 = 12
        
    time_string = f"{hour_12}:{'{:02d}'.format(minute)}"
    return time_string, ampm


def read_battery_level(adc):
    """
    read approx battery level on the adc and return as int range 0 (low) to 3 (high)
    """
    raw_value = adc.read_uv() # vbat has a voltage divider of 1/2
    
    # more real-world data is needed to dial in battery level.
    # the original values were low, so they will be adjusted based on feedback.
    
    #originally 525000 (1.05v)
    if raw_value < 1575000: #3.15v
        return 0
    #originally 1050000 (2.1v)
    if raw_value < 1750000: #3.5v
        return 1
    #originally 1575000 (3.15v)
    if raw_value < 1925000: #3.85v
        return 2
    # 2100000 (4.2v)
    return 3 # 4.2v or higher



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GRAPHICS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def scroll_text(tft, scroll_factor, app_names, app_selector_index, prev_selector_index, config):
    """Handle scrolling animation for app text (buf_idx = 2)"""
    global text_scroll_position, prev_text_scroll_position
    
    if scroll_factor < 0: # handle negative numbers
        text_ease_factor = -ease_in_out_quart( abs(scroll_factor))
    else:
        text_ease_factor = ease_in_out_quart(scroll_factor)
        
    # scroll text out of view using scroll method
    text_scroll_position = int(text_ease_factor * 240)
    tft.scroll(text_scroll_position - prev_text_scroll_position, 0, buf_idx=2)
    
    if abs(text_scroll_position) < 120:
        #blackout the old text
        if text_scroll_position == 0: # full blackout
            tft.fill(config['bg_color'], buf_idx = 2)
            
        else: # partial blackout
            blackout_width = (min(len(app_names[prev_selector_index]), 15)) * 16
            tft.rect((120 - (blackout_width // 2)) + text_scroll_position, 80, blackout_width, 32, config['bg_color'], fill=True, buf_idx=2)
            #also blackout right or left (depending on scroll direction) to prevent streaks
            scroll_size = abs(text_scroll_position - prev_text_scroll_position)
            if text_scroll_position > 0:
                tft.rect(240 - (scroll_size), 80, scroll_size, 32, config['bg_color'], fill=True, buf_idx=2)
            else:
                tft.rect(0, 80, scroll_size, 32, config['bg_color'], fill=True, buf_idx=2)
            
        #crop text for display
        current_app_text = app_names[app_selector_index]
        if len(current_app_text) > 15:
            current_app_text = current_app_text[:12] + "..."

        #draw new text
        tft.bitmap_text(font, current_app_text, center_text_x(current_app_text) + text_scroll_position, 80, config['ui_color'], buf_idx=2)
    tft.show(buf_idx=2)
    
    
def scroll_icon(tft, scroll_factor, app_names, app_selector_index, config, app_paths):
    """Handle scrolling animation for app icon (buf_idx = 1)"""
    global icon_scroll_position, prev_icon_scroll_position
    
    if scroll_factor < 0: # handle negative numbers
        icon_ease_factor = -ease_in_out_cubic( abs(scroll_factor))
    else:
        icon_ease_factor = ease_in_out_cubic(scroll_factor)
    
    # scroll text out of view using scroll method
    icon_scroll_position = int(icon_ease_factor * 240)
    tft.scroll(icon_scroll_position - prev_icon_scroll_position, 0, buf_idx=1)
    
    if 30 < abs(icon_scroll_position) < 130 or icon_scroll_position == 0:
        # redraw icons
        #blackout old icon
        tft.fill(config['bg_color'], buf_idx=1)
        
        current_app_text = app_names[app_selector_index]
        #special menu options for settings
        if current_app_text == "UI Sound":
            if config['ui_sound']:
                tft.bitmap_text(font, "On", center_text_x("On") + icon_scroll_position, 36, config['ui_color'], buf_idx=1)
            else:
                tft.bitmap_text(font, "Off", center_text_x("Off") + icon_scroll_position, 36, config.palette[3], buf_idx=1)
                
        elif current_app_text == "Reload Apps":
            tft.bitmap_icons(icons, icons.RELOAD, config['ui_color'],104 + icon_scroll_position, 36, buf_idx=1)
            
        elif current_app_text == "Settings":
            tft.bitmap_icons(icons, icons.GEAR, config['ui_color'],104 + icon_scroll_position, 36, buf_idx=1)
            
        elif app_paths[app_names[app_selector_index]][:3] == "/sd":
            tft.bitmap_icons(icons, icons.SDCARD, config['ui_color'],104 + icon_scroll_position, 36, buf_idx=1)
        else:
            tft.bitmap_icons(icons, icons.FLASH, config['ui_color'],104 + icon_scroll_position, 36, buf_idx=1)
    tft.show(buf_idx=1)

def draw_status_bar(tft, config, batt):
    """Handle redrawing the status bar (buf_idx = 0)"""
    
    tft.fill(config['bg_color'], buf_idx=0)
    tft.rect(0,0,240, 16, config.palette[2], fill=True, buf_idx=0)
    tft.hline(0,17,240, config.palette[0], buf_idx=0) # shadow
    
    #clock
    _,_,_, hour_24, minute, _,_,_ = time.localtime()
    formatted_time, ampm = time_24_to_12(hour_24, minute)
    tft.text(formatted_time, 11,5,config.palette[0], buf_idx=0) # shadow
    tft.text(formatted_time, 10,4,config['ui_color'], buf_idx=0)
    tft.text(ampm, 11 + (len(formatted_time) * 8),5,config.palette[0], buf_idx=0) # shadow
    tft.text(ampm, 10 + (len(formatted_time) * 8),4,config.palette[4], buf_idx=0)
    
    #battery
    battlevel = read_battery_level(batt)
    tft.bitmap_icons(battery, battery.FULL, config.palette[0],209, 4, buf_idx=0) # shadow
    if battlevel == 3:
        tft.bitmap_icons(battery, battery.FULL, config.rgb_colors[1],208, 3, buf_idx=0)
    elif battlevel == 2:
        tft.bitmap_icons(battery, battery.HIGH, config['ui_color'],208, 3, buf_idx=0)
    elif battlevel == 1:
        tft.bitmap_icons(battery, battery.LOW, config['ui_color'],208, 3, buf_idx=0)
    else:
        tft.bitmap_icons(battery, battery.EMPTY, config.rgb_colors[0],208, 3, buf_idx=0)
    tft.show(buf_idx=0)
    
def draw_scroll_bar(tft, config, app_selector_index, app_names):
    """Handle redrawing the scroll bar (buf_idx = 3)"""
    tft.fill(config['bg_color'], buf_idx=3)
    
    exact_scrollbar_width = 232 / len(app_names)
    scrollbar_width = int(exact_scrollbar_width)
    tft.rect(int(exact_scrollbar_width * app_selector_index) + 4,131,
             scrollbar_width,4,config.palette[4], fill=True, buf_idx=3)
    tft.rect(int(exact_scrollbar_width * app_selector_index) + 4,131,
             scrollbar_width,4,config.palette[2], fill=False, buf_idx=3)
    tft.show(buf_idx=3)

#--------------------------------------------------------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Loop: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#--------------------------------------------------------------------------------------------------

def main_loop():
    global sd, rtc, tft, kb, beep, config, batt
    global prev_icon_scroll_position, icon_scroll_position, prev_text_scroll_position, text_scroll_position
    
    machine.freq(240_000_000)
    #before anything else, we should scan for apps
    app_names, app_paths, sd = scan_apps(sd)
    
    
    # global vars for animation
    scroll_factor = 0.0

    prev_text_scroll_position = 0
    text_scroll_position = 0
    text_drawing = True

    prev_icon_scroll_position = 0
    icon_scroll_position = 0
    icon_drawing = True

    # app selector
    app_selector_index = 0
    prev_selector_index = 0

    clock_minute_drawn = -1

    force_redraw_display = True
    
    #starupp sound
    if config['ui_sound']:
        beep.play(('C3',
                   ('F3'),
                   ('A3'),
                   ('F3','A3','C3'),
                   ('F3','A3','C3')),130,config['volume'])
        
#     # init diplsay
#     # icons
#     tft.fill(config['bg_color'], buf_idx=1)
#     tft.show(buf_idx=1)
#     # text
#     tft.fill(config['bg_color'], buf_idx=2)
#     tft.show(buf_idx=2)
#     # scroll bar
#     tft.fill(config['bg_color'], buf_idx=3)
#     tft.show(buf_idx=3)
#     
    while True:
        # ----------------------- check for key presses on the keyboard. Only if they weren't already pressed. --------------------------
        new_keys = kb.get_new_keys()
        if new_keys:
            
            # ~~~~~~ check if the arrow keys are newly pressed ~~~~~
            if "/" in new_keys: # right arrow
                app_selector_index += 1
                
                #animation:
                scroll_factor = 1.0
                text_drawing = True
                icon_drawing = True
                prev_text_scroll_position = 240
                text_scroll_position = 240
                prev_icon_scroll_position = 240
                icon_scroll_position = 240
                
                if config['ui_sound']:
                    beep.play((("C5","D4"),"A4"), 80, config['volume'])

                
            elif "," in new_keys: # left arrow
                app_selector_index -= 1
                
                #animation:
                scroll_factor = -1.0
                text_drawing = True
                icon_drawing = True
                prev_text_scroll_position = -240
                text_scroll_position = -240
                prev_icon_scroll_position = -240
                icon_scroll_position = -240
                
                if config['ui_sound']:
                    beep.play((("B3","C5"),"A4"), 80, config['volume'])
                
            
        
            # ~~~~~~~~~~ check if GO or ENTER are pressed ~~~~~~~~~~
            if "GO" in new_keys or "ENT" in new_keys:
                
                # special "settings" app options will have their own behaviour, otherwise launch the app
                if app_names[app_selector_index] == "UI Sound":
                    
                    if config['ui_sound'] == 0: # currently muted, then unmute
                        config['ui_sound'] = True
                        force_redraw_display = True
                        beep.play(("C4","G4","G4"), 100, config['volume'])
                    else: # currently unmuted, then mute
                        config['ui_sound'] = False
                        force_redraw_display = True
                
                elif app_names[app_selector_index] == "Reload Apps":
                    app_names, app_paths, sd = scan_apps(sd)
                    app_selector_index = 0
                    current_vscsad = 42 # forces scroll animation triggers
                    if config['ui_sound']:
                        beep.play(('F3','A3','C3'),100,config['volume'])
                        
                else: # ~~~~~~~~~~~~~~~~~~~ LAUNCH THE APP! ~~~~~~~~~~~~~~~~~~~~
                    
                    #save config if it has been changed:
                    config.save()
                    
                    # shut off the display
                    tft.fill(0)
                    tft.sleep_mode(True)
                    machine.Pin(38, machine.Pin.OUT).value(0) #backlight off
                    
                    if sd != None:
                        try:
                            sd.deinit()
                        except:
                            print("Tried to deinit SDCard, but failed.")
                            
                    if config['ui_sound']:
                        beep.play(('C4','B4','C5','C5'),100,config['volume'])
                        
                    launch_app(app_paths[app_names[app_selector_index]])

            else: # keyboard shortcuts!
                for key in new_keys:
                    # jump to letter:
                    if len(key) == 1: # filter special keys and repeated presses
                        if key in 'abcdefghijklmnopqrstuvwxyz1234567890':
                            #search for that letter in the app list
                            for idx, name in enumerate(app_names):
                                if name.lower().startswith(key):
                                    #animation:
                                    if app_selector_index > idx:
                                        #scroll_direction = -1
                                        scroll_factor = -1.0
                                        text_drawing = True
                                        icon_drawing = True
                                        prev_text_scroll_position = -240
                                        text_scroll_position = -240
                                        prev_icon_scroll_position = -240
                                        icon_scroll_position = -240
                                        
                                    elif app_selector_index < idx:
                                        scroll_factor = 1.0
                                        text_drawing = True
                                        icon_drawing = True
                                        prev_text_scroll_position = 240
                                        text_scroll_position = 240
                                        prev_icon_scroll_position = 240
                                        icon_scroll_position = 240

                                    # go there!
                                    app_selector_index = idx
                                    if config['ui_sound']:
                                        beep.play(("G3"), 100, config['volume'])
                                    found_key = True
                                    break
        
        
        #wrap around our selector index, in case we go over or under the target amount
        app_selector_index = app_selector_index % len(app_names)
    
        time.sleep_ms(1)
        
        
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Graphics: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        
        # handle scroll_factor
        if scroll_factor != 0 or force_redraw_display:
            if scroll_factor > 0:
                scroll_factor -= min(0.11, abs(scroll_factor))
            else:
                scroll_factor += min(0.11, abs(scroll_factor))
        
        if text_drawing or force_redraw_display:
            scroll_text(tft, scroll_factor, app_names, app_selector_index, prev_selector_index, config)
            if text_scroll_position == 0:
                text_drawing = False
            
        if icon_drawing or force_redraw_display:
            scroll_icon(tft, scroll_factor, app_names, app_selector_index, config, app_paths)
            if icon_scroll_position == 0:
                icon_drawing = False
                
        if time.localtime()[4] != clock_minute_drawn or force_redraw_display:
            clock_minute_drawn = time.localtime()[4]
            draw_status_bar(tft, config, batt)
            
        if app_selector_index != prev_selector_index or force_redraw_display:
            draw_scroll_bar(tft, config, app_selector_index, app_names)



        # reset vars for next loop
        force_redraw_display = False
        prev_selector_index = app_selector_index
        prev_text_scroll_position = text_scroll_position
        prev_icon_scroll_position = icon_scroll_position
        
        
# run the main loop!
main_loop()





