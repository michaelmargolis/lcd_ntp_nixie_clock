# MemNet

import os
import socket
import network
import time
import gc
    
class wifi(object):
    def __init__(self, timeout=10):
        self.timeout = timeout
        self.this_ip = None
        self.wlan = None
            
    def connect(self, ssid, password):
        #returns error status
        max_wait = self.timeout
        try:           
            self.wlan = network.WLAN(network.STA_IF)
            self.wlan.active(True)
            self.wlan.connect(ssid, password)
            print("Connecting to {}".format(ssid))
            # Wait for connect or fail

            while max_wait > 0:
                if self.wlan.status() < 0 or self.wlan.status() >= 3:
                    break
                max_wait -= 1
                print('waiting for connection...')
                time.sleep(1)

            # Handle connection error
            status = self.wlan.status()
            if status != 3:
                print('network connection failed, err =', status)
                return status
            else:
                status = self.wlan.ifconfig()
                self.this_ip = status[0]
                print('Connected: Pico IP is {}'.format(self.this_ip))
                gc.collect()
                time.sleep(.5)
                return self.wlan.status() # should be network.STAT_GOT_IP
         
        except Exception as e:
            print(e)
        
        return self.wlan.status()

    def is_connected(self):
        return self.wlan.isconnected()

    def set_hostname(self, hostname='NixieClock'):
        network.hostname(hostname)
        
    def status_text(self, status_code):
        status_messages = {
            network.STAT_IDLE: "Idle",
            network.STAT_CONNECTING: "Con ?",
            network.STAT_WRONG_PASSWORD: "Wrong PW",
            network.STAT_NO_AP_FOUND: "AP not found",
            network.STAT_CONNECT_FAIL: "Conn fail",
            network.STAT_GOT_IP: "OK",
        }
        return status_messages.get(status_code, "Unkn {}".format(status_code))






