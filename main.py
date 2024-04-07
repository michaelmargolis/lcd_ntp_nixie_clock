import time
from machine import Pin,PWM

import settings
import display
import ds3231
import leds

import wifi, secrets
import ntptime
import time_utils
from button import Button

from webserver import my_HTTPserver

import micropython # for memory diags only

micropython.alloc_emergency_exception_buf(100)  # Allocate buffer for interrupt exceptions

"""
WiFi/NTP code connects to router using credentials in the secrets.py file
If connected, time_utils module attempts to set the machine.RTC using NTP time
See wifi and time_utils modules for more info  
"""
net = wifi.wifi(10)


#=======================================================================
# Helper Functions
#=======================================================================

  
def alarm_callback(caller, is_alarm_toggle):
    # toggle alarm on/off if is_alarm_toggle, else turn off buzzer if on
    # mode button held for more than 2 seconds sets is_alarm_toggle True
    if is_alarm_toggle:
        if settings.get_setting("alarm_on") == "No":
             settings.set_setting("alarm_on", 'Yes')
        else:
             settings.set_setting("alarm_on", 'No')
        print("toggled alarm state to {}".format(settings.settings["alarm_on"]))
        clock.update_info_text() 
    clock.alarm.reset_trigger() 
    print("clock trigger reset")

def button_callback(caller, is_long_press):
    if caller.name == "toggle_seconds":
        if settings.get_setting("show_secs") == "No":
            settings.set_setting("show_secs", "Yes")
        else:
            settings.set_setting("show_secs", "No")
    elif caller.name == "sequence_font":
        active_font = settings.get_setting("active_font")    
        if active_font == "nixie":
            settings.set_setting("active_font", "dot")
        elif active_font =="dot":
            settings.set_setting("active_font", "7seg")
        elif active_font =="7seg":
            settings.set_setting("active_font", "nixie")
    clock.update_display_state()       
    # in this version, settings.save_settings() is not called
    
#====================================================================
# Alarm class
#====================================================================
class Alarm:
    def __init__(self, leds, get_setting):
        self.leds = leds
        self.get_setting = get_setting
        self.buzzer = PWM(Pin(settings.BUZZER_PIN, Pin.OUT))
        self.buzzer.duty_u16(0)
        self.triggered = False

    def check(self, hour, minute, sec):
        """sounds buzzer if given time matches the alarm time and if the trigger is enabled."""
        alarm_enabled = self.get_setting("alarm_on")
        alarm_hour = int(self.get_setting("alarm_hour"))
        alarm_min = int(self.get_setting("alarm_min"))
        # print(alarm_enabled, alarm_hour,hour, alarm_min,minute,sec)
        if alarm_enabled == 'Yes' and alarm_hour == hour and alarm_min == minute and sec == 0:
            self.triggered = True
        if self.triggered:
            if (sec % 2) == 0:
                self.leds.rgb_strip.fill((255,255,255))
            else:
                leds.rgb_strip.fill((0,0,0))
            self.leds.rgb_strip.write()
            
            self.buzzer.duty_u16(32768)
            for i in range(0,4):
                self.buzzer.freq(1500)
                time.sleep(0.05)
                self.buzzer.freq(2400)
                time.sleep(0.05)
            self.buzzer.duty_u16(0)             
            if alarm_min != minute:
                self.triggered  = False # turn off alarm after one minute
        
    def reset_trigger(self):
        # Stop the alarm
        self.buzzer.duty_u16(0)
        leds.set_color(settings.get_setting("led_color"), int(settings.get_setting("led_brightness")))
        self.triggered  = False
        
       

