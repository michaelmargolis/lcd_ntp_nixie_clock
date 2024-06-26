# lcd_ntp_nixie_clock
Pseudo Nixie LCD clock in Micropython for the Waveshare kit and Pi Pico W

This project is based on the Pseudo Nixie clock by Gary Bleads: https://github.com/g0hjq/lcd_nixie_clock

The version here has automaic date and time setting synchronized with NTP and a web browser user interface to configure clock settings. 
A Pi Pico W is required. If you want to use the clock with a non WiFI pico or prefer a more retro experience then Gary's repo is the place to go.

There are many changes in this fork so treat this version as early beta. Please raise an issue if you find a problem.
 
![image](https://github.com/g0hjq/lcd_nixie_clock/assets/37076748/554df180-edf5-486d-a488-68c63047eff1)


## Features inherited from Gary's code
- Shows the time in 12 or 24 hour format
- Shows time in on the LCDs in the style of Nixie tubes. Other display types can be selected
- Shows Hours, minutes and seconds, or Hours, Minutes and Alarm status
- Alarm sounds the buzzer and flashes the LED neopixels
- Controlable brightness

## Features new to this version
- Time and date set from NTP server synchronized at startup and once per hour
- The time can be autmatically adjusted for Daylight Savings Time for users in Europe or North America
- Font and RGB colours can be set to any 16 bit value
- Optionally shows the month and day in the rightmost digit (in hr/min mode) 
- Web browser interface for display settings.

## Limitations
- Due to the limited amount of eeprom in the Pi Pico, only one set of font files may be loaded at any one time, however alternative .raw font files may be created and uploaded via Thonny. Additional 7-segment and dot-matrix like fonts are generated by the software.
- The temperature and humidity from the BME280 sensor are not displayed. The sensor is on the PCB, inside an unventilated case, so is never going to be able to give accurate readings.
- The logic for determining start and and of DST in regions other than EU/Uk and North America have not been implimented. Contributions for other reagions are welcome and will be added to the repo.

# Disclaimer
THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


## Font Files
The ten images for the digits 0 to 9 are stored in .raw files. This is explained here: https://www.penguintutor.com/programming/picodisplayanimations . You can create your own set of font files as follows:
- Create a set of 10 image files at resolution 240 x 135 pixels.
- Rotate the images anticlockwise 90 degrees and save as .png files 0.png to 9.png
- Run the conversion program animation_convert.py. This will produce files 0.raw to 9.raw
- Use thonny to upload the .raw files to the root directory of the pi pico

## Other Fonts
Additional 7-segment and dot-matrix like fonts in various colurs are generated by the Python code in display.py

![PXL_20230707_190128832](https://github.com/g0hjq/lcd_nixie_clock/assets/37076748/7784f8dd-b2f1-4781-a3c2-daf8a86a8d97)

![PXL_20230707_184316827](https://github.com/g0hjq/lcd_nixie_clock/assets/37076748/b2fb8b04-7def-455a-abbd-d3ba16caa3c3)

## Core Files
- main.py : The main program file in Micropython
- ds3231.py : Driver for the DS3231 real time clock chip
- display.py : LCD driver for the Waveshare ST7789 1.14" 240x134 pixel LCD. Also includes a 5x8 ASCII text font which is shown magnified 4x
- leds.py : Controls the RGB neopixel LEDs behind each digit. Consider adding more effects and/or animations, maybe running as a seperate thread in the second core.
- setings.py : Saves and retrieves the alarm time, display mode and other setting values in the settings.json file below.
- settings.json : Contains the setting values. This file is written to every time one of the clock settings is changed. settings.json will be created automatically if it does not exist

## Runtime font files
- 0.raw, 1.raw etc through 9.raw

## Additional files used in this version
- wifi.py and secrets.py:  your typical PicoW wifi code
- webserver.py: provides a browser user interface for clock settings.
- nixieclock.jpg: a picture of the clock displayed by the webserver, located in the images folder
- ntptime.py:  returns UTC time using the standard python datetime tuple
- time_utils: code for syncing with the NTP code. It also has DST code that returns True if the current time is DST in the given region. The North America logic has not been tested.
- button.py: provides an interface consistent with the polling interface of the other modules


## Installation

Use the Thonny IDE to upload the core, runtime font and additional files listed above to the root directory of the Raspberry Pi Pico.
Do not copy the fonts directory or its contents. 

>[!WARNING]
> Always disconnect the clock's USB power lead whenever using the Pi Pico USB cable to connect to a computer or other power source.
>The clock can be run using either the Pico USB cable or the POWER USB C connecter on the clock, but don't use both at the same time.

Open secrets.py in the Thonny editor and modify the SSID and PASSWORD to match the credentials needed for the WiFI access point you want the clock to connect to.
Open main.py in Thonny and press RUN. 

When running from the POWER USB connector, the clock will start automatically when powered on.


## Clock Buttons
- A short press on the mode button clears the currently active alarm and a long press (longer than two seconds) on the mode button will toggle the recurring alarm setting on or off. 
- Short press on the right button to toggle the display of seconds on or off
- Short press on the left button cycles through each of the fonts, each press selects another font.

## Clock Configuration
- Configuration of the clock settings is achieved through a web browser. Enter the IP address displayed when the clock is powered up into your browser's address bar. 
![browser ui](https://github.com/michaelmargolis/lcd_ntp_nixie_clock/blob/main/docs/browser_ui.jpg)
- The clock picture may take a while to load, a future development may be able to speed this up.

