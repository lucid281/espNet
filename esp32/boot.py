# This file is executed on every boot (including wake-boot from deepsleep)import gcgc.enable()import machinemachine.freq(240000000)ssid = 'YOUR_WIFI'password = 'YOUR_PASSWORD'ip, subnet, gateway, dns = '192.168.1.200',\                           '255.255.255.0',\                           '192.168.1.1',\                           '192.168.1.1'import networksta_if = network.WLAN(network.STA_IF)sta_if.ifconfig((ip, subnet, gateway, dns))sta_if.active(True)if not sta_if.isconnected():    print('connecting to network...')    sta_if.connect(ssid, password)    while not sta_if.isconnected():        pass    print('connected!')gc.collect()