#====================================================================
# Clock class
#====================================================================
class Clock():
    tick = True # static flag to indcated 1hz isr trigger
    
    def __init__(self, lcd, leds, get_setting):
        self.lcd = lcd
        self.get_setting = get_setting # accesser for values in the settings module
        self.alarm = Alarm(leds, get_setting)
        self.active_font = None
        self.info_text = None # text on digit 5 when not showing seconds
        self.digits_cache = [None]*6
        self.init_rtc()
        
    def init_rtc(self):
        self.rtc_ds3231 = ds3231.DS3231(add = 0x68)
        trim = int(self.get_setting("adjust_timing"))
        print("setting rtc trim to {}".format(trim))
        self.rtc_ds3231.Set_Timing(trim)
        # Set up the handler to recieve a regular interrupt on the 1Hz output from the DS3231
        rtc_1Hz_pin   = Pin(settings.RTC_1HZ_PIN, Pin.IN)
        rtc_1Hz_pin.irq(trigger=Pin.IRQ_RISING, handler=self.rtc_1hz_isr)
     
  
    def rtc_setter(self, dt):
        # syncs ds3231 with the given time as python datetime tuple
        self.rtc_ds3231.set_localtime(dt)
        
    @staticmethod
    def rtc_1hz_isr(pin):
        Clock.tick = True
  
    def show_digit_if_changed(self, digit, pos):
        if digit != self.digits_cache[pos]:            
            self.lcd.select_digit(pos)
            if digit is None:
                self.lcd.fill(self.lcd.black)
                self.digits_cache[pos] = None
            else:
                self.lcd.display_digit(digit)
                self.digits_cache[pos] = digit       
            self.lcd.show()            

    
    def extract_digits(self, value):
        # Assumes value is always two digits
        return [value // 10, value % 10]

    def show_time(self, hr, mins, sec):
        digits = self.extract_digits(hr) + self.extract_digits(mins) + self.extract_digits(sec)
        if self.get_setting("show_secs") == 'No':              
            self.show_digit_if_changed(digits[3], 4)               
            # Show tens of minute
            self.show_digit_if_changed(digits[2], 3)
            # show blinking colon
            self.lcd.show_colon(2, digits[5]%2) # on every other second
            self.digits_cache[2] = None # force digit display if changing to show_secs
            # show hour. Suppress leading zero if in 12 hour mode
            self.show_digit_if_changed(digits[1], 1)
            
            if self.get_setting("24_hour")=="24" or hr > 9:
                self.show_digit_if_changed(digits[0], 0)
            else:
                self.show_digit_if_changed(None, 0)
            self.update_info_text()       
      
        else:
            # 6-digit mode : display hours, minutes and seconds
            for idx, digit in enumerate(digits):
                self.show_digit_if_changed(digit, idx)
     
    def update_info_text(self):
        info_text = ""
        if self.get_setting("show_date") == 'Yes':
            month, day = self.rtc_ds3231.localtime()[1:3]
            month_str = time_utils.months[month]
            info_text += "{} {} ".format(month_str, day)
        if self.get_setting("alarm_on") == 'Yes':
            info_text += " Alarm {0}:{1:02d}".format(int(self.get_setting("alarm_hour")),
                       int(self.get_setting("alarm_min")))
        ##else:
        ##    info_text += ("Alarm OFF")
        # only update if changed
        if info_text != self.info_text:
            self.lcd.select_digit(5) 
            self.lcd.display_text(info_text)
            self.info_text = info_text
  
    def update_display_state(self):
        self.lcd.set_brightness(int(self.get_setting("brightness")))
        if self.active_font != self.get_setting("active_font"):
            # print("old font",self.active_font, "->", self.get_setting("active_font"))
            self.digits_cache = [None]*6
        self.active_font = self.get_setting("active_font")
        hex_color = self.get_setting(self.active_font)
        self.lcd.set_font(self.active_font, hex_color)
        self.info_text = None
        self.update_info_text()
 
    def show_ip_addr(self, addr, wait_time):
        octets= ["This IP Addr",] + addr.split(".")
        for i in range(len(octets)):
            self.lcd.select_digit(i) 
            self.lcd.display_text(octets[i])
        time.sleep(wait_time)
    
    def service(self):
        # call this once per tick
        hr, mins, sec = self.rtc_ds3231.localtime()[3:6]
        self.show_time(hr, mins, sec)
        self.alarm.check(hr, mins, sec)
     
def web_callback(data):
    # update settings with k,v pairs in the given dictionary
    changed = 0
    for k,v in data.items():
        if v[:3] == '%23': # convert html representaion of # symbol
            v = '#' + v[3:]
        if settings.settings[k] != v:
            changed += 1
            print('settings change for', k, 'old val = ', settings.settings[k], 'new val' ,v)
            settings.settings.update({k:v})
    if changed:
        print("updated {} items".format(changed))        
        settings.save_settings()
        leds.set_color(settings.get_setting("led_color"), int(settings.get_setting("led_brightness")))
        clock.update_display_state()
    
    micropython.mem_info()         
    # print('after post', settings.settings)
    
#=======================================================================
# Main Body
#=======================================================================

settings.load_settings()

active_font = settings.get_setting("active_font")
hex_color = settings.get_setting(active_font)
lcd = display.Display(active_font, hex_color)
lcd.clear()
leds.set_color(settings.get_setting("led_color"), int(settings.get_setting("led_brightness")))

t_utils = time_utils.Time_utils(int(settings.get_setting("utc_offset")))

clock = Clock(lcd, leds, settings.get_setting)

Button.append("alarm", settings.MODE_PIN , pull=None, callback=alarm_callback, long_press_time=2000)  # Set long press dur in ms)
Button.append("sequence_font", settings.LEFT_PIN , pull=None, callback=button_callback)
Button.append("toggle_seconds", settings.RIGHT_PIN , pull=None, callback=button_callback) 

#===================================================================
# The main control loop starts here
#===================================================================

net.set_hostname('nixieclock') # todo needs testing

for attempts in range(2):
    lcd.set_brightness(100) # max brightness while showing startup status
    lcd.select_digit(5) 
    lcd.display_text("Wait for WiFi")
    try:
        status = net.connect(secrets.SSID, secrets.PASSWORD)
        if net.status_text(status) == 'OK':
            if net.is_connected():
                lcd.display_text("Net OK")
                if t_utils.check_sync(clock.rtc_setter):
                    lcd.display_text("Synced with NTP")
                else:
                    lcd.display_text("NTP not Avail")
                webserver = my_HTTPserver(settings, web_callback)
                clock.show_ip_addr(net.this_ip, 4) # show ip address on clock for 4 seconds at startup
                break
        else:
            lcd.display_text(net.status_text(status)) # show error if not connected
            time.sleep(1)
    except Exception as e:
        print(e)
            
    
if not net.is_connected():
    lcd.display_text("Net not Avail")
    print("ds3231", clock.rtc_ds3231.localtime())
    time.sleep(2) # just to show the above text 

   

micropython.mem_info() # only for initial memory tests 

while True:
    if Clock.tick:
        if net.is_connected():
            if t_utils.check_sync(clock.rtc_setter):
                print("clock synced")
        clock.service() # update display and check alarm
        Clock.tick = False
    if net.is_connected():    
        webserver.listen() # check and handle web UI request 
    Button.service() # handle any pressed buttons
    time.sleep(0.05)  # Polling interval
    
# The end.


