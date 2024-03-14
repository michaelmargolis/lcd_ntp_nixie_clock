""" 
  webserver.py  Copyright (c) 2024 Michael Margolis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED
"""


import socket
import os
import errno

try:
    from micropython import const
    upython = True
except ImportError:
    const = lambda x : x
    
SOCK_TIMEOUT = const(0)

html_start = b"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body>
   <style>
    *{font-family: Verdana;}
    h1 {font-size: 30px;padding-left: 12px;}
    table {border: 1px solid grey; border-collapse: collapse;}
    td, th { padding-left: 8px; padding-right: 8px; padding-top: 4px;padding-bottom: 4px;}
    .h-line {border-bottom: 1px solid grey;}
    </style>
<font size="4">
<table>
<tr><img src="images/nixieclock.jpg" /></tr>
<tr><h1>Nixie Clock Settings</h1>  </tr>
<tr><td colspan="3">&zwnj;</td></tr>

<form action="/" method="POST">
"""

html_end = b"""  
  <br>
  <input type="submit">
</form>

</body>
</html>
"""

content_types = dict(
    html='text/html',
    css='text/css',
    js='application/javascript',
    json='application/json',
    jpg='image/jpeg',
    ico='image/x-icon',
    default='text/plain',
    )

READ_BUF_LEN = 512
PAGE_BUF_LEN = 5120 # max bytes for an html page

page_buf = bytearray(PAGE_BUF_LEN)

class my_HTTPserver(object):
    def __init__(self, settings, cfg_callback):
        self.cfg = settings.settings
        self.cfg_tags = settings.tags
        self.dst_options = settings.dst_options
        self.update_func = cfg_callback
        # Open socket
        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if SOCK_TIMEOUT == 0:
            self.sock.setblocking(False)
        else:    
            self.sock.settimeout(SOCK_TIMEOUT) 
        self.sock.bind(addr)
        self.send_array = bytearray(READ_BUF_LEN)
        self.sock.listen(1)
        print('Ready to listen on', addr)

    def listen(self):
        client = None
        try:
            client, addr = self.sock.accept()

        except OSError as e:
            if e.args[0] == errno.EAGAIN or e.args[0] == errno.EWOULDBLOCK:
                pass
            elif 'timed out' in e.args:
                pass
            else:
                print('in listen', e)
                if cl:
                    cl.close()
                    print('connection closed')
        else:
            # A client has connected
            print(f"Connection from {addr}")
            # Handle the client connection
            client.setblocking(True)  # Optionally set the client socket to blocking for simplicity
            request = client.recv(2048)
            r = str(request)
            if len(r) > 0:
                if r[:6] == "b'GET ":
                    self.process_get(r, client)
                elif r[:6] == "b'POST":
                    self.process_post(r, client)
                else:
                    print("unhandled request", r[:6])
                    return            
            client.close()
        

    def append_to_page_buf(self, byte_arrays):
        global page_buf
        for i in range(len(page_buf)):
            page_buf[i] = 0
        # page_buf[:] = bytes(len(page_buf)) # clear the buffer    
        current_size = 0 
        for byte_array in byte_arrays:
            # Calculate space left in the buffer
            space_left = PAGE_BUF_LEN - current_size
            if space_left <= 0:
                raise("Web Page Buffer full")

            # If the byte_array fits into the space left, append it entirely
            if len(byte_array) <= space_left:
                page_buf[current_size:current_size + len(byte_array)] = byte_array
                current_size += len(byte_array)
            # If the byte_array does not fit, append only the part that fits
            else:
                page_buf[current_size:PAGE_BUF_LEN] = byte_array[:space_left]
                current_size = PAGE_BUF_LEN
                raise("Web page buffer full after partial append.")
        return page_buf    
    
    def send_page(self, cl, page):
        page = self.append_to_page_buf((html_start,self.get_input_tags(),html_end))
        cl.send(b'HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        cl.send(page)
        
    def process_get(self, response, cl):
      
        r = response[:32].split(' ',3)
        if r[1][1:7] == 'images':
            fname = r[1][1:]
            self.send_file(cl, fname)
                 
        elif r[2][:4] == 'HTTP':
            page = self.append_to_page_buf((html_start,self.get_input_tags(),html_end))
            self.send_page(cl, page)
            
        elif len(r) > 0: 
            print('unhandled:', r)      
     
    def process_post(self, request, cl):
        start = request.find('Referer')
        start = request.find('\\r\\n\\r\\n', start)+ 8
        end = request.find('\\r\\n', start)
        fields = request[start:end]
        fields = fields.split('@')
        fields = fields[0].split('&')
        #print(fields, fields[-1])
        d = {}
        for item in fields:
            if '=' in item:
                k,v = item.split("=")
                d[k] = v
    
        # d = dict(item.split("=") for item in fields)
        if 'asFont' in d:
            if d['asFont'] == 'on':
                font = d['active_font'] #set color to font if selected 
                d['led_color'] = d[font]
            del d['asFont'] # don't send the asFont key
        self.update_func(d) # update config
        page = self.append_to_page_buf((html_start,self.get_input_tags(),html_end))
        self.send_page(cl, page)
    
    def send_file(self, cl, filename, binary=True):
        content_type = content_types.get(filename.split('.')[-1], content_types['default'])
        file_size = os.stat(filename)[6]

        # Prepare the HTTP response headers
        headers = [
            b"HTTP/1.1 200 OK\r\n",
            "Content-Type: {}\r\n".format(content_type).encode(),
            "Content-Length: {}\r\n\r\n".format(file_size).encode()
        ]

        # Send headers in one go
        cl.send(b"".join(headers))

        try:
            with open(filename, 'rb' if binary else 'r') as f:
                while True:
                    data = f.read(READ_BUF_LEN)  # Ensure READ_BUF_LEN is defined elsewhere
                    if not data:
                        break
                    cl.send(data)
        except OSError as e:
            if e.args[0] == errno.ETIMEDOUT:
                pass
            elif e.args[0] == errno.ENOENT:
                raise HttpError(cl, 404, "File Not Found")
            else:
                raise
            
    def form_text_input(self, id, text, min, max, value):
        minmax = '<td>({} to {})</td>'.format(min, max)
        line = '<tr><td><label for="{}">{}:</label></td><td><input type="text" id="{}" \
                name="{}" min="{}" max="{}" value="{}" size="2"></td>{}</tr>'. \
                format(id, text, id, id, min, max, value, minmax)
        return line

    def form_radio_input(self, id, text, selected, values):      
        line = '<tr><td><label>{}:</label></td>'.format(text)        
        for i in range(len(values)):
            if values[i] == selected:
                chked = 'checked="checked"'
            else:
                chked = ''
            line += '<td><input type="radio" name="{}" value="{}" {} id={}>'.format(id, values[i], chked, id)
            line += '<label for="{}">{}</label></td>'.format(values[i], values[i])    
        line += '</tr>'
        return line
    
    def form_font_input(self, active_id, heading, font_info ):
        active = self.cfg[active_id]
        line = '<tr><td><label>{}</label></td><td><label>Colour</label></td></tr>'.format(heading)
        for f in font_info:
            font = f.split(':') # format is id:display_name
            id = font[0]
            color = self.cfg[id]
            text = font[1]
            color_id = id
            if id == self.cfg[active_id]:
                checked = 'checked="checked"'
            else:
                checked = ''                
            line+= '''<tr><td><input type="radio" name="active_font" value="{}" {} id={}>
                    <label for="{}">{}</label></td>
                    <td><input type="color" id="{}" name="{}" value="{}"/>
                    <label for="color_id">{}</label></td></tr><tr>''' \
                    .format(id, checked, id, id, text, color_id, color_id, color, color)
                
        return line    
            
    def form_led_color_select(self, id, heading):
        # print(id, self.cfg[id])
        color = self.cfg[id]
        # print("led color in cfg is ", color)
        line = '''<tr><td>{}</td><td><input type="color" name="{}" id="{}" value="{}"></td><td>
                <input type="checkbox" name="asFont" id="asFontCb">As Font</td> </tr>''' \
                .format(heading, id, id, color)
        return line
    
    def form_dropdown(self, id, heading, options, selected):
        line = '<tr><td><label>{}</label></td><td><select id="{}" name="{}">'.format(heading, id, id)
        for key in options:
            option_text = options[key]
            if key == selected:
                line += '<option value="{}" selected="selected">{}</option>'.format(key, option_text)
            else:
                line += '<option value="{}">{}</option>'.format(key, option_text )
        line += '</select></td></tr>'
        return line
    
    def get_input_tags(self):
        fields = []
        for idx, tag in enumerate(self.cfg_tags):
            # print(tag)
            if tag[1] == 'N': # numeric textbox
               id, type, text, min, max = tag
               fields.append(self.form_text_input(id, text, min, max, self.cfg[id]))
            elif tag[1] == 'R': # radio buttons
                id, type, text = tag[:3]
                values = tag[3:]
                fields.append(self.form_radio_input(id, text, self.cfg[id], values))
            elif tag[1] == 'F': # font group
                id, type, heading = tag[:3]
                fonts = tag[3:]
                fields.append(self.form_font_input(id, heading, fonts))
            elif tag[1] == 'L': # led color
                id, type, heading = tag  
                fields.append(self.form_led_color_select(id, heading))
            elif tag[1] == 'D': # selection dropdown
                id, type, heading, options = tag # todo remove dst_mode from init ??
                fields.append(self.form_dropdown(id, heading, options, self.cfg[id]))
            elif tag[1] == '-': # empty row with line
                fields.append('<tr class="h-line"><td colspan="3">&zwnj;</td></tr><tr><td colspan="3">&zwnj;</td></tr>')
                #     '<tr><td>&zwnj;<label> </label></td></tr>'
        fields.append('<tr><td colspan="3">&zwnj;</td></tr>')        
        fields.append('</table>')        
        return '\n'.join(fields).encode('utf8')
    
"""   
if __name__ == "__main__":
    import time
    

    cfg = { # these are defaults, actual values are in config.json
        "alarm_on": "No",
        "alarm_hour": 6,
        "alarm_min": 30,
        "active_font": "nixie",
        "nixie": "#FFBF00",
        "dot": "#ff0000",
        "7seg": "#00ffff",
        "brightness" : 50,
        "rgb_mode": 1,
        "24_hour" : "24",
        "show_secs" : "No",
        "adjust_timing" : 128
    }


        
    cfg_tags = ( # tuple used to create html cfg tags
            ('alarm_on', 'R', 'Alarm Enabled', 'Yes', 'No'),  
            ('alarm_hour', 'T', 'Alarm hour', 1, 23),
            ('alarm_min', 'T', 'Alarm minute', 0, 59),
            ('', '-'),
            ('active_font', 'F','Font', 'nixie:Nixie', 'dot:Dot Matrix', '7seg:7 Segment'),
            ('', '-'),
            ('24_hour', 'R','Hours Format', '12', '24'),
            ('show_secs', 'R','Show Seconds', 'Yes', 'No'),
            ('', '-'),
            ('brightness', 'T','Brightness', 1, 100),
            ('rgb_mode', 'T','RGB Mode ?', 1, 59),
            ('adjust_timing', 'T', 'Trim timing', 0, 255)
       )
    
    def update_config(data):
        changed = 0
        for k,v in data.items():
            if v[:3] == '%23':
                v = '#' + v[3:]
            if cfg[k] != v:
                changed += 1
                print('cfg change for', k, 'old v = ', cfg[k], 'new v' ,v)
                cfg.update({k:v})
        if changed:
            # print("updated {} items".format(changed))
            pass
                  
    def post_callback(data):
        print("in post callback\n", data)
        update_config(data)
       
    webserver = my_HTTPserver(cfg, cfg_tags, post_callback)
    while(True):
        webserver.listen()
        # print(time.time())        
"""
