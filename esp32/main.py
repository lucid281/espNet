import gc
import socket

import dht
import machine
import micropython
import ubinascii
import utime
from microWebSrv import MicroWebSrv

import esp32

ID = ubinascii.hexlify(machine.unique_id()).decode("utf-8")
ESPNET_HOST = ''
INTERRUPT = 0
CALLBACKS = {}


def pin_interrupt(pin):
    global INTERRUPT
    INTERRUPT += 1
    global CALLBACKS
    s = str(pin)
    if s not in CALLBACKS:
        CALLBACKS[s] = True


def get_gpio_status():
    gpio_status = {}
    for i in range(0, 40):
        try:
            v = machine.Pin(i).value()
            gpio_status[i] = v
        except:
            pass
    return gpio_status


@micropython.native
def read_ms(adc):
    d = []
    t = utime.ticks_us()
    while utime.ticks_diff(utime.ticks_us(), t) < 10000:
        d.append(adc.read())
    return int(sum(d) / len(d))


ui_page = '''\
    <!DOCTYPE html>
    <html>
        <head>
            <title>node: {id}</title>
        </head>
        <body>
            <h1>{id}</h1>
            
            <h2>board_temp</h2>
            {board_temp}f<br />
            
            <h2>espnet host</h2>
            {ESPNET_HOST}<br />
            
            <h2>/set_host - post</h2>
            set host for callbacks<br />
            <form action="/set_host" method="post">
                ip: <input type="text" name="ip"><br />
                <input type="submit" value="OK">
            </form>
            
            <h2>/gpio - post</h2>
            set pin high (1) or low(0).<br />
            <form action="/gpio" method="post">
                pin: <input type="text" name="pin"><br />
                <input type="radio" id="0" name="value" value="0">
                <label for="0">0</label><br>
                <input type="radio" id="1" name="value" value="1">
                <label for="1">1</label><br>
                <input type="submit" value="OK">
            </form>
                
            <h2>/adc - post</h2>
            sample adc using gpio as source voltage<br />
            <form action="/adc" method="post">
                read_pin: <input type="text" name="read_pin"><br />
                power_pin:  <input type="text" name="power_pin"><br />
                samples:  <input type="text" name="samples"> (1 == ~10ms)<br />
                <input type="submit" value="OK">
            </form>
        </body>
    </html>
    '''


@micropython.native
@MicroWebSrv.route('/ui')
def home(client, resp):
    resp.WriteResponseOk(contentType='text/html',
                         contentCharset='UTF-8',
                         content=ui_page.format(id=ID, board_temp=esp32.raw_temperature()))
    gc.collect()


@micropython.native
@MicroWebSrv.route('/', 'GET')
def board(client, resp):
    resp.WriteResponseJSONOk({
        'f': esp32.raw_temperature(),
        'id': ID,
        'gpio': get_gpio_status(),
        'espnet_host': ESPNET_HOST,
    })
    gc.collect()


@micropython.native
@MicroWebSrv.route('/gpio', 'POST')
def gpio(client, resp):
    m = machine
    d = client.ReadRequestPostedFormData()
    on_off = int(d['value'])
    if ',' in d['pin']:
        pins = [int(i) for i in d['pin'].split(',')]
        for pin_num in pins:
            pin = m.Pin(pin_num, m.Pin.OUT)
            if on_off == 2:
                v = pin.value()
                if v == 0:
                    pin.value(1)
                else:
                    pin.value(0)
            else:
                pin.value(on_off)
    else:
        p = int(d['pin'])
        pin = m.Pin(p, m.Pin.OUT)
        if on_off == 2:
            v = pin.value()
            if v == 0:
                pin.value(1)
            else:
                pin.value(0)
        else:
            pin.value(on_off)
    resp.WriteResponseJSONOk({
        'id': ID,
        'status': 'OK'
    })
    gc.collect()


@micropython.native
@MicroWebSrv.route('/adc', 'POST')
def adc(client, resp):
    m = machine
    d = client.ReadRequestPostedFormData()
    power_pin = int(d['power_pin'])
    power = m.Pin(power_pin, m.Pin.OUT, value=1)  # set pin high on creation
    read_pin = int(d['read_pin'])
    samples = 20
    if 'samples' in d:
        samples = int(d['samples'])
    adc = m.ADC(m.Pin(read_pin))  # create ADC object on ADC pin
    adc.atten(m.ADC.ATTN_11DB)  # set 11dB input attenuation (voltage range roughly 0.0v - 3.6v)
    adc.width(m.ADC.WIDTH_12BIT)  # set 9 bit return values (returned range 0-511)

    t = utime.ticks_us()
    resp.WriteResponseJSONOk({
        'id': ID,
        'data': [read_ms(adc) for i in range(samples)],
        'ticks': utime.ticks_diff(utime.ticks_us(), t)
    })
    power.value(0)  # kill power
    gc.collect()


@micropython.native
@MicroWebSrv.route('/dht22', 'POST')
def dht22(client, resp):
    m = machine
    d = client.ReadRequestPostedFormData()

    read_pin = int(d['read_pin'])
    d = dht.DHT22(m.Pin(read_pin))
    d.measure()
    resp.WriteResponseJSONOk({
        'id': ID,
        'temp': d.temperature(),
        'humidity': d.humidity()
    })
    gc.collect()


@micropython.native
@MicroWebSrv.route('/set_host', 'POST')
def set_host(client, resp):
    d = client.ReadRequestPostedFormData()
    global ESPNET_HOST
    ESPNET_HOST = d['ip']
    resp.WriteResponseJSONOk({
        'id': ID,
        'status': 'OK'
    })
    gc.collect()


mws = MicroWebSrv()
if not mws._started:
    mws._server = socket.socket()
    mws._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    mws._server.bind(mws._srvAddr)
    mws._server.listen(16)
    MicroWebSrv._startThread(mws._serverProcess)

