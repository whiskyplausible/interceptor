# OK this is looking much more healthy - menus actually make sense rather than the bizarre shit that was happening before
# So just need to make long press on middle button go back to start of menus. Just set time to measure press and release, and if it is more
# than certain amount, bail back to the main menu
# Generate the menus by loops, not arrays.. maybe?

# Improvements - show which patches actually have content in, also maybe confirm overwriting a patch when saving

"""4 physical buttons available - SAVE, RESTORE, UP + DOWN

*SAVE PROCESS*
- Press Save button
- Use up/down buttons to scroll through MIDI channel numbers (shown on screen)
- Press Save to select MIDI channel
- Use up/down to choose patch number 1-99
- Press Save

*Save via MIDI CC*
MIDI Channel 16
CC#01 - Range 1-99 (saves to MIDI channel 1)
CC#02 - Range 1-99 (saves to MIDI channel 2)
CC#03 etc etc
Up to CC#15

*RESTORE PROCESS*
- Press Restore button
- Use up/down buttons to scroll through MIDI channels
- Press Restore to select MIDI channel
- Use up/down to choose patch number 1-99
- Press Restore

*Restore via MIDI CC*
MIDI Channel 16
CC#16 - Range 1-99 (Restores to MIDI channel 1)
CC#17 - Range 1-99 (Restores to MIDI channel 2)
CC#18 etc etc
Up to CC#30

*Program NOT to save or restore unless the CC command has 'settled' for 1 second.*

The reason for asking the program to pause restoring and saving until it has 'settled' on the command sent is because I will be selecting this patch with a stepped potentiometer on my Beatstep Pro. The Beatstep has a 3 digit LCD so I can program it to also show number between 1 and 99. So I can quickly rotate the knob until i see the right number, then stop turning. Obviously when turned the pot will blast a load of CC patch commands at the Pi.
"""
## Oh. Hai!
## Need to check the ways that other controllers can interfere with the load/save proces.
## Fire off thread to see if a message should be sent after x time

import time
from time import perf_counter
import pickle
import os.path
import threading
import sys
import atexit
from os import path
import traceback
import mido
from gfxhat import touch, lcd, backlight, fonts
from PIL import Image, ImageFont, ImageDraw


PATCH_LOAD = "patch_load"
PATCH_SAVE = "patch_save"

SETTINGS = "settings"
SETTLE_TIME = 2

sent_ccs = [[-1 for x in range(128)] for y in range(16)]
saved_ccs = [[-1 for x in range(128)] for y in range(16)]

loop = True
patch_load = (None, 0, 0, None)

width, height = lcd.dimensions()

# A squarer pixel font
#font = ImageFont.truetype(fonts.BitocraFull, 11)

# A slightly rounded, Ubuntu-inspired version of Bitocra
font = ImageFont.truetype(fonts.BitbuntuFull, 10)

image = Image.new('P', (width, height))

draw = ImageDraw.Draw(image)

current_menu_option = 0

trigger_action = False

current_menu = 0
current_channel = 1
screen_interaction = False
last_button_press = 0
offset_top = 0
last_press_time = 0

class MenuOption:
    def __init__(self, name, action, options=()):
        self.name = name
        self.action = action
        self.options = options
        self.size = font.getsize(name)
        self.width, self.height = self.size

    def trigger(self):
        print("ok i can haz triggers here innit", *self.options)
        self.action(*self.options)


def set_backlight(r, g, b):
    backlight.set_all(r, g, b)
    backlight.show()

def set_menu(menu_number, set_channel=None, patch_no=None):
    global current_menu, current_channel
    current_menu = menu_number
    if set_channel:
        current_channel = set_channel
    if patch_no:
        current_patch = patch_no

def set_channel(channel_number):
    global current_channel
    current_channel = channel_number


def save_patch_menu(patch_no):
    global current_channel
    save_patch(current_channel, patch_no)


menu_options = [None, None, None, None, None, None, None]

menu_options[1] = [[ 'No settings yet',1]]
menu_options[0] = [
    ['Load patch', 'load_patch',''],
    ['Save patch', 'save_patch',''],
    ['Settings', 'settings',''] 
    ]

