import threading
from hcsr04sensor import sensor
from logger import log_debug, log_error, log_info
from bounce_filter import BounceFilter
from config import GPIO_TRIGGER, GPIO_ECHO

MAX_READING_TIMEOUT = 0.7

log_info('Connecting HCSR04 sensor...')
hcsr04 = sensor.Measurement(trig_pin=GPIO_TRIGGER, echo_pin=GPIO_ECHO) 

# Keeps the last sensor measurements
readings = BounceFilter(size=6, discard_count=1)

reading_complete = threading.Event()

def wait_for_distance():
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
