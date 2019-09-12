import sys
import traceback
import threading
from time import sleep, time
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!  Use 'sudo' to run your script")
import cloud4rpi

from config import C4R_TOKEN, C4R_HOST
from config import GPIO_PUMP
from config import MIN_DISTANCE, MAX_DISTANCE, STOP_PUMP_DISTANCE, DISTANCE_DELTA
from config import SENSOR_ERROR, NO_WATER_ERROR
import rpi
from distance_sensor import wait_for_distance
from messages import calc_status, calc_alert
from logger import log_debug, log_error, log_info
from notifications import notify_in_background

# Time intervals
DIAG_SENDING_INTERVAL = 60  # secs
DATA_SENDING_INTERVAL = 300  # secs
DEBUG_LOG_INTERVAL = 10 # secs

MIN_SEND_INTERVAL = 0.5  # secs
POLL_INTERVAL = 0.1  # ms

# Pump 
START_PUMP = 1
STOP_PUMP = 0
PUMP_BOUNCE_TIME = 50 # milliseconds

prev_distance = -9999
start_pouring_time = None
start_pouring_distance = -9999
last_sending_time = -1
disableAlerts = False
pump_on = False

def water_level_changed(current):
    global prev_distance
    return abs(prev_distance - current) > DISTANCE_DELTA


def water_source_empty(now, distance):
    global start_pouring_time, start_pouring_distance
    if start_pouring_time and now - start_pouring_time > 3:   # Waits 3 sec after pouring start 
        # Checks for water level changes since the start of pouring
        return abs(start_pouring_distance - distance) < DISTANCE_DELTA 
    return False        


def calc_water_level_percent(distance):
    d = distance if distance else 0
    value = (MAX_DISTANCE - d) / (MAX_DISTANCE - MIN_DISTANCE) * 100
    return max(0, round(value))


def is_pump_on():
    global pump_on
    return pump_on

def pump_relay_handle(pin):
    global pump_on, prev_distance, start_pouring_time, start_pouring_distance
    pump_on = GPIO.input(GPIO_PUMP)
    log_debug("Pump relay changed to %d" % pump_on)

    start_pouring_time = time() if pump_on else None
    start_pouring_distance = prev_distance if pump_on else -9999

def toggle_pump(value):
    if is_pump_on() != value:
        log_debug("[x] %s" % ('START' if value else 'STOP'))
    GPIO.setup(GPIO_PUMP, GPIO.OUT)
    GPIO.output(GPIO_PUMP, value)  # Start/Stop pouring    


def send(cloud, variables, dist, error_code=0, force=False):
    pump_on = is_pump_on()
    percent = calc_water_level_percent(dist)
    variables['Distance']['value'] = dist
    variables['WaterLevel']['value'] = percent
    variables['PumpRelay']['value'] = pump_on
    variables['Status']['value'] = calc_status(error_code, percent, pump_on)

    current = time()
    global last_sending_time
    if force or current - last_sending_time > MIN_SEND_INTERVAL:
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

    cloud = cloud4rpi.connect(C4R_TOKEN, C4R_HOST)
    cloud.declare(variables)
    cloud.declare_diag(diagnostics)
    cloud.publish_config()

    data_timer = 0
    diag_timer = 0
    log_timer = 0

    log_info("Setup GPIO...")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO_PUMP, GPIO.IN)
    GPIO.add_event_detect(GPIO_PUMP, GPIO.BOTH, callback=pump_relay_handle, bouncetime=PUMP_BOUNCE_TIME) 
    toggle_pump(STOP_PUMP)

    try:
        log_debug('Start...')
        while True:
            global disableAlerts, prev_distance

            distance = wait_for_distance() # Read the current water depth

            if distance is None:
                log_error('Distance error!')
                if not disableAlerts:
                    notify_in_background(calc_alert(SENSOR_ERROR))
                    send(cloud, variables, distance, error_code=SENSOR_ERROR, force=True)
                    disableAlerts = True

                if is_pump_on() and prev_distance < STOP_PUMP_DISTANCE + DISTANCE_DELTA:
                    log_error('[!] Emergency stop of the pump. No signal from a distance sensor')
                    toggle_pump(STOP_PUMP)

                continue

            now = time()
            should_log = now - log_timer > DEBUG_LOG_INTERVAL
            if should_log:
                #log_debug("Distance = %.2f (cm)" % (distance))
                log_timer = now

            if water_source_empty(now, distance):
                log_error('[!] Emergency stop of the pump. Water source is empty')
                toggle_pump(STOP_PUMP)
                notify_in_background(calc_alert(NO_WATER_ERROR))
                send(cloud, variables, distance, error_code=NO_WATER_ERROR, force=True)
                continue

            if distance <= STOP_PUMP_DISTANCE:  # Stop pouring
                toggle_pump(STOP_PUMP)

            if GPIO.event_detected(GPIO_PUMP):
                edge = 'On' if is_pump_on() else 'Off'
                log_debug('[!] Pump event detected:  %s' % edge)
                send(cloud, variables, distance, force=True)

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
        log_error('ERROR: %s' % e)
        traceback.print_exc()

    finally:
        log_debug('Stopped!')
        GPIO.remove_event_detect(GPIO_PUMP)
        GPIO.cleanup()
        sys.exit(0)


if __name__ == '__main__':
    main()
