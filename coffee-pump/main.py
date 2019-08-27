import sys
import traceback
import threading
from time import sleep, time, monotonic
import RPi.GPIO as GPIO
import cloud4rpi

from logger import log_debug, log_error, log_info
from notifications import notify_all
from ultrasonic_sensor import read_sensor_in_background
from status import calc_status

C4R_TOKEN = '__PUT_YOUR_DEVICE_TOKEN_HERE__'

ALERT_SENSOR_MSG = 'WARNING! dxPump is probably out of order...'

# Time intervals
DIAG_SENDING_INTERVAL = 30  # sec
DATA_SENDING_INTERVAL = 300  # sec
MIN_SEND_INTERVAL = 0.5  #
DEBUG_LOG_INTERVAL = 1 # sec
POLL_INTERVAL = 0.2  # 200 ms

# Pump 
PUMP_PIN = 4  # 7
STOP_PUMP = 0
START_PUMP = 1

# Distance from crsr04 sensor to a water level
MIN_DISTANCE = 4  # cm
MAX_DISTANCE = 9  # cm
DISTANCE_DELTA = 0.5 # cm

log_info("Initialize GPIO mode")
GPIO.setmode(GPIO.BCM)

pump_on = False
prev_distance = -999999
last_sending_time = -1
disableAlerts = False


def get_uptime():
    return '%.2f' % monotonic()


def water_level_changed(current):
    global prev_distance
    return abs(prev_distance - current) > DISTANCE_DELTA


def calc_water_level_percent(dist):
    d = dist if dist else 0
    value = (MAX_DISTANCE - d) / (MAX_DISTANCE - MIN_DISTANCE) * 100
    return max(0, round(value))


def toggle_pump(value, log):
    if log:
        log_debug("[x] %s" % ('START' if value else 'STOP'))
    global pump_on
    pump_on = value
    GPIO.setup(PUMP_PIN, GPIO.OUT)
    GPIO.output(PUMP_PIN, pump_on)  # Start/Stop pouring


def send(cloud, variables, dist, error=False):
    global pump_on
    percent = calc_water_level_percent(dist)
    variables['Distance']['value'] = dist
    variables['WaterLevel']['value'] = percent
    variables['PumpRelay']['value'] = pump_on
    variables['Status']['value'] =  calc_status(error, percent, pump_on)

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
        'Uptime': get_uptime
    }

    cloud = cloud4rpi.connect(C4R_TOKEN, 'mq.stage.cloud4rpi.io')
    cloud.declare(variables)
    cloud.declare_diag(diagnostics)
    cloud.publish_config()

    data_timer = 0
    diag_timer = 0

    try:
        log_debug('Start reading distance...')
        next_log_time = 0

        while True:
            distance = read_sensor_in_background()

            if distance is None:
                log_error('Distance error!')
                global disableAlerts
                if not disableAlerts:
                    notify_all(ALERT_SENSOR_MSG)
                    send(cloud, variables, distance, True)
                    disableAlerts = True

                continue;    

            now = time()
            should_log = now - next_log_time > DEBUG_LOG_INTERVAL
            if should_log:
                log_debug("Distance = %.2f (cm)" % (distance))
                #log_debug(readings.get_all())
                next_log_time = now

            global pump_on
            if distance < MIN_DISTANCE:  # Stop pouring
                prev_pump_on = pump_on
                toggle_pump(STOP_PUMP, should_log)

                if (pump_on != prev_pump_on):
                    send(cloud, variables, distance)

            if distance > MAX_DISTANCE * 2:  # Distance is out of expected range: do not start pouring
                log_error('Distance is out of range:  %.2f' % distance)
                continue

            if distance > MAX_DISTANCE: # Start pouring
                prev_pump_on = pump_on
                toggle_pump(START_PUMP, should_log)

                if (pump_on != prev_pump_on):
                    send(cloud, variables, distance)

            global prev_distance
            if water_level_changed(distance):
                log_debug("Distance changed to %.2f (cm)" % (distance))
                send(cloud, variables, distance)
                prev_distance = distance

            if data_timer <= 0:  # Regular 
                send(cloud, variables, distance)
                data_timer = DATA_SENDING_INTERVAL


            if diag_timer <= 0:
                cloud.publish_diag()
                #send(cloud, variables, distance)
                diag_timer = DIAG_SENDING_INTERVAL

            sleep(POLL_INTERVAL)

            diag_timer -= POLL_INTERVAL
            data_timer -= POLL_INTERVAL

            disableAlerts = False

    except Exception as e:
        log_error('FAILED:', e)
        traceback.print_exc()

    finally:
        traceback.print_exc()
        GPIO.cleanup()
        sys.exit(0)


if __name__ == '__main__':
    main()
