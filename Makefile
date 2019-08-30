.PHONY: install run start stop status log deploy beta-deploy

SCRIPT_FILE:= coffee-pump/main.py
SERVICE_NAME:= coffee-pump.service

install:
	sudo service_install $(SCRIPT_FILE)

run:
	sudo python3 $(SCRIPT_FILE)

start:
	sudo systemctl start $(SERVICE_NAME)

status:
	sudo systemctl status $(SERVICE_NAME)

stop:
	sudo systemctl stop $(SERVICE_NAME)

log:
	sudo journalctl -u coffee-pump

deploy:
	rsync -av coffee-pump sensor-setup Makefile *.sh pi@10.10.113.148:~/

# beta-deploy:
# 	rsync -av coffee-pump sensor-setup Makefile *.sh pi@10.10.113.148:~/beta/
