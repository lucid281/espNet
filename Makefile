.ONESHELL:
#SHELL := /bin/bash

device = '/dev/ttyUSB0'

pico:
	picocom $(device) -b115200

install-pipenv-system:
	pipenv install --deploy --system --ignore-pipfile

install-host:
	sudo apt update
	sudo apt-get install apt-transport-https ca-certificates curl gnupg lsb-release python3-dev pipenv minicom

install-docker: install-host
	curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
	echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(shell lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
	sudo apt update
	sudo apt-get install docker-ce docker-ce-cli containerd.io

install-docker-user:
	echo "Run this: sudo usermod -aG docker $USER"

install-terraform:
	curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
	sudo apt-add-repository "deb [arch=$(shell dpkg --print-architecture)] https://apt.releases.hashicorp.com $(shell lsb_release -cs) main"
	sudo apt install terraform

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
	bash -c 'while true; do curl -X POST http://192.168.1.200/gpio -d pin=32 -d value=2; done'

