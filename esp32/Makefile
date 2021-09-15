.ONESHELL:

device = '/dev/ttyUSB0'
firmware = 'esp32-20210902-v1.17.bin'

pico:
	picocom $(device) -b115200

get-firmware:
	wget https://micropython.org/resources/firmware/$(firmware)

flash:
	esptool.py --chip esp32 --port $(device) erase_flash
	sleep 1
	esptool.py --chip esp32 --port $(device) --baud 460800 write_flash -z 0x1000 $(firmware)

ls:
	ampy -p $(device) ls /

put-app:
	ampy -p $(device) put main.py main.py
	ampy -p $(device) put microWebSrv.py microWebSrv.py

put-boot:
	ampy -p $(device) -d 1 put boot.py boot.py

pp: put pico

pr: put
	ampy -p $(device) reset

put-main:
	ampy -p $(device) put main.py main.py

reset:
	ampy -p $(device) reset