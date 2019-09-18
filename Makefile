.PHONY: install run start stop status log deploy

MAIN_FILE:= coffee-pump/main.py
SERVICE_INSTALL_SCRIPT:= service_install.sh
SERVICE_NAME:= coffee-pump.service

install:
	chmod +x $(SERVICE_INSTALL_SCRIPT)
	sudo ./$(SERVICE_INSTALL_SCRIPT) $(MAIN_FILE)

run:
	sudo python3 $(MAIN_FILE)

start:
	sudo systemctl start $(SERVICE_NAME)

status:
	sudo systemctl status $(SERVICE_NAME)

stop:
	sudo systemctl stop $(SERVICE_NAME)

log:
	sudo journalctl -u coffee-pump --since today

deploy:
	rsync -av coffee-pump sensor-setup Makefile *.sh pi@10.10.113.148:~/
