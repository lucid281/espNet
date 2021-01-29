.ONESHELL:

device = '/dev/ttyUSB0'

pico:
	picocom $(device) -b115200

get-firmware:
	wget http://micropython.org/resources/firmware/esp32-idf3-20200902-v1.13.bin

flash:
	esptool.py --chip esp32 --port $(device) erase_flash
	sleep 1
	esptool.py --chip esp32 --port $(device) --baud 460800 write_flash -z 0x1000 esp32-idf3-20200902-v1.13.bin

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