menu_options[2] = [
    ['Channel 1', 1],
    ['Channel 2', 2],
    ['Channel 3', 3],
    ['Channel 4', 4],
    ['Channel 5', 5],
    ['Channel 6', 6],
    ['Channel 7', 7],
    ['Channel 8', 8],
    ['Channel 9', 9],
    ['Channel 10', 10],
    ['Channel 10', 10],
    ['Channel 10', 10],
    ['Channel 10', 10],
    ['Channel 10', 10],
    ['Channel 10', 10],
    ['Channel 10', 10],
    ]

menu_options[3] = menu_options[2]


menu_options[5] = [
    ['Patch 1', 1],
    ['Patch 2', 2],
    ['Patch 3', 3],
    ['Patch 4', 4],
    ['Patch 5', 5],
    ['Patch 6', 6],
    ['Patch 7', 7],
    ['Patch 8', 8],
    ['Patch 9', 9],
    ['Patch 10', 10],
]

menu_options[6] = menu_options[5]

current_milli_time = lambda: int(round(time.time() * 1000))

def save_patch(channel, patch_no):
    filename = str(channel).zfill(2) + str(patch_no).zfill(2)
    print("saving patch: ", filename)
    with open(filename, 'wb') as f:
        pickle.dump(sent_ccs[channel], f)

    for index, value in enumerate(sent_ccs[channel]):
        if value > -1:
            print("saving: control num:", index, "value: ", value)

def load_patch(channel, patch_no):
    filename = str(channel).zfill(2) + str(patch_no).zfill(2)

    print("loading patch: ", filename)

    if not path.exists(filename):
        print("can't find that patch")
        return False

    file = open(filename, 'rb')
    patch = pickle.load(file)
    file.close()
    for index, value in enumerate(patch):
        if value > -1:
            msg = mido.Message('control_change', channel=channel - 1, control=index, value=value)
            outport.send(msg)
            print("loading: ", msg)
            time.sleep(0.1)
    return True

def check_load_settle():
    global patch_load
    print("starting up settle thread")
    while 1:
        time.sleep(1)
        if patch_load[3] == PATCH_LOAD and perf_counter() - patch_load[0] > SETTLE_TIME:
            print("ok we're good to load now.")
            load_patch(patch_load[1], patch_load[2])
            patch_load = (None, 0, 0, None)

        if patch_load[3] == PATCH_SAVE and perf_counter() - patch_load[0] > SETTLE_TIME:
            print("ok we're good to save now.")
            save_patch(patch_load[1], patch_load[2])
            patch_load = (None, 0, 0, None)


def handler(ch, event):
    global current_menu_option, trigger_action, screen_interaction, current_menu, offset_top, menu_options, current_menu, current_channel, last_press_time
    try:
        backlight_on()
        if event == 'press':
          last_press_time = current_milli_time()	
        if event != 'release':
            return
        if current_milli_time() - last_press_time > 1000 and ch == 4:
            current_menu = 0
            current_menu_option = 0
            offset_top = 0
            draw_menu()
            return
            
        if ch == 3 and current_menu_option > 0:
            current_menu_option -= 1
            offset_top -= 12
            
        if ch == 5:
            if current_menu_option == len(menu_options[current_menu]) - 1:
                current_menu_option = 0
                offset_top = 0
            else: 
                current_menu_option += 1
                offset_top += 12
            
        if ch == 4:
            if current_menu == 0: # We're on the top menu
                offset_top = 0
                if current_menu_option == 0: # Load selected
                    current_menu = 3
                    current_menu_option = 0
                if current_menu_option == 1: # Save selected
                    current_menu = 2
                    current_menu_option = 0                
                if current_menu_option == 2: # Settings selected
                    current_menu = 1
                    current_menu_option = 0
            elif current_menu == 3: # We're in load channel select menu
                offset_top = 0
                current_menu = 6
                current_channel = current_menu_option
                current_menu_option = 0
            elif current_menu == 2: # We're in save channel select menu
                offset_top = 0
                current_menu = 5
                current_channel = current_menu_option
                current_menu_option = 0
            elif current_menu == 5: # We're in the save patch select menu
                save_patch(current_channel+1, current_menu_option)
                modal("Saved")
            elif current_menu == 6: # We're in the load patch select menu
                load_response = load_patch(current_channel+1, current_menu_option)
                modal("Loaded" if load_response else "No patch found")
        draw_menu()
        
    except Exception:
        traceback.print_exc()

