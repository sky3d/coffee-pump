import sys
import traceback
import threading
from time import sleep, time
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!  This is probably because you need superuser privileges.  You can achieve this by using 'sudo' to run your script")
import cloud4rpi

import rpi
from distance_sensor import wait_for_distance
from status import calc_status
from logger import log_debug, log_error, log_info
from notifications import notify_all

C4R_TOKEN = '__PUT_YOUR_DEVICE_TOKEN_HERE__'

ALERT_SENSOR_MSG = 'WARNING! dxPump is probably out of order...'

# Time intervals
DIAG_SENDING_INTERVAL = 60  # sec
DATA_SENDING_INTERVAL = 300  # sec
DEBUG_LOG_INTERVAL = 10 # sec

MIN_SEND_INTERVAL = 0.5  #
POLL_INTERVAL = 0.1  # 200 ms

# Pump 
PUMP_PIN = 4  # 7
START_PUMP = 1
STOP_PUMP = 0
PUMP_BOUNCE_TIME = 200 # milliseconds

# Distance from the sensor to the water level
MIN_DISTANCE = 3  # cm
MAX_DISTANCE = 8  # cm
DISTANCE_DELTA = 0.4 # cm

prev_distance = -999999
last_sending_time = -1
disableAlerts = False
pump_on = False

def pump_relay_handle(pin):
    global pump_on
    prev_pump_on = pump_on
    GPIO.setup(PUMP_PIN, GPIO.IN)
    pump_on = GPIO.input(PUMP_PIN)
    if prev_pump_on != pump_on:
        log_debug("[x] %s on distance  %.2f" % ('START' if pump_on else 'STOP', prev_distance))


log_info("Setup GPIO...")
GPIO.setmode(GPIO.BCM)

GPIO.setup(PUMP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(PUMP_PIN, GPIO.BOTH, callback=pump_relay_handle, bouncetime=PUMP_BOUNCE_TIME) 


def water_level_changed(current):
    global prev_distance
    return abs(prev_distance - current) > DISTANCE_DELTA


def calc_water_level_percent(distance):
    current = distance if distance else 0
    value = (MAX_DISTANCE - current) / (MAX_DISTANCE - MIN_DISTANCE) * 100
    return max(0, round(value))


def is_pump_on():
    global pump_on
    return pump_on
   

def toggle_pump(value):
    GPIO.setup(PUMP_PIN, GPIO.OUT)
    GPIO.output(PUMP_PIN, value)  # Start/Stop pouring    


def send(cloud, variables, dist, error=False):
    pump_on = is_pump_on()
    percent = calc_water_level_percent(dist)
    variables['Distance']['value'] = dist
    variables['WaterLevel']['value'] = percent
    variables['PumpRelay']['value'] = pump_on
    variables['Status']['value'] = calc_status(error, percent, pump_on)

    current = time()
    global last_sending_time
    if current - last_sending_time > MIN_SEND_INTERVAL:
        readings = cloud.read_data()
        cloud.publish_data(readings)
        last_sending_time = current


def main():
    variables = {
        'Distance': {
            'type': 'numeric',
        },
        'Status': {
            'type': 'string',
        },
        'PumpRelay': {
            'type': 'bool',
            'value': False
        },
        'WaterLevel': {
            'type': 'numeric',
        },
    }

    diagnostics = {
        'IP_Address': rpi.ip_address,
        'Host': rpi.host_name,
        'CPU_Temp': rpi.cpu_temp,
        'OS': rpi.os_name,
        'Uptime': rpi.uptime_human
    }

    cloud = cloud4rpi.connect(C4R_TOKEN, 'mq.stage.cloud4rpi.io')
    #cloud = cloud4rpi.connect(C4R_TOKEN, '10.10.110.2')
    cloud.declare(variables)
    cloud.declare_diag(diagnostics)
    cloud.publish_config()

    data_timer = 0
    diag_timer = 0
    log_timer = 0

    try:
        log_debug('Start...')
        while True:
            global disableAlerts
            global prev_distance

            distance = wait_for_distance()            
            if distance is None:
                log_error('Distance error!')
                if not disableAlerts:
                    notify_all(ALERT_SENSOR_MSG)
                    send(cloud, variables, distance, True)
                    disableAlerts = True

                if is_pump_on() and prev_distance < MIN_DISTANCE + DISTANCE_DELTA:
                    log_error('[!] Emergency stop of the pump. No signal from a distance sensor')
                    toggle_pump(STOP_PUMP)

                continue    # TODO hanle case when pump is ON

            now = time()
            should_log = now - log_timer > DEBUG_LOG_INTERVAL
            if should_log:
                #log_debug("Distance = %.2f (cm)" % (distance))
                #log_debug(readings.get_all())
                log_timer = now

            if distance < MIN_DISTANCE:  # Stop pouring
                toggle_pump(STOP_PUMP)

            if GPIO.event_detected(PUMP_PIN):
                edge = 'On' if is_pump_on() else 'Off'
                log_debug('[+] Event Detected:  %s' % edge)
                send(cloud, variables, distance)

            if distance > MAX_DISTANCE * 2:  # Distance is out of expected range: do not start pouring
                log_error('Distance is out of range:  %.2f' % distance)
                continue

            if distance > MAX_DISTANCE: # Start pouring
                toggle_pump(START_PUMP)
            
            if water_level_changed(distance):
                log_debug("Distance changed to %.2f (cm)" % (distance))
                send(cloud, variables, distance)
                prev_distance = distance

            if now - data_timer > DATA_SENDING_INTERVAL:
                send(cloud, variables, distance)
                data_timer = now

            if now - diag_timer > DIAG_SENDING_INTERVAL:
                cloud.publish_diag()
                diag_timer = now
            
            disableAlerts = False
            
            sleep(POLL_INTERVAL)

    except Exception as e:
        log_error('FAILED:', e)
        traceback.print_exc()

    finally:
        log_debug('Stopped!')
        GPIO.remove_event_detect(PUMP_PIN)
        GPIO.cleanup()
        sys.exit(0)


if __name__ == '__main__':
    main()
