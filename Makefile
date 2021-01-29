.ONESHELL:
#SHELL := /bin/bash

device = '/dev/ttyUSB0'

pico:
	picocom $(device) -b115200

install:
	pipenv install --deploy --system --ignore-pipfile

setup:
	python3 -m pip install .

local-dev:
	python3 -m pip install --user pipenv
	python3 -m pipenv install


test:
	@echo -n '0 L:'; curl -s -X POST http://192.168.1.200/adc -d read_pin=36 -d power_pin=32 -d sample=200 | jq -j '.mean'
	@echo -n '  T:'; curl -s -X POST http://192.168.1.200/adc -d read_pin=39 -d power_pin=33 -d sample=200 | jq '.mean'
	@echo ''

test2:
	bash -c 'while true; do curl -X POST http://192.168.1.203/gpio -d pin=32 -d value=2; done'
