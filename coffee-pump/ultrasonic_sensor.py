import threading
from hcsr04sensor import sensor
from logger import log_debug, log_error, log_info
from bounce_filter import BounceFilter

MAX_READING_TIMEOUT = 1

# GPIO Pins
TRIGGER_PIN = 17  #
ECHO_PIN = 27  # 13

log_info('Connecting HCSR04 sensor...')
hcsr04 = sensor.Measurement(trig_pin=TRIGGER_PIN, echo_pin=ECHO_PIN) 

# Keeps the last sensor measurements
readings = BounceFilter(size=6, discard_count=1)

reading_complete = threading.Event()

def read_sensor_in_background():
    reading_complete.clear()
    thread = threading.Thread(target=read_distance)
    thread.start()
  
    if not reading_complete.wait(MAX_READING_TIMEOUT):
        log_info('Reading sensor timeout')
        return None
    return readings.avg()


def read_distance():
    try:
        value = hcsr04.raw_distance(sample_size=5)
        rounded = value if value is None else round(value, 1)
        readings.add(rounded)        
    except Exception as err:
        log_error('Internal error: %s' % err)
    finally:
        reading_complete.set()        