for x in range(6):
    touch.set_led(x, 0)
    backlight.set_pixel(x, 255, 255, 255)
    touch.on(x, handler)

backlight.show()

def backlight_on():
    for x in range(6):
        backlight.set_pixel(x, 255, 255, 255)
    backlight.show()
    
def cleanup():
    backlight.set_all(0, 0, 0)
    backlight.show()
    lcd.clear()
    lcd.show()

def modal(message):

    image.paste(0, (0, 0, width, height))
    draw.text((0,0), message, 1, font)
    for x in range(width):
        for y in range(height):
            pixel = image.getpixel((x, y))
            lcd.set_pixel(x, y, pixel)
    lcd.show()
    time.sleep(1)
    draw_menu()

def draw_menu():
    image.paste(0, (0, 0, width, height))
    
    for index in range(len(menu_options[current_menu])):
        x = 10
        y = (index * 12) + (height / 2) - 4 - offset_top
        option = menu_options[current_menu][index]
        if index == current_menu_option:
            draw.rectangle(((x-2, y-1), (width, y+10)), 1)
        draw.text((x, y), option[0], 0 if index == current_menu_option else 1, font)

    w, h = font.getsize('>')
    draw.text((0, (height - h) / 2), '>', 1, font)

    for x in range(width):
        for y in range(height):
            pixel = image.getpixel((x, y))
            lcd.set_pixel(x, y, pixel)

    lcd.show()

def backlight_thread():
    global last_press_time
    while 1:
        if current_milli_time() - last_press_time > 10000:
            backlight.set_all(0, 0, 0)
            backlight.show()
        time.sleep(1)


def screen_thread():
    global image, trigger_action, current_menu_option, menu_options, font, draw, lcd, screen_interaction
    print("Starting screen thread.")
    try:
        offset_top = 0
        screen_interaction = True
        while True:

            if screen_interaction:

                if trigger_action:
                    menu_options[current_menu][current_menu_option].trigger()
                    trigger_action = False

                for index in range(len(menu_options[current_menu])):
                    if index == current_menu_option:
                        break
                    offset_top += 12
            time.sleep(0.5)

    except Exception:
        traceback.print_exc()
    #    cleanup()

atexit.register(cleanup)

thread1 = threading.Thread(target = check_load_settle)
thread1.start()

thread2 = threading.Thread(target = backlight_thread)
thread2.start()

draw_menu()

if not path.exists("interceptor.cfg"):
    in_names = mido.get_input_names()
    out_names = mido.get_output_names()
    print("can't find config file")
    print("Please select your MIDI input from the list:")
    for index, value in enumerate(in_names):
        print(index + 1,":", value)
    in_sel = input("Port: ")

    inport = mido.open_input(in_names[int(in_sel) - 1])

    print("Please select your MIDI output from the list:")
    for index, value in enumerate(out_names):
        print(index + 1,":", value)
    out_sel = input("Port: ")
    outport = mido.open_output(out_names[int(out_sel) - 1])

    inp = input("Save these for next time (Y/n):")
    if inp.upper() != "N":
        config = {
            "midiInput":  in_names[int(in_sel) - 1],
            "midiOutput": out_names[int(out_sel) - 1]
        }
        with open("interceptor.cfg", 'wb') as f:
            pickle.dump(config, f)
        print("config saved: ", config)
else:
    print("found config file.")
    file = open("interceptor.cfg", 'rb')
    config = pickle.load(file)
    file.close()
    print(config)
    inport = mido.open_input(config["midiInput"])
    outport = mido.open_output(config["midiOutput"])
    print("midi ports set up from config file")

print("starting up")

while loop:
    msg = inport.receive()
    outport.send(msg)
    print("received: ",msg)

    if msg.type == 'control_change':

        if msg.channel == 15 and  msg.value < 100:

            # This means they want to save current patch
            if msg.control < 16: 
                print("setting up for saving in couple of seconds")
                patch_load = (perf_counter(), msg.control, msg.value, PATCH_SAVE)

            # This means they want to load a patch
            if msg.control > 15 and msg.control < 33:
                print("setting up for loading in couple of seconds")
                patch_load = (perf_counter(), msg.control - 15, msg.value, PATCH_LOAD)

        if msg.channel < 15:
            sent_ccs[msg.channel + 1][msg.control] = msg.value
