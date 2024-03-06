from machine import Pin
import time

class Button:
    _buttons = []
    
    @staticmethod
    def append(name, pin_number, debounce=50, pull=Pin.PULL_UP, callback=None, long_press_time=2000, prevent_multiple=False):
        Button._buttons.append(Button(name, pin_number, debounce, pull, callback, long_press_time, prevent_multiple))
   
    @staticmethod
    def service():
        for button in  Button._buttons:
            button.check()

    def __init__(self, name, pin_number, debounce=50, pull=Pin.PULL_UP, callback=None, long_press_time=2000, prevent_multiple=False):
        self.name = name # a brief text descripter that can identify this button when shared callbacks are used 
        if pull == None:
            self.pin = Pin(pin_number, Pin.IN)
            self.active_low = True
        else:    
            self.pin = Pin(pin_number, Pin.IN, pull)
            self.active_low = pull == Pin.PULL_UP
        self.debounce = debounce / 1000.0  # Convert to seconds
        self.long_press_duration = long_press_time / 1000.0  # Convert to seconds
        self.callback = callback
        self.prevent_multiple = prevent_multiple
        self.debounce_active = False
        self.long_press_detected = False
        self.short_press_called = False  # Track if short press callback has been called
        # print('{} button on pin {}'.format(name, pin_number))

    def check(self):
        # print(self.name, self.active_low, self.pin.value() == self.active_low)
        now = time.time()
        if self.pin.value() == self.active_low:
            if not self.debounce_active:
                self.press_start_time = now
                self.debounce_active = True
                if not self.prevent_multiple:
                    self.short_press_called = False  # Reset short press call tracker
                    self.long_press_detected = False  # Reset long press detection
            elif now - self.press_start_time > self.debounce:
                # print(self.name, now - self.press_start_time)
                if not self.short_press_called and now - self.press_start_time < self.long_press_duration:
                    # print(self.name, self.active_low, self.pin.value() == self.active_low)
                    self.short_press_called = True
                    if self.callback: self.callback(self, False)  # Short press callback
                elif now - self.press_start_time > self.long_press_duration and not self.long_press_detected:
                    self.long_press_detected = True
                    if self.callback: self.callback(self, True)  # Long press callback
        else:
            self.debounce_active = False
            if self.prevent_multiple:
                self.long_press_detected = False
                self.short_press_called = False  # Ensure short press can be detected again after release

"""
# Example usage
def button_callback(caller, is_long_press):
    # Custom action based on the press duration
    print("{} button custom action triggered by {} button press.".format(caller.name, 'long' if is_long_press else 'short' ))

# GPIO pins for push buttons
MODE_PIN  = 17
LEFT_PIN  = 15
RIGHT_PIN = 16


Button.append("Mode", MODE_PIN , pull=None, callback=button_callback, long_press_time=2000)
Button.append("Left", LEFT_PIN , pull=None, callback=button_callback)
Button.append("Right", RIGHT_PIN , pull=None, callback=button_callback)

# Main loop for Button.append 
while True:
    Button.service()
    time.sleep(0.1)  # Polling interval
  
    
# Example usage with GPIO pin number (e.g., 0 for D0 on ESP8266) and the callback
mode_button = Button("Mode", MODE_PIN , pull=None, callback=button_callback, long_press_time=2000)  # Set long press dur in ms
left_button = Button("Left", LEFT_PIN , pull=None, callback=button_callback) 
right_button = Button("Right", RIGHT_PIN , pull=None, callback=button_callback)

# Main loop for explicit instantiation
while True:
    mode_button.check()
    left_button.check()
    right_button.check()
    time.sleep(0.1)  # Polling interval
"""