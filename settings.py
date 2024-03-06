#=============================================================
#=============================================================
#=============================================================
# Settings and global variables, shared by all python modules
#=============================================================
#=============================================================
#=============================================================
from collections import OrderedDict
import json

# GPIO Pin Numbers for LCD
RST_PIN    = 12
CLK_PIN    = 10
DIN_PIN    = 11
DC_PIN     = 8
CS1_PIN    = 2
CS2_PIN    = 3
CS3_PIN    = 4
BL_PIN     = 13

# GPIO pins for push buttons
MODE_PIN  = 17
LEFT_PIN  = 16
RIGHT_PIN = 15

# Other GPIO Pins
BUZZER_PIN = 14
NEOPIXEL_PIN = 22
RTC_1HZ_PIN = 18


# Global Variables

settings = {
    "alarm_on": "No",
    "alarm_hour": '6',
    "alarm_min": '30',
    "active_font": "nixie",
    "nixie": "#ff7b00",
    "dot": "#ff0000",
    "7seg": "#00ffff",
    "brightness" : "50",
    "led_color": "#ff7b00",
    "led_alarm_color": "#cccccc",
    "24_hour" : "24",
    "show_secs" : "No",
    "show_date" : "No",
    "utc_offset" : "0",
    "dst_mode": "auto_eu",
    "adjust_timing" : "128"
}


# ordered dictionary to preserve dropdown sequence
dst_options = OrderedDict([ 
    ("dst_off", "DST Off"),
    ("dst_on", "DST On"),
    ("auto_eu", "Auto EU"),
    ("auto_na", "Auto NA")
    ])

"""
tags are used to define the browser user interface
first touple element is key to settings dictionary
second element is 'R' if radio button,  'T' if text field
'F' if font selection, '-' if blank line seperator
"""

tags = ( 
            ('alarm_on', 'R', 'Alarm Enabled', 'Yes', 'No'),  
            ('alarm_hour', 'N', 'Alarm hour', 1, 23),
            ('alarm_min', 'N', 'Alarm minute', 0, 59),
            ('', '-'),
            ('active_font', 'F','Font', 'nixie:Nixie', 'dot:Dot Matrix', '7seg:7 Segment'),
            ('brightness', 'N','Brightness %', 1, 100),
            ('', '-'),
            ('led_color', 'L','LED color'),
            ('', '-'),
            ('24_hour', 'R','Hours Format', '12', '24'),
            ('show_secs', 'R','Show Seconds', 'Yes', 'No'),
            ('show_date', 'R','Show Date', 'Yes', 'No'),
            ('utc_offset', 'N', 'Offset from UTC', -12, 12),
            ('dst_mode', 'D', 'DST Mode', dst_options),
            # ('', '-'),
            # ('adjust_timing', 'N', 'Trim timing', 0, 255)
       )


    
tick = True


#==============================================================================
#==============================================================================
#==============================================================================
# Functions to Read and write the Settings File "settings.json" on eeprom
#==============================================================================
#==============================================================================
#==============================================================================

# Save all settings to "disk".
def save_settings():
    print("saving settings")
    with open("settings.json", "w") as f:
        json.dump(settings, f)
 
            
# Load all settings from "disk"
def load_settings():
    global settings
    try:
        with open("settings.json", "r") as f:
            settings = json.load(f)
    except:
        print("Unable to load settings.json. Creating new file")
        print(settings)
        save_settings()

# Retrieve a single setting value from memory
def get_setting(key):
    try:
        v = settings[key]  
        return v
    except KeyError:
        print("Key '{}' not found in settings. Delete file settings.json and try again".format(key))

# set a single setting value
def set_setting(key, value):
    try:
        settings[key] = value     
    except KeyError:
        print("Key '{}' not found in settings, unable to save".format(key))
    


# Update a single setting value in memory and "disk"
def save_setting(key,value):
    if key in settings:
        settings[key] = value
        save_settings()
    else:
        raise Exception("Key '" + key + "' not found in settings. Delete file settings.json and try again")

 